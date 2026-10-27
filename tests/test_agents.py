import pytest

from src.modules.agents.base import BaseAgent
from src.modules.agents.sql_agent import DEFAULT_SKILLS, SQLAgent
from src.utils.assets import list_skills, load_prompt_template, load_skill, render
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


def test_rulebook_goes_last_in_system_prompt():
    agent = SQLAgent(llm=FakeLLM(), rulebook="## 9. Đáp án\nKhách sộp nhất: từ 3 đơn trở lên")
    assert agent.system_prompt.startswith(SQLAgent(llm=FakeLLM()).system_prompt)
    assert agent.system_prompt.endswith("Khách sộp nhất: từ 3 đơn trở lên")
    assert "{{rulebook}}" not in agent.system_prompt
    assert SQLAgent(llm=FakeLLM()).rulebook == ""


@pytest.mark.parametrize(
    "reply",
    [
        'Here: {"action": "final", "x": 1} and also {"action": "abstain"}',
        '{"action": "final", "x": 1}\n\nNote: the result {looks} right.',
        '<think>maybe {not json}</think>```json\n{"action": "final", "x": 1}\n```',
    ],
)
def test_first_json_object_ignores_extra_text(reply):
    from src.modules.agents.sql_agent import first_json_object

    assert first_json_object(reply) == {"action": "final", "x": 1}
