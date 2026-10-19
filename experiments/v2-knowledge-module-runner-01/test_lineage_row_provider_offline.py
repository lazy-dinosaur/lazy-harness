"""Fake-DB integration tests: SQL row mapping -> provider -> existing materializer."""
import json
import socket
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

BLOCKED = {"socket": 0, "process": 0}
def deny(name):
    def call(*_a, **_k):
        BLOCKED[name] += 1
        raise AssertionError("external effect blocked in provider test")
    return call
socket.create_connection = deny("socket")
socket.getaddrinfo = deny("socket")
subprocess.Popen = deny("process")

from lineage_row_provider import PostgresLineageRowProvider, _refs_digest
from lineage_scope import LineageProofError, materialize_snapshot
from execution_scope import ExecutionScope

NAMESPACE = "fixture-lineage"

class FakeCursor:
    def __init__(self, mutation=None): self.result = []; self.description = None; self.readonly = False; self.mutation=mutation
    def execute(self, sql, params=None):
        if sql == "SET TRANSACTION READ ONLY": self.readonly = True; self.result=[]; return
        if "current_database(),current_user" in sql: self.result=[("postgres","supabase_admin")]; return
        if "from knowledge.host" in sql: self.result=[(NAMESPACE,)]; return
        if "from knowledge.confirmation_queue" in sql:
            qids=params[0]
            self.result=[(qid,NAMESPACE,"pending",{"id":f"L{qid}","text":f"left claim {qid}",
                "with_id":f"R{qid}","with_text":f"right claim {qid}"},f"E{qid}",f"W{qid}") for qid in qids]
            return
        if "from knowledge.subject_alias a join knowledge.fragment f" in sql:
            _host, alias, subject_id = params
            fid = "L1" if subject_id == "subject-L1" and alias == "declared-alias" else None
            self.result=[(fid,NAMESPACE,"stored-alias-left","left claim 1",1,True,
                {"evidence_refs":[{"type":"code_test","locator":"x","quote":"q"}]})] if fid else []
            return
        if "from knowledge.fragment where host_id=%s and subject_id=%s and active" in sql:
            _host, subject_id = params
            fid = "R1" if subject_id == "subject-R1" else None
            self.result=[(fid,NAMESPACE,"storage-right","right claim 1",1,True,
                {"evidence_refs":[{"type":"code_test","locator":"x","quote":"q"}]})] if fid else []
            return
        if "from knowledge.fragment_history" in sql:
            fid=params[0]
            self.result=[(fid,2,{"id":fid,"host_id":NAMESPACE,"subject_id":"subject-L1","alias":"alias-L1","text":"left claim 1","revision":2,
                "source":{"evidence_refs":[{"type":"code_test","locator":"x","quote":"q"}]}},22),
                (fid,3,{"id":fid,"host_id":NAMESPACE,"subject_id":"subject-L1","alias":"alias-L1","text":"left claim 1","revision":2,
                "source":{"evidence_refs":[{"type":"code_test","locator":"x","quote":"q"}]}},21)] if fid=="L1" else []
            if fid=="L1" and self.mutation=="duplicate_history": self.result.append(self.result[-1])
            if fid=="L1" and self.mutation=="ambiguous_history":
                duplicate=list(self.result[-1]); duplicate[3]=999; self.result.append(tuple(duplicate))
            return
        if "from knowledge.source_correction_receipt" in sql:
            _host,fid,oldrev,newrev,oldtext=params
            self.result=[]
            if (fid,oldrev,newrev,oldtext)==("L1",2,3,"left claim 1"):
                replacement_ref={"type":"code_test","locator":"x","quote":"q2"}
                evidence={"semantic_judgement":{"choice":"supported","probabilities":{"supported":0.96}},
                    "source_contexts":[{"origin":"frozen-import","manifest_sha256":"a"*64,
                        "type":"code_test","locator":"x","quote":"q"}]}
                refs_fp=_refs_digest({"evidence_refs":[{"type":"code_test","locator":"x","quote":"q"}]})
                origin="frozen-import"; receipt_oldrev=2; receipt_oldtext="left claim 1"; source_fp="b"*64
                if self.mutation=="legacy_pre_digest":
                    evidence["source_contexts"]=[{"origin":"frozen-import","manifest_sha256":"a"*64,**replacement_ref}]
                    evidence["source_recovery"]={"replacement_refs":[replacement_ref],"replacement_fingerprint":source_fp}
                if self.mutation=="legacy_missing_payload":
                    evidence["source_contexts"]=[{"origin":"frozen-import","manifest_sha256":"a"*64,**replacement_ref}]
                if self.mutation=="wrong_authority": origin="live-generated"
                if self.mutation=="wrong_refs": refs_fp="c"*64
                if self.mutation=="wrong_claim": receipt_oldtext="wrong claim"
                if self.mutation=="wrong_cas": receipt_oldrev=1
                if self.mutation=="unsupported_choice": evidence["semantic_judgement"]["choice"]="unsupported"
                if self.mutation=="malformed_manifest": evidence["source_contexts"][0]["manifest_sha256"]="bad"
                self.result=[("receipt-L1",receipt_oldrev,3,receipt_oldtext,"corrected claim 1",source_fp,refs_fp,origin,evidence)]
            return
        if "from knowledge.fragment where id=" in sql:
            fid=params[0]; qid=int(fid[1:]) if fid.startswith(("L","R")) else 1
            side="left claim" if fid.startswith("L") else "right claim"
            claim=f"corrected claim {qid}" if fid=="L1" else f"{side} {qid}"
            revision=3 if fid=="L1" else 1
            subject = "subject-L1" if fid == "L1" else "subject-R1" if fid == "R1" else None
            quote = "q2" if fid == "L1" and self.mutation in {"legacy_pre_digest","legacy_missing_payload"} else "q"
            self.result=[(fid,NAMESPACE,f"alias-{fid}",claim,revision,True,{"evidence_refs":[{"type":"code_test","locator":"x","quote":quote}]},subject)]
            return
        raise AssertionError(f"unexpected SQL in fake: {sql}")
    def fetchone(self): return self.result.pop(0) if self.result else None
    def fetchall(self): result,self.result=self.result,[]; return result
    def __enter__(self): return self
    def __exit__(self,*_): pass

class FakeConnection:
    def __init__(self, mutation=None): self.autocommit=True; self.cur=FakeCursor(mutation); self.rolled_back=False
    def cursor(self): return self.cur
    def rollback(self): self.rolled_back=True
    def __enter__(self): return self
    def __exit__(self,*_): pass

class FakeDBIntegration(TestCase):
    def test_changed_baseline_bytes_fail_before_opening_database(self):
        import hashlib
        cases=[{"question_id":i,"kind":"canon_contradiction"} for i in range(315)]
        ledger={"cases":cases}
        with TemporaryDirectory() as d:
            path=Path(d)/"ledger.json"; path.write_text(json.dumps(ledger))
            provider=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                connect=lambda _dsn: self.fail("DB must not open"),ledger_path=path,
                approved_ledger_sha256="0"*64)
            with self.assertRaisesRegex(ValueError,"baseline ledger fingerprint mismatch"):
                provider.load({"read_only":True,"database":{"original_baseline_roots":315}})

    def test_receipt_and_history_corruption_are_explicitly_blocked(self):
        cases=[{"question_id":i,"kind":"canon_contradiction"} for i in range(315)]
        ledger={"cases":cases}; proof={"read_only":True,"database":{"original_baseline_roots":315}}
        expectations={"wrong_authority":"missing_or_unauthorized_cas_edge",
            "wrong_claim":"missing_or_unauthorized_cas_edge","wrong_cas":"missing_or_unauthorized_cas_edge",
            "unsupported_choice":"missing_or_unauthorized_cas_edge","malformed_manifest":"missing_or_unauthorized_cas_edge",
            "wrong_refs":"cas_edge_before_refs_mismatch"}
        for mutation,expected in expectations.items():
            with self.subTest(mutation=mutation):
                provider=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                    connect=lambda _dsn,m=mutation:FakeConnection(m)).load(proof)
                root=provider.resolve_root(cases[1],proof)
                self.assertEqual(root["admission"],"blocked")
                self.assertTrue(any(expected in reason for reason in root["blocked_reasons"]))

    def test_complete_direct_root_coverage_is_not_dropped_and_is_blocked_by_existing_api(self):
        cases=[{"question_id":i,"kind":"canon_contradiction"} for i in range(315)]
        cases[0]["kind"]="unknown-baseline-kind"
        ledger={"cases":cases}; proof={"read_only":True,"database":{"original_baseline_roots":315}}
        connection=FakeConnection(); opened=[]
        def connect(_dsn): opened.append(connection); return connection
        provider=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,connect=connect).load(proof)
        rows=[provider.resolve_root(case,proof) for case in cases]
        self.assertEqual(len(rows),315)
        self.assertEqual(provider.metrics["direct_dependencies"],627)
        self.assertEqual(provider.metrics["cas_descendants"],1)
        self.assertTrue(connection.cur.readonly and connection.rolled_back)
        self.assertEqual(len(opened),1)
        self.assertTrue(all(len(root["sides"])==2 for root in rows))
        self.assertEqual(rows[0]["admission"],"blocked")
        self.assertEqual(len(rows[0]["blocked_reasons"]),2)
        self.assertEqual(rows[0]["blocked_reasons"][0],"selector_mapping:baseline case kind is unsupported")
        self.assertEqual(rows[0]["current_question"]["question_id"],"0")
        self.assertEqual(rows[0]["current_question"]["root_fingerprint"],rows[0]["root_fingerprint"])
        self.assertEqual(rows[1]["admission"],"lineage_projected")
        self.assertEqual(rows[1]["sides"][0]["classification"],"cas_descendant")
        self.assertEqual(rows[1]["sides"][0]["history_match_count"],1)
        self.assertEqual(rows[1]["sides"][0]["receipt_id"],"receipt-L1")
        self.assertEqual(rows[1]["sides"][1]["classification"],"direct_unchanged")
        self.assertNotIn("blocked_reason",rows[1]["sides"][1])
        with TemporaryDirectory() as d:
            lp=Path(d)/"ledger.json"; pp=Path(d)/"proof.json"
            lp.write_text(json.dumps(ledger)); pp.write_text(json.dumps(proof))
            with self.assertRaisesRegex(LineageProofError,r"root 0 is explicitly blocked: \['selector_mapping:baseline case kind is unsupported'"):
                provider.materialize(lp,pp,Path(d)/"snapshot.json")
        exact_duplicate=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
            connect=lambda _dsn:FakeConnection("duplicate_history")).load(proof)
        self.assertEqual(exact_duplicate.resolve_root(cases[1],proof)["admission"],"lineage_projected")
        same_before_state=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
            connect=lambda _dsn:FakeConnection("ambiguous_history")).load(proof)
        projected=same_before_state.resolve_root(cases[1],proof)
        self.assertEqual(projected["admission"],"lineage_projected")
        history=projected["sides"][0]["history"]
        self.assertEqual(history["match_count"],1)
        self.assertEqual(len(history["provenance"]),3)
        self.assertEqual(BLOCKED,{"socket":0,"process":0})

    def test_alias_conflict_uses_authoritative_subject_alias_root_candidates(self):
        cases=[{"question_id":i,"kind":"canon_contradiction"} for i in range(315)]
        cases[0]={"question_id":0,"kind":"alias_conflict"}
        ledger={"cases":cases}; proof={"read_only":True,"database":{"original_baseline_roots":315}}
        # Exact subject IDs and alias spelling are read from the current root reason.
        class AliasCursor(FakeCursor):
            def execute(self, sql, params=None):
                if "from knowledge.confirmation_queue" in sql:
                    qids=params[0]
                    self.result=[(qid,NAMESPACE,"pending",({"alias":"declared-alias",
                        "subject_id":"subject-L1","other_id":"subject-R1"} if qid == 0 else
                        {"id":f"L{qid}","text":f"left claim {qid}","with_id":f"R{qid}","with_text":f"right claim {qid}"}),
                        f"E{qid}",f"W{qid}") for qid in qids]
                    return
                return super().execute(sql,params)
        class AliasConnection(FakeConnection):
            def __init__(self):
                self.autocommit=True; self.cur=AliasCursor(); self.rolled_back=False
        provider=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
            connect=lambda _dsn:AliasConnection()).load(proof)
        root=provider.resolve_root(cases[0],proof)
        self.assertEqual(root["admission"],"lineage_projected")
        self.assertEqual({side["fragment_id"] for side in root["sides"]},{"L1","R1"})
        self.assertEqual(root["sides"][0]["classification"],"cas_descendant")
        self.assertEqual(root["sides"][0]["receipt_id"],"receipt-L1")

    def test_synthetic_alias_alias_root_shapes_allow_storage_alias_mismatch_and_pair_hint(self):
        q95_left="11111111-1111-4111-8111-111111111111"
        q95_right="22222222-2222-4222-8222-222222222222"
        q316_left="33333333-3333-4333-8333-333333333333"
        q316_right="44444444-4444-4444-8444-444444444444"
        roots={95:("subject-left-95","subject-right-95",
                   "synthetic-declared-left","synthetic-declared-right",q95_left,q95_right),
               316:("subject-left-316","subject-right-316",
                    "synthetic-same-alias","synthetic-same-alias",
                    q316_left,q316_right)}
        cases=[{"question_id":10000+i,"kind":"canon_contradiction"} for i in range(315)]
        cases[0]={"question_id":95,"kind":"alias_conflict"}; cases[1]={"question_id":316,"kind":"alias_conflict"}
        ledger={"cases":cases}; proof={"read_only":True,"namespace":NAMESPACE,"database":{"original_baseline_roots":315}}
        class RealShapeCursor(FakeCursor):
            def execute(self,sql,params=None):
                if "from knowledge.confirmation_queue" in sql:
                    self.result=[]
                    for qid in params[0]:
                        if qid in roots:
                            ls,rs,la,ra,lf,rf=roots[qid]
                            reason=({"alias":la,"subject_id":ls,"other_id":rs} if qid==95 else
                                    {"alias":la,"text":"root text is deliberately unrelated to storage alias",
                                     "subject_id":ls,"other_id":rs})
                            self.result.append((qid,NAMESPACE,"pending",reason,f"E{qid}",f"W{qid}"))
                        else:
                            self.result.append((qid,NAMESPACE,"pending",{"id":f"L{qid}","text":f"left claim {qid}",
                                "with_id":f"R{qid}","with_text":f"right claim {qid}"},f"E{qid}",f"W{qid}"))
                    return
                if "from knowledge.subject_alias a join knowledge.fragment f" in sql:
                    _host,alias,subject=params
                    qid=95 if subject==roots[95][0] else 316
                    ls,rs,la,ra,lf,rf=roots[qid]
                    # Both synthetic declared-alias joins return zero rows.
                    self.result=[]
                    return
                if "from knowledge.fragment where host_id=%s and subject_id=%s and active" in sql:
                    _host,subject=params
                    qid=next(q for q,root in roots.items() if subject in root[:2])
                    ls,rs,la,ra,lf,rf=roots[qid]; fid=lf if subject==ls else rf
                    self.result=[(fid,NAMESPACE,"independent-storage-alias",f"claim-{fid}",1,True,{"evidence_refs":[]})]
                    return
                if "id=any(%s::uuid[])" in sql:
                    self.result=[]
                    for fid in params[1]:
                        if fid in roots[316][4:]:
                            root=roots[316]; subject=root[0] if fid==root[4] else root[1]
                            self.result.append((fid,NAMESPACE,"fragment-storage-alias",f"claim-{fid}",1,True,{"evidence_refs":[]},subject))
                    return
                if "from knowledge.fragment where id=%s::uuid" in sql:
                    fid=params[0]
                    found=next(((qid,root) for qid,root in roots.items() if fid in root[4:]),None)
                    if found:
                        qid,root=found; _,_,_,_,lf,rf=root; subject=root[0] if fid==lf else root[1]
                        self.result=[(fid,NAMESPACE,"fragment-storage-alias",f"claim-{fid}",1,True,{"evidence_refs":[]},subject)]
                        return
                return super().execute(sql,params)
        class RealShapeConnection(FakeConnection):
            def __init__(self): self.autocommit=True; self.cur=RealShapeCursor(); self.rolled_back=False
        provider=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
            connect=lambda _dsn:RealShapeConnection()).load(proof)
        for qid in (95,316):
            row=provider.resolve_root({"question_id":qid},proof)
            self.assertEqual(row["admission"],"lineage_projected",row["blocked_reasons"])
            alias_side=next(side for side in row["sides"] if side["original_root_selector"])
            self.assertEqual(alias_side["classification"],"direct_unchanged")
            self.assertEqual(alias_side["history"]["match_count"],0)
            self.assertIsNone(alias_side["cas_receipt"]["receipt_id"])
            self.assertNotEqual(alias_side["original_root_selector"]["declared_alias"],
                                alias_side["resolved_selector"]["alias"])
            self.assertEqual(alias_side["resolved_selector"]["subject_id"],roots[qid][0])
        with TemporaryDirectory() as d:
            lp=Path(d)/"ledger.json"; pp=Path(d)/"proof.json"; out=Path(d)/"scope.json"
            lp.write_text(json.dumps(ledger)); pp.write_text(json.dumps(proof))
            snapshot=provider.materialize(lp,pp,out)
            scope=ExecutionScope.from_materialized_snapshot(out,lp,namespace=NAMESPACE,
                dataset_fingerprint="a"*64,source_manifest_fingerprint="b"*64)
            self.assertEqual(scope.pair_for_question("316"),tuple(snapshot["question_fragment_pairs"]["316"]))
            resolved=provider._rows["95"]["sides"][0]["resolved_selector"]
            original_subject=resolved["subject_id"]
            resolved["subject_id"]="wrong-subject"
            with self.assertRaisesRegex(LineageProofError,"resolved_selector_namespace_subject_or_current_identity_mismatch"):
                provider.materialize(lp,pp,Path(d)/"wrong-subject.json")
            resolved["subject_id"]=original_subject
        self.assertEqual(BLOCKED,{"socket":0,"process":0})

    def test_original_public_provider_to_adapter_to_materializer_accepts_direct_and_cas(self):
        cases=[{"question_id":i,"kind":"canon_contradiction"} for i in range(315)]
        ledger={"cases":cases}; proof={"read_only":True,"database":{"original_baseline_roots":315}}
        with TemporaryDirectory() as d:
            lp=Path(d)/"ledger.json"; pp=Path(d)/"proof.json"; out=Path(d)/"snapshot.json"
            lp.write_text(json.dumps(ledger)); pp.write_text(json.dumps(proof))
            provider=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                connect=lambda _dsn:FakeConnection()).load(proof)
            snapshot=provider.materialize(lp,pp,out)
            self.assertEqual(len(snapshot["root_question_ids"]),315)
            self.assertEqual(len(snapshot["question_fragment_pairs"]),315)
            sides=snapshot["bindings"]["1"]["sides"]
            self.assertEqual({side["classification"] for side in sides},{"cas_descendant","direct_unchanged"})
            direct=next(side for side in sides if side["classification"]=="direct_unchanged")
            self.assertIsNone(direct["cas_receipt"]["receipt_id"])
            self.assertEqual(direct["history"]["match_count"],0)
            self.assertIsNotNone(next(side for side in sides if side["classification"]=="cas_descendant")["cas_receipt"]["receipt_id"])
            self.assertTrue(out.exists())
            scope=ExecutionScope.from_materialized_snapshot(out,lp,namespace=NAMESPACE,
                dataset_fingerprint="a"*64,source_manifest_fingerprint="b"*64)
            self.assertEqual(len(scope.question_fragment_pairs),315)
            self.assertEqual(len(scope.blocked_root_question_ids),0)

            legacy=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                connect=lambda _dsn:FakeConnection("legacy_pre_digest")).load(proof)
            legacy_snapshot=legacy.materialize(lp,pp,Path(d)/"legacy.json")
            legacy_side=next(side for side in legacy_snapshot["bindings"]["1"]["sides"] if side["classification"]=="cas_descendant")
            legacy_edge=legacy_side["cas_receipt"]["chain"][0]
            self.assertEqual(legacy_edge["receipt_source_refs_digest"], _refs_digest({"evidence_refs":[{"type":"code_test","locator":"x","quote":"q"}]}))
            self.assertEqual(legacy_edge["source_refs_fingerprint"], _refs_digest({"evidence_refs":[{"type":"code_test","locator":"x","quote":"q2"}]}))
            self.assertEqual(legacy_edge["reference_proof"]["version"], "legacy-source-correction-post-refs-v1")

            failures={"wrong_refs": "cas_edge_before_refs_mismatch",
                      "legacy_missing_payload": "current_refs_do_not_match_receipt_proof"}
            for mutation, reason in failures.items():
                bad=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                    connect=lambda _dsn,m=mutation:FakeConnection(m)).load(proof)
                with self.subTest(mutation=mutation), self.assertRaisesRegex(LineageProofError,reason):
                    bad.materialize(lp,pp,Path(d)/f"{mutation}.json")
            wrong_root=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                connect=lambda _dsn:FakeConnection()).load(proof)
            wrong_root._rows["1"]["current_question"]["question_id"]="2"
            with self.assertRaisesRegex(LineageProofError,"exact current-question"):
                wrong_root.materialize(lp,pp,Path(d)/"wrong-root.json")
            missing=PostgresLineageRowProvider("fake",ledger,namespace=NAMESPACE,
                connect=lambda _dsn:FakeConnection()).load(proof)
            del missing._rows["1"]["sides"][1]["current_refs"]
            with self.assertRaisesRegex(LineageProofError,"sides\\[\\]\\.current_refs"):
                missing.materialize(lp,pp,Path(d)/"missing.json")
        self.assertEqual(BLOCKED,{"socket":0,"process":0})

if __name__ == "__main__": main()
