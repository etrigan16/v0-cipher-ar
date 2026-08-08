"""Secret configuration unit tests.

Design D5: Settings must fail validation when SECRET_KEY is not provided.
The module-level ``settings`` object is already bound with the env set by
conftest, so these tests instantiate a fresh Settings with ``_env_file=None``
to ignore any .env file and exercise the environment only.
"""

import os

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_secret_key_required_when_unset():
    saved = os.environ.pop("SECRET_KEY", None)
    try:
        with pytest.raises(ValidationError) as excinfo:
            Settings(_env_file=None)
        assert "secret_key" in str(excinfo.value)
    finally:
        if saved is not None:
            os.environ["SECRET_KEY"] = saved


def test_secret_key_reads_from_environment():
    settings = Settings(_env_file=None)
    assert settings.secret_key == "test-secret"


# --- Phase 4: LLM enrichment settings (PR 3) --------------------------------


def test_llm_defaults_when_key_absent():
    """R1/KeyAbsent: defaults are Groq base URL + a Groq model; key empty -> disabled."""
    s = Settings(_env_file=None)
    assert s.llm_api_key == ""
    assert s.llm_base_url == "https://api.groq.com/openai/v1"
    assert s.llm_model == "llama-3.3-70b-versatile"
    assert s.llm_timeout == 30.0
    assert s.llm_enabled is False


def test_llm_enabled_derived_from_key_presence(monkeypatch):
    """LLM_ENABLED is derived: key set -> enabled, key removed -> disabled."""
    monkeypatch.setenv("LLM_API_KEY", "gsk_test_key")
    s = Settings(_env_file=None)
    assert s.llm_enabled is True
    assert s.llm_api_key == "gsk_test_key"

    monkeypatch.delenv("LLM_API_KEY")
    s2 = Settings(_env_file=None)
    assert s2.llm_enabled is False


def test_llm_overrides_read_from_environment(monkeypatch):
    """Base URL/model/timeout honor environment overrides."""
    monkeypatch.setenv("LLM_BASE_URL", "https://custom.example/v1")
    monkeypatch.setenv("LLM_MODEL", "llama-3.3-70b")
    monkeypatch.setenv("LLM_TIMEOUT", "15")
    s = Settings(_env_file=None)
    assert s.llm_base_url == "https://custom.example/v1"
    assert s.llm_model == "llama-3.3-70b"
    assert s.llm_timeout == 15.0
