"""File IO for src/assets/: prompt templates (`prompt_templates/<name>.md`) and skills
(`skills/<name>/SKILL.md`). Reading and placeholder filling only; no agent logic."""

from pathlib import Path

from src.config import settings

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
PROMPT_TEMPLATES_DIR = ASSETS_DIR / "prompt_templates"
SKILLS_DIR = ASSETS_DIR / "skills"


def load_prompt_template(name: str, templates_dir: Path = PROMPT_TEMPLATES_DIR) -> str:
    """Return `assets/prompt_templates/<name>.md`. Raises KeyError if unknown.

    With PROMPT_LANG=vi, `prompt_templates/vi/<name>.md` is used when it exists (JSON keys, action
    names and SQL stay English: code parses them)."""
    path = templates_dir / f"{name}.md"
    if settings.prompt_lang == "vi":
        vi = templates_dir / "vi" / f"{name}.md"
        if vi.is_file() and vi.resolve().parent.parent == templates_dir.resolve():
            return vi.read_text().strip()
    if not path.is_file() or path.resolve().parent != templates_dir.resolve():
        raise KeyError(name)
    return path.read_text().strip()


def render(template: str, **values: str) -> str:
    """Fill `{{name}}` placeholders. Single braces are left alone (SQL and JSON use them)."""
    for name, value in values.items():
        template = template.replace("{{" + name + "}}", value)
    return template


def list_skills(skills_dir: Path = SKILLS_DIR) -> list[str]:
    return sorted(p.parent.name for p in skills_dir.glob("*/SKILL.md"))


def load_skill(name: str, skills_dir: Path = SKILLS_DIR) -> str:
    """Return a skill body (frontmatter removed). Raises KeyError if unknown."""
    path = skills_dir / name / "SKILL.md"
    if not path.is_file() or path.resolve().parent.parent != skills_dir.resolve():
        raise KeyError(name)
    if settings.prompt_lang == "vi" and (skills_dir / name / "SKILL.vi.md").is_file():
        path = skills_dir / name / "SKILL.vi.md"
    text = path.read_text()
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()
