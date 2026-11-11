import pytest
from pydantic import ValidationError

from src.config import Settings


def test_a_legacy_pipeline_name_is_mapped_not_silently_ignored():
    with pytest.warns(UserWarning, match="legacy"):
        settings = Settings(_env_file=None, pipeline="ca")
    assert settings.pipeline == "malt"


def test_an_unknown_pipeline_fails_loudly():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, pipeline="nope")


def test_the_vote_pipeline_keeps_its_name():
    assert Settings(_env_file=None, pipeline="vote").pipeline == "vote"


def test_retired_env_names_are_reported(monkeypatch):
    monkeypatch.setenv("CA_SAMPLES", "3")
    with pytest.warns(UserWarning, match="retired"):
        Settings(_env_file=None)
