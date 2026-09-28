"""knowledge.json loader: env override, file, defaults, permission gate, missing-key message without values."""
import json
import os

import pytest

import config


@pytest.fixture
def cfgfile(tmp_path, monkeypatch):
    for env, _ in config.FIELDS.values():
        monkeypatch.delenv(env, raising=False)
    p = tmp_path / "knowledge.json"
    monkeypatch.setenv(config.PATH_ENV, str(p))
    def write(data, mode=0o600):
        p.write_text(json.dumps(data))
        os.chmod(p, mode)
    return write


def test_defaults_and_file(cfgfile):
    cfgfile({"db_url": "postgresql://x", "jev": {"api_key": "SECRET"}})
    c = config.load()
    assert c["db_url"] == "postgresql://x" and c["jev_api_key"] == "SECRET"
    assert c["jev_model"] == "~typesafe/jev-latest" and c["jev_base_url"] == "https://openrouter.ai/api"


def test_env_overrides_file(cfgfile, monkeypatch):
    cfgfile({"jev": {"model": "file-model"}})
    monkeypatch.setenv("LH_JEV_MODEL", "env-model")
    assert config.load()["jev_model"] == "env-model"


def test_permission_gate(cfgfile):
    cfgfile({"jev": {"api_key": "SECRET"}}, mode=0o644)
    with pytest.raises(config.ConfigError, match="chmod 600"):
        config.load()


def test_missing_names_not_values(cfgfile):
    cfgfile({"jev": {"api_key": "SECRET"}})
    with pytest.raises(config.ConfigError) as err:
        config.require("db_url", "jev_api_key")
    assert "db_url" in str(err.value) and "SECRET" not in str(err.value) and "jev_api_key" not in str(err.value)


def test_no_file_is_ok(cfgfile):
    assert config.load()["db_url"] is None
