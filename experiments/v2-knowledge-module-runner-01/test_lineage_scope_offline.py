"""Guard-first proof validation for history/CAS lineage materialization."""
import socket, subprocess
from unittest.mock import patch
BLOCKED = {"network": 0, "process": 0}
def deny(key):
    def call(*_a, **_k):
        BLOCKED[key] += 1
        raise AssertionError("unexpected external effect")
    return call
socket.create_connection = deny("network")
socket.getaddrinfo = deny("network")
subprocess.Popen = deny("process")

import json
import tempfile
import unittest
from pathlib import Path
from lineage_scope import LineageProofError, materialize_snapshot

class Provider:
    def __init__(self, mutate=None): self.mutate = mutate
    def resolve_root(self, case, _proof):
        sides=[]
        for fid in ("fid-left", "fid-right"):
            row={"classification":"cas_descendant","fragment_id":fid,"selector_fingerprint":"a"*64,
                 "history":{"match_count":1,"fragment_id":fid,"before_revision":1,"before_claim_fingerprint":"a"*64},
                 "current_claim":{"fragment_id":fid,"alias":"alias","text":"claim after","revision":2,"active":True,"fingerprint":"b"*64},
                 "current_refs":{"fragment_id":fid,"evidence_refs":[],"fingerprint":"d"*64},
                 "before_revision":1,"after_revision":2,"before_claim_fingerprint":"a"*64,
                 "after_claim_fingerprint":"b"*64,"before_refs_fingerprint":"d"*64,"after_refs_fingerprint":"d"*64,
                 "receipt_id":"receipt-"+fid,"receipt_old_claim_fingerprint":"a"*64,
                 "receipt_fragment_id":fid,"receipt_before_revision":1,"receipt_after_revision":2,
                 "source_fingerprint":"e"*64,"source_refs_fingerprint":"d"*64,
                 "typed_verification":{"choice":"supported","probability":0.99},
                 "source_authority":{"origin":"frozen-import","manifest_sha256":"1"*64,
                                     "source_fingerprint":"e"*64},
                 "cas_receipt":{"receipt_id":"receipt-"+fid,"fragment_id":fid,"before_revision":1,
                     "after_revision":2,"old_claim_fingerprint":"a"*64,"source_fingerprint":"e"*64,
                     "source_refs_fingerprint":"d"*64}}
            if self.mutate: self.mutate(row)
            sides.append(row)
        qid=str(case["question_id"]); fingerprint="f"*64
        return {"question_id":qid,"root_fingerprint":fingerprint,
                "current_question":{"question_id":qid,"host_id":"pilot","root_fingerprint":fingerprint},"sides":sides}

class LineageScopeOffline(unittest.TestCase):
    def test_materializes_immutable_snapshot_from_valid_same_fid_cas(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Path(d)/"roots.json"; proof=Path(d)/"trace.json"; output=Path(d)/"scope.json"
            ledger.write_text(json.dumps({"cases":[{"question_id":i} for i in range(315)]}))
            proof.write_text(json.dumps({"read_only":True,"database":{"original_baseline_roots":315}}))
            snapshot=materialize_snapshot(ledger,proof,output,Provider())
            self.assertTrue(snapshot["immutable"])
            self.assertEqual(len(snapshot["bindings"]),315)
            from execution_scope import ExecutionScope
            scope=ExecutionScope.from_materialized_snapshot(output,ledger,namespace="pilot",
                dataset_fingerprint="1"*64,source_manifest_fingerprint="2"*64)
            self.assertEqual(scope.pair_for_question("17"),("fid-left","fid-right"))
            self.assertTrue(scope.admits_question_fragments("17",["fid-left","fid-right"]))
            with self.assertRaisesRegex(LineageProofError,"immutable lineage snapshot"):
                materialize_snapshot(ledger,proof,output,Provider(lambda r:r["history"].update(provenance=[{"history_id":91}])))

    def test_exact_contiguous_multihop_cas_chain_passes_and_fork_skip_missing_edge_fail(self):
        def chain_provider(mutation=None):
            class Chained(Provider):
                def resolve_root(self, case, _proof):
                    root=super().resolve_root(case,_proof)
                    for side in root["sides"]:
                        side.update(classification="cas_descendant",before_revision=1,after_revision=3,
                            history={"match_count":1,"fragment_id":side["fragment_id"],
                                "before_revision":1,"before_claim_fingerprint":"a"*64},
                            current_refs={"fragment_id":side["fragment_id"],"fingerprint":"d"*64},
                            cas_receipt={"receipt_id":"r2","fragment_id":side["fragment_id"],
                                "before_revision":1,"after_revision":3,"old_claim_fingerprint":"a"*64,
                                "chain":[
                                  {"receipt_id":"r1","fragment_id":side["fragment_id"],"before_revision":1,
                                   "after_revision":2,"old_claim_fingerprint":"a"*64,"new_claim_fingerprint":"c"*64,
                                   "source_fingerprint":"e"*64,"source_refs_fingerprint":"d"*64,"after_refs_fingerprint":"d"*64,
                                   "typed_verification":{"choice":"supported","probability":.96},
                                   "source_authority":{"origin":"frozen-import","manifest_sha256":"1"*64,"source_fingerprint":"e"*64}},
                                  {"receipt_id":"r2","fragment_id":side["fragment_id"],"before_revision":2,
                                   "after_revision":3,"old_claim_fingerprint":"c"*64,"new_claim_fingerprint":"b"*64,
                                   "source_fingerprint":"e"*64,"source_refs_fingerprint":"d"*64,"after_refs_fingerprint":"d"*64,
                                   "typed_verification":{"choice":"supported","probability":.97},
                                   "source_authority":{"origin":"frozen-import","manifest_sha256":"1"*64,"source_fingerprint":"e"*64}}]},
                            current_claim={"fragment_id":side["fragment_id"],"fingerprint":"b"*64,"revision":3,"active":True},
                            after_claim_fingerprint="b"*64,selector_fingerprint="a"*64,
                            before_claim_fingerprint="a"*64,before_refs_fingerprint="d"*64)
                        side["receipt_id"]="r2"; side["receipt_fragment_id"]=side["fragment_id"]
                        side["receipt_before_revision"]=1; side["receipt_after_revision"]=3
                        side["receipt_old_claim_fingerprint"]="a"*64
                    if mutation:
                        mutation(root["sides"][0]["cas_receipt"]["chain"])
                    return root
            return Chained()
        with tempfile.TemporaryDirectory() as d:
            ledger=Path(d)/"roots.json"; proof=Path(d)/"trace.json"
            ledger.write_text(json.dumps({"cases":[{"question_id":i} for i in range(315)]}))
            proof.write_text(json.dumps({"read_only":True,"database":{"original_baseline_roots":315}}))
            made=materialize_snapshot(ledger,proof,Path(d)/"valid.json",chain_provider())
            self.assertEqual(made["bindings"]["0"]["sides"][0]["cas_receipt"]["chain"][1]["before_revision"],2)
            mutations=[lambda c:c[1].update(before_revision=3),
                       lambda c:c.pop(),
                       lambda c:c[0].update(fragment_id="other"),
                       lambda c:c[1].update(typed_verification={"choice":"unknown","probability":.99})]
            for i,mutate in enumerate(mutations):
                with self.subTest(i=i), self.assertRaises(LineageProofError):
                    materialize_snapshot(ledger,proof,Path(d)/f"bad-{i}.json",chain_provider(mutate))

    def test_forged_or_ambiguous_history_wrong_chain_and_missing_source_rejected(self):
        mutations=[lambda r:r["history"].update(match_count=2),lambda r:r["cas_receipt"].update(fragment_id="other"),
                   lambda r:r["cas_receipt"].update(before_revision=0),lambda r:r["cas_receipt"].update(old_claim_fingerprint="f"*64),
                   lambda r:r.update(typed_verification={"choice":"uncertain","probability":0.99}),
                   lambda r:r.update(source_authority={"origin":"live-root","manifest_sha256":"1"*64,
                                                     "source_fingerprint":"e"*64}),
                   lambda r:r.update(source_authority={"origin":"frozen-import","manifest_sha256":"bad",
                                                     "source_fingerprint":"e"*64}),
                   lambda r:r.update(after_refs_fingerprint="f"*64),
                   lambda r:r["cas_receipt"].pop("source_refs_fingerprint")]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as d:
                ledger=Path(d)/"roots.json"; proof=Path(d)/"trace.json"
                ledger.write_text(json.dumps({"cases":[{"question_id":i} for i in range(315)]}))
                proof.write_text(json.dumps({"read_only":True,"database":{"original_baseline_roots":315}}))
                with self.assertRaises(LineageProofError):
                    materialize_snapshot(ledger,proof,Path(d)/"scope.json",Provider(mutate))
        self.assertEqual(BLOCKED,{"network":0,"process":0})

if __name__ == "__main__": unittest.main()
