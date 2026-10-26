import json

import pytest
from fastapi.testclient import TestClient

import src
from scripts.devfree.toy import write_toy_split


class FakeLLM:
    """Replies from a script: a list (one reply per call) or a function of the user prompt."""

    def __init__(self, replies=None, error=None):
        self.replies = replies
        self.error = error
        self.messages = None
        self.calls = []

    def complete(self, messages, seed=None):
        if self.error:
            raise self.error
        self.messages = messages
        self.calls.append((messages[-1]["content"], seed))
        if callable(self.replies):
            return self.replies(messages[-1]["content"])
        if isinstance(self.replies, list):
            return self.replies.pop(0)
        return '{"answer_type": "number", "sql": "SELECT 1"}'


def plan(answer_type, sql):
    return json.dumps({"answer_type": answer_type, "sql": sql, "reason": "test"})


@pytest.fixture
def toy_split(tmp_path):
    """A split with one messy business package: CSV with title rows, XLSX with merged cells, SQLite."""
    return write_toy_split(tmp_path / "train")


@pytest.fixture
def client():
    with TestClient(src.create_app()) as c:
        yield c
