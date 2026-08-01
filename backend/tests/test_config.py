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
