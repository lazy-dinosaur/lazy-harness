"""Local resident encoder contract and outage regression."""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

import embed
import embed_server
import store_pg as pg
from test_store_pg import fixture, host, judgement, process


def test_health_vectors_and_input_limits(embed_service):
    with urlopen(embed_service + "/health") as response:
        health = json.load(response)
    assert health["model_id"] == embed.MODEL_ID and health["dim"] == 384 and health["loaded_at"]
    # _infer is the original subprocess-era algorithm, retained solely as a parity oracle.
    python = embed._MODEL_DIR / "venv/bin/python"
    import subprocess
    reference = subprocess.run([str(python), "-c", "import embed,json; print(json.dumps(embed._infer(['테스트 문장'], 'passage')))"],
                               text=True, capture_output=True, check=True).stdout
    reference_vector = json.loads(reference)[0]
    vector = embed.encode_passages(["테스트 문장"])[0]
    cosine = sum(a * b for a, b in zip(reference_vector, vector)) / (
        sum(a*a for a in reference_vector)**.5 * sum(b*b for b in vector)**.5)
    assert cosine >= .9999
    print(f"parity cosine={cosine:.9f}")
    for payload in ({"texts": ["a" * 4097], "role": "passage"},
                    {"texts": ["a"] * 65, "role": "query"},
                    {"texts": ["a " * 600], "role": "query"}):
        request = Request(embed_service + "/embed", json.dumps(payload).encode(),
                          {"Content-Type": "application/json"}, method="POST")
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 400
    with pytest.raises(ValueError):
        embed_server.serve(0, "0.0.0.0")


def test_outage_fallback_digest_and_backfill(dsn, host, embed_service, monkeypatch):
    monkeypatch.setenv("LH_EMBED_URL", "http://127.0.0.1:1")
    embed.encode_query.cache_clear()
    add = judgement(host, text="오프라인 조각 검색")
    _, _, receipt = process(dsn, add, fixture(text="오프라인 조각 검색"))
    result = pg.digest(dsn, add["work_unit_id"], True, {receipt: fixture(text="오프라인 조각 검색")})
    assert result["status"] == "absorbed" and result["embedding_pending"]
    rows = pg.search(dsn, host, "오프라인 조각 검색", mode="hybrid")
    assert rows and rows[0]["mode_used"] == "text" and rows[0]["warning"]
    monkeypatch.setenv("LH_EMBED_URL", embed_service)
    embed.encode_query.cache_clear()
    assert pg.backfill_embeddings(dsn, host) == 1
    assert pg.search(dsn, host, "오프라인 조각 검색", mode="hybrid")[0]["mode_used"] == "hybrid"
