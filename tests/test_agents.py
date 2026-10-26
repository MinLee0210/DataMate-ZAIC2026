import pytest

from src.modules.agents.base import BaseAgent
from src.modules.agents.prompts import load_prompt_template, render
from src.modules.agents.skills import list_skills, load_skill
from src.modules.agents.sql_agent import DEFAULT_SKILLS, SQLAgent
from tests.conftest import FakeLLM


def test_list_and_load_skills():
    assert set(DEFAULT_SKILLS) <= set(list_skills())
    body = load_skill("ranking-rules")
    assert body.startswith("# Ranking rules")
    assert "name:" not in body


@pytest.mark.parametrize("name", ["missing", "../services"])
def test_unknown_skill(name):
    with pytest.raises(KeyError):
        load_skill(name)


def test_agent_without_skills_uses_its_prompt_template():
    assert BaseAgent().system_prompt == load_prompt_template("default")


def test_unknown_prompt_template():
    with pytest.raises(KeyError):
        load_prompt_template("../skills/summarize/SKILL")


def test_sql_agent_system_prompt_includes_its_skills():
    agent = SQLAgent(llm=FakeLLM())
    assert agent.system_prompt.startswith(load_prompt_template("sql_agent"))
    assert "# Ranking rules" in agent.system_prompt
    assert len(agent.variants) >= 3


def test_agent_unknown_skill_fails_at_build():
    with pytest.raises(KeyError):
        SQLAgent(llm=FakeLLM(), skills=["nope"])


def test_render_leaves_single_braces():
    assert render('{"a": 1} {{x}}', x="y") == '{"a": 1} y'
