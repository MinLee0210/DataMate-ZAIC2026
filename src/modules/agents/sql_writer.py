import re

from src.modules.llm import LLM
from src.utils import get_logger
from src.utils.assets import load_prompt_template, render

logger = get_logger(__name__)

_BLOCK = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_THINK = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL)
_START = re.compile(r"\b(WITH|SELECT)\b", re.IGNORECASE)


def extract_sql(reply: str) -> str | None:
    """The query of a reply: the first fenced block, else the text from the first SELECT/WITH."""
    reply = _THINK.sub("", reply)
    block = _BLOCK.search(reply)
    text = block.group(1) if block else reply
    start = _START.search(text)
    sql = text[start.start() :].strip().rstrip(";").strip() if start else ""
    return sql or None


class SQLWriter:
    """A second model that writes the SQL of one named data query (text-to-SQL specialist).

    The analyst model decides what to ask; this one only turns the data question into SQL.
    Any failure returns None and the analyst's own SQL is used instead.
    """

    def __init__(self, llm: LLM, max_tokens: int = 1024) -> None:
        self.llm = llm
        self.max_tokens = max_tokens

    def write(self, values: dict[str, str], seed: int) -> str | None:
        prompt = render(load_prompt_template("sql_specialist"), **values)
        try:
            reply = self.llm.complete(
                [{"role": "user", "content": prompt}], seed=seed, max_tokens=self.max_tokens
            )
        except Exception:  # the analyst's SQL is the fallback; log and go on
            logger.exception("SQL writer failed")
            return None
        return extract_sql(reply)
