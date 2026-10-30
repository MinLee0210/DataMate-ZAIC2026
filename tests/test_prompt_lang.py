import re

import pytest

from src.config import settings
from src.utils.assets import SKILLS_DIR, load_prompt_template, load_skill

VI_TEMPLATES = sorted(p.stem for p in (SKILLS_DIR.parent / "prompt_templates" / "vi").glob("*.md"))
VI_SKILLS = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.vi.md"))


def test_english_is_the_default():
    assert settings.prompt_lang == "en"
    assert "Reason over" in load_prompt_template("ca_results_thought")


@pytest.mark.parametrize("name", VI_TEMPLATES)
def test_vietnamese_templates_keep_placeholders_and_json_keys(name, monkeypatch):
    en = load_prompt_template(name)
    monkeypatch.setattr(settings, "prompt_lang", "vi")
    vi = load_prompt_template(name)
    assert vi != en
    for token in re.findall(r"\{\{\w+\}\}", en):
        assert token in vi
    for key in ('"thought"', '"action"', '"data_queries"', '"sample_fields"', '"answer_type"'):
        assert (key in en) == (key in vi)


@pytest.mark.parametrize("name", VI_SKILLS)
def test_vietnamese_skills_load(name, monkeypatch):
    en = load_skill(name)
    monkeypatch.setattr(settings, "prompt_lang", "vi")
    assert load_skill(name) != en


def test_vietnamese_falls_back_to_english_when_a_file_is_missing(monkeypatch):
    en = load_prompt_template("analyze")  # only the vote pipeline uses it: no Vietnamese copy
    monkeypatch.setattr(settings, "prompt_lang", "vi")
    assert load_prompt_template("analyze") == en
