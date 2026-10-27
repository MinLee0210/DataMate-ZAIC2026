import json
from pathlib import Path
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # app: the debug API (scripts/entrypoints.sh) and logging
    app_name: str = "datamate"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = False
    log_level: str = "INFO"

    # LLM: hosted OpenAI-compatible provider in dev_free, local vLLM in dev_constraint / final
    llm_base_url: str = "http://127.0.0.1:8001/v1"
    llm_model: str = "Qwen/Qwen3-14B"
    llm_api_key: str = "EMPTY"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    llm_timeout_s: float = 120.0
    # stream replies so time to first token can be measured; same output either way
    llm_stream: bool = True
    # JSON merged into every request body, e.g. Qwen3 without thinking on vLLM:
    # '{"chat_template_kwargs": {"enable_thinking": false}}'
    llm_extra_body: str = ""
    seed: int = 2026
    # "vote": k SQL candidates + vote (services/qa/graph.py).
    # "ca": the reasoning loop of Google's Conversational Analytics API (services/qa/ca.py)
    pipeline: str = "vote"
    # vote pipeline: business analysis step before SQL generation (one LLM call per question)
    analyze: bool = True
    # JSON merged over LLM_EXTRA_BODY for the analysis call (vote) or every CA step, e.g. thinking:
    # DeepSeek '{"thinking": {"type": "enabled"}}',
    # vLLM Qwen3 '{"chat_template_kwargs": {"enable_thinking": true}}'
    analyze_extra_body: str = ""
    # thinking tokens count against max_tokens, so those calls get more room
    analyze_max_tokens: int = 16384

    # FINAL_MODE=1: competition inference, only a local LLM endpoint is allowed
    final_mode: bool = False

    data_dir: Path = Path("/data")
    result_dir: Path = Path("/result")
    work_dir: Path = Path("/tmp/datamate")
    split: str = "private_test"

    # decision policy: k candidates, answer when vote agreement >= tau
    k: int = 3
    tau: float = 0.67
    # repair rounds after failed candidates; each round is one LLM step (1 + max_repairs in total)
    max_repairs: int = 5
    sql_timeout_s: float = 20.0
    max_result_rows: int = 200
    # question threads in `python -m src`; each has its own LLM client and DuckDB connections
    workers: int = 1
    # stop answering (abstain) after this many seconds, leaving margin inside the 6 h limit
    time_budget_s: float = 4.5 * 3600

    @model_validator(mode="after")
    def _final_mode_is_offline(self) -> "Settings":
        if self.final_mode and urlparse(self.llm_base_url).hostname not in LOCAL_HOSTS:
            raise ValueError(f"FINAL_MODE=1 needs a local LLM_BASE_URL, got {self.llm_base_url}")
        return self

    @property
    def extra_body(self) -> dict:
        return json.loads(self.llm_extra_body) if self.llm_extra_body else {}

    @property
    def analyze_body(self) -> dict:
        return json.loads(self.analyze_extra_body) if self.analyze_extra_body else {}


settings = Settings()
