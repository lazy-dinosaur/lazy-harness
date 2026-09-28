from check_fragments import check
SRC = "\n".join(f"규칙 줄 {i}" for i in range(1, 41))  # 40 내용 줄 -> 범위 [1, 19]
def mk(n, text="Persistence registry 는 값을 고정한다.", group=None, lines=(1, 2)):
    fr = [{"text": text, "kind": "fact", "source_lines": list(lines), "group": group or f"g{i}"} for i in range(n)]
    return '{"records":[{"record_id":"R1","fragments":%s}]}' % __import__("json").dumps(fr, ensure_ascii=False)
def test_ok(): assert check("R1", SRC, mk(6))["ok"]
def test_parse(): assert check("R1", SRC, "거부합니다")["reasons"] == ["parse"]
def test_count_high(): assert "count" in check("R1", SRC, mk(40))["reasons"][0]
def test_kana(): assert "kana" in check("R1", SRC, mk(5, text="Persistence registry は固定する"))["reasons"]
def test_no_hangul(): assert "no_hangul" in check("R1", SRC, mk(5, text="registry fixed"))["reasons"]
def test_lines(): assert any(r.startswith("source_lines") for r in check("R1", SRC, mk(5, lines=(30, 99)))["reasons"])

def mixed(good, bad):
    import json
    fr = [{"text": "Persistence registry 는 값을 고정한다.", "kind": "fact", "source_lines": [1, 2], "group": f"g{i}"} for i in range(good)]
    fr += [{"text": "Persistence registry 는 값을 고정한다.", "kind": "fact", "source_lines": [41, 45], "group": f"b{i}"} for i in range(bad)]
    return json.dumps({"records": [{"record_id": "R1", "fragments": fr}]}, ensure_ascii=False)

def test_one_bad_line_dropped_not_failed():
    c = check("R1", SRC, mixed(10, 1))
    assert c["ok"] and c["n"] == 10 and c["raw_n"] == 11 and c["warnings"] == ["dropped_source_lines 1"]
    assert all(f["source_lines"] == [1, 2] for f in c["fragments"])

def test_many_bad_lines_fail():
    c = check("R1", SRC, mixed(8, 4))
    assert not c["ok"] and "source_lines 4" in c["reasons"]

def test_small_record_floor():
    small = "\n".join(f"규칙 {i}" for i in range(1, 11))  # 10 줄 -> 상한 최소 12
    assert check("R1", small, mk(11))["ok"]
    assert not check("R1", small, mk(13))["ok"]

def test_density_upper_bound():
    big = "\n".join(f"규칙 {i}" for i in range(1, 101))  # 100 줄 -> 상한 46
    assert check("R1", big, mk(44))["ok"]
    assert "count" in check("R1", big, mk(50))["reasons"][0]
def test_single_group(): assert "single_group" in check("R1", SRC, mk(6, group="g1"))["reasons"]
def test_prefix_text(): assert check("R1", SRC, "앞말 " + mk(6))["ok"]

def test_repair_missing_brace():
    from check_fragments import repair_json
    raw = mk(6)[:-1]
    fixed, did = repair_json(raw)
    assert did and check("R1", SRC, raw)["ok"]
