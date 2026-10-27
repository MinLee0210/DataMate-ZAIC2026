"""Run a short pandas snippet written by the model, as Google's Conversational Analytics API does
for follow-up analysis.

The snippet sees `pd`, `results` (the named DataFrames retrieved earlier, as CA-API's
`AnalysisQuery.dataResultNames`), a read-only `query(sql) -> DataFrame` over the business's DuckDB,
and a small set of builtins. It must assign `result` (DataFrame, Series, list or scalar). Imports,
dunder and private names, and file or reflection builtins are rejected before it runs. The
snippet runs on a daemon thread with a timeout; a snippet that times out is abandoned.
"""

import ast
import threading
from collections.abc import Callable
from typing import Any

import pandas as pd

_SAFE_BUILTINS = {
    name: __builtins__[name] if isinstance(__builtins__, dict) else getattr(__builtins__, name)
    for name in (
        "abs all any bool dict enumerate filter float int isinstance len list map max min "
        "range reversed round set sorted str sum tuple zip"
    ).split()
}
_BANNED_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "input",
    "breakpoint",
    "__import__",
}


class UnsafeCodeError(ValueError):
    pass


def check_code(code: str) -> ast.Module:
    """Parse the snippet and reject what it must not do. Raises UnsafeCodeError or SyntaxError."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom | ast.Global | ast.Nonlocal):
            raise UnsafeCodeError("imports and global names are not allowed")
        if isinstance(node, ast.Name) and (node.id.startswith("_") or node.id in _BANNED_CALLS):
            raise UnsafeCodeError(f"name {node.id!r} is not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise UnsafeCodeError(f"attribute {node.attr!r} is not allowed")
        if isinstance(node, ast.Attribute) and node.attr in {"to_csv", "to_parquet", "to_pickle"}:
            raise UnsafeCodeError(f"attribute {node.attr!r} is not allowed")
    return tree


def to_frame(value: Any) -> pd.DataFrame:
    """The snippet's `result` as a DataFrame, the shape format_result expects."""
    if isinstance(value, pd.DataFrame):
        return value.reset_index(drop=True)
    if isinstance(value, pd.Series):
        return value.reset_index(drop=True).to_frame()
    if isinstance(value, list | tuple):
        return pd.DataFrame({"value": list(value)})
    return pd.DataFrame([[value]])


def run_python(
    code: str,
    query: Callable[[str], pd.DataFrame],
    results: dict[str, pd.DataFrame] | None = None,
    timeout_s: float = 20.0,
) -> pd.DataFrame:
    """Run the snippet and return its `result` as a DataFrame."""
    tree = check_code(code)
    scope: dict[str, Any] = {
        "__builtins__": _SAFE_BUILTINS,
        "pd": pd,
        "query": query,
        "results": {name: frame.copy() for name, frame in (results or {}).items()},
    }
    outcome: dict[str, Any] = {}

    def target() -> None:
        try:
            exec(compile(tree, "<verify>", "exec"), scope)  # noqa: S102 - checked above
            outcome["result"] = scope.get("result")
        except Exception as e:  # reported to the caller
            outcome["error"] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        raise TimeoutError(f"python snippet ran over {timeout_s}s")
    if "error" in outcome:
        raise outcome["error"]
    if outcome.get("result") is None:
        raise ValueError("the snippet did not set `result`")
    return to_frame(outcome["result"])
