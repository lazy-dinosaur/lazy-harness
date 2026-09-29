"""emb-01/dup: re-measure the capture_audit DUP_COSINE cut for e5-large.
Pairs mirror what dedupe sees: the same decision said as request / plan / report (same) vs neighbouring but different decisions (diff).
Hand-made from this session's real decisions (the 2026-09-28 G7 sample was not kept). Passage embeddings, like dedupe."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SAME = [
 ("e5-large 로 전체 옮기자", "임베딩 모델을 OpenRouter e5-large 로 전환한다"),
 ("하네스 규칙은 DB 가 아니라 코드에 박자", "하네스 규칙을 코드에 하드코딩하고 base_rules.json 을 삭제했다"),
 ("규칙은 시스템 안내에 넣고 지식은 턴 시작 메시지로 넣자", "규칙은 system prompt, 지식은 턴 시작 메시지로 주입하도록 바꿨다"),
 ("답변 끝에서 하네스 규칙과 프로젝트 규칙을 한 번에 판정하자", "답변 끝 판정을 하네스·프로젝트 규칙 통합 한 번으로 합친다"),
 ("메인 DB 에 적용하기 전에 백업부터 떠", "적용 전 backup.py 로 knowledge 스키마를 백업했다"),
 ("LFM 은 학습에 쓰일 수 있어서 빼자", "LFM2.5 무료 모델은 요청이 학습에 쓰일 수 있어 제외한다"),
 ("ref 항목은 매번 임베딩하지 말고 저장된 벡터를 쓰자", "ref_fetch 가 저장 벡터로 정렬하도록 고쳤다"),
 ("테스트는 항상 로컬 모델로 돌리자", "테스트는 설정과 상관없이 로컬 e5-small 로 고정했다"),
 ("로컬 임베딩 서비스는 꺼도 돼", "lhv2-embed 서비스를 종료한다"),
 ("품질 비교를 먼저 해보고 정하자", "전환 전에 scale 정답 세트로 검색 품질을 비교하기로 했다"),
]
DIFF = [
 ("e5-large 로 전체 옮기자", "LFM2.5 무료 모델은 요청이 학습에 쓰일 수 있어 제외한다"),
 ("하네스 규칙을 코드에 하드코딩했다", "프로젝트 규칙은 DB rules 테이블에 둔다"),
 ("규칙은 시스템 안내에 넣는다", "지식은 턴 시작 메시지로 넣는다"),
 ("메인 DB 에 0007 을 적용한다", "메인 DB 에 0008 을 적용한다"),
 ("백업은 하루 한 번 돌린다", "백업은 최신 14개만 보관한다"),
 ("ref_fetch 가 저장 벡터를 쓴다", "검색어는 묶어서 한 번에 임베딩한다"),
 ("테스트는 로컬 모델로 돈다", "실사용은 OpenRouter 모델로 돈다"),
 ("중복 묶기 기준을 다시 잰다", "규칙 선택 기준을 다시 잰다"),
 ("품질 비교를 먼저 한다", "비용은 한 달 1달러 미만이다"),
 ("로컬 임베딩 서비스를 끈다", "백업 서비스는 그대로 둔다"),
]


def cos(a, b):
    return sum(x * y for x, y in zip(a, b))


out = {}
for prov in ("local", "openrouter"):
    os.environ["LH_EMBED_PROVIDER"] = prov
    import importlib, embed
    importlib.reload(embed)
    texts = list(dict.fromkeys([t for p in SAME + DIFF for t in p]))
    vec = dict(zip(texts, embed.encode_passages(texts)))
    s = sorted(round(cos(vec[a], vec[b]), 3) for a, b in SAME)
    d = sorted(round(cos(vec[a], vec[b]), 3) for a, b in DIFF)
    out[prov] = {"same": s, "diff": d, "same_min": s[0], "diff_max": d[-1]}
    print(prov, json.dumps(out[prov]))
(Path(__file__).resolve().parent / "dup-result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
