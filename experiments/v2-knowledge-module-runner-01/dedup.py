"""One duplicate test for digestion (schema-delta '중복 판정 함수 분리', 2026-09-29).
Compared against what digestion is about to make canonical in the same pass (not the ledger: pending entries may still
be rejected). Precision first: dropping a real fact is worse than a leftover duplicate (write-01 round_dedup), so only
the same sentence counts (whitespace, punctuation, filler '최대/모두/현재' and the sentence ending ignored).
Near matches were measured and rejected: '생성 때 … 자른다' vs '수정 때 … 자른다' and '자른다' vs '자르지 않는다' score
0.86-0.88 character ratio with the same numbers and e5-large cosine above 0.96, so cosine/ratio thresholds would drop
contradictory facts. Paraphrases stay for the later clean-up job."""
import re

_FILLER = re.compile(r"(최대|모두|현재)")
_ENDING = re.compile(r"(이다|입니다|한다|된다|다)$")


def normalize(text):
    t = re.sub(r"[\s`'\"·,.!?()\[\]]+", "", str(text or ""))
    t = _FILLER.sub("", t)
    return _ENDING.sub("", t)


def find_duplicate(text, candidates):
    """Index of the first candidate that is the same sentence after normalize(), else None."""
    n = normalize(text)
    if not n:
        return None
    for i, c in enumerate(candidates or []):
        if n == normalize(c):
            return i
    return None
