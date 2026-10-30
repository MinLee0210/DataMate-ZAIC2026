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
    llm_model: str = "Qwen/Qwen3.5-9B"
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
    # "malt": the dataAgent reasoning loop (services/qa/malt.py)
    pipeline: str = "malt"
    # vote pipeline: business analysis step before SQL generation (one LLM call per question)
    analyze: bool = True
    # JSON merged over LLM_EXTRA_BODY for the analysis call (vote) or every CA step, e.g. thinking:
    # DeepSeek '{"thinking": {"type": "enabled"}}',
    # vLLM Qwen3 '{"chat_template_kwargs": {"enable_thinking": true}}'
    analyze_extra_body: str = ""
    # thinking tokens count against max_tokens, so those calls get more room
    analyze_max_tokens: int = 16384
    # dataAgent: answer only when the final step's self-reported confidence (0-1) reaches this.
    # 0 = never gate. Chosen on dev200 from the PA-vs-tau curve (trace `agreement` = confidence).
    min_confidence: float = 0.0
    # dataAgent: solved train examples shown to the query step (0 = none); assets/examples/
    few_shot_k: int = 3
    # dataAgent self-consistency: runs per question, one approach each (malt_variants.md), majority
    # vote; answer only when the majority share >= MALT_MIN_AGREEMENT (chosen by scripts/calibrate)
    malt_samples: int = 1
    malt_min_agreement: float = 0.0
    # stop sampling once the remaining samples cannot change the answer or the gate (saves time
    # when the first samples agree; the trace's agreement is then a lower bound)
    malt_early_stop: bool = False
    # first approach used by sample 0 (malt_variants.md has 6): 3 gives three more independent votes
    malt_variant_offset: int = 0

    # language of the prompts and skills: "en" or "vi" (prompt_templates/vi/, skills/*/SKILL.vi.md)
    prompt_lang: str = "en"

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
