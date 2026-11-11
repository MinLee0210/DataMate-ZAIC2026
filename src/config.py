import json
import os
import warnings
from pathlib import Path
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
# PIPELINE names: "malt" is the dataAgent; "vote" is the older k-candidate pipeline. The pod
# scripts used "ca" before the rename and it silently ran the vote pipeline, so legacy names are
# mapped explicitly and an unknown name fails instead of falling through.
PIPELINE_ALIASES = {
    "malt": "malt",
    "ca": "malt",
    "dataagent": "malt",
    "vote": "vote",
    "graph": "vote",
}
# env names that the rename retired; silently ignored by pydantic, so they are warned about here
LEGACY_ENV = (
    "CA_SAMPLES",
    "CA_MIN_AGREEMENT",
    "CA_EARLY_STOP",
    "CA_VARIANT_OFFSET",
    "CA_TYPE_GATES",
)


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
    # data-parallel replicas: comma-separated base URLs (one vLLM per GPU); worker thread i uses
    # URL i mod n. Empty = every thread uses LLM_BASE_URL.
    llm_base_urls: str = ""
    llm_api_key: str = "EMPTY"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    llm_timeout_s: float = 120.0
    # stream replies so time to first token can be measured; same output either way
    llm_stream: bool = True
    # JSON merged into every request body, e.g. Qwen3 without thinking on vLLM:
    # '{"chat_template_kwargs": {"enable_thinking": false}}'
    llm_extra_body: str = ""
    # optional second model that only writes the SQL of MALT's data queries (empty = off)
    sql_llm_base_url: str = ""
    sql_llm_model: str = ""
    seed: int = 2026
    # "vote": k SQL candidates + vote (services/qa/graph.py).
    # "malt": the dataAgent reasoning loop (services/qa/malt.py)
    pipeline: str = "malt"
    # vote pipeline: business analysis step before SQL generation (one LLM call per question)
    analyze: bool = True
    # JSON merged over LLM_EXTRA_BODY for the analysis call (vote) or every MALT step, e.g.
    # thinking:
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
    # warn the model when a query filters on a string value the data does not contain
    malt_literal_check: bool = True
    # stricter agreement/confidence for some answer types, as JSON, e.g. '{"list": 1.0}'
    # (empty = every type uses the global gate). Lists scored -0.37 on dev1000.
    malt_type_gates: str = ""
    # a final reply without `confidence` used to count as certainty (1.0); 0.5 is neutral
    malt_missing_confidence: float = 0.5
    # an unanswerable answer without `evidence` used to become 0.0 and then abstain under any gate;
    # cap it instead, so the guard survives without discarding a rulebook §7 answer
    malt_unanswerable_cap: float = 0.5
    # read the answer shape from the wording (list vs table vs scalar) and say it in the prompt
    answer_shape: bool = True
    # answer "unanswerable" with no LLM call when every period in the question is outside the data
    premise_check: bool = True
    # characters of the shop's README kept in the prompt; the conventions section is always kept
    readme_chars: int = 4000
    # answer high-volume families with deterministic SQL over the semantic views (no LLM call)
    family_compiler: bool = True
    # families the compiler may answer (comma separated; empty = all it recognises)
    compiler_families: str = (
        "revenue_plain,avg_order,best_day,count_cancelled,count_orders,"
        "count_orders_threshold,growth_plain"
    )

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
    def _pipeline_is_known(self) -> "Settings":
        name = (self.pipeline or "").strip().lower()
        if name not in PIPELINE_ALIASES:
            raise ValueError(
                f"PIPELINE must be one of {sorted(PIPELINE_ALIASES)}, got {self.pipeline!r}"
            )
        if PIPELINE_ALIASES[name] != name:
            warnings.warn(
                f"PIPELINE={self.pipeline!r} is a legacy name; using {PIPELINE_ALIASES[name]!r}",
                stacklevel=2,
            )
        self.pipeline = PIPELINE_ALIASES[name]
        legacy = [key for key in LEGACY_ENV if key in os.environ]
        if legacy:
            warnings.warn(
                f"ignoring retired env names {legacy}: use the MALT_* ones (MALT_SAMPLES, "
                "MALT_MIN_AGREEMENT, MALT_EARLY_STOP, MALT_VARIANT_OFFSET, MALT_TYPE_GATES)",
                stacklevel=2,
            )
        return self

    @model_validator(mode="after")
    def _final_mode_is_offline(self) -> "Settings":
        if self.final_mode and urlparse(self.llm_base_url).hostname not in LOCAL_HOSTS:
            raise ValueError(f"FINAL_MODE=1 needs a local LLM_BASE_URL, got {self.llm_base_url}")
        for url in self.llm_urls:
            if self.final_mode and urlparse(url).hostname not in LOCAL_HOSTS:
                raise ValueError(f"FINAL_MODE=1 needs local LLM_BASE_URLS, got {url}")
        if self.final_mode and self.sql_llm_base_url:
            if urlparse(self.sql_llm_base_url).hostname not in LOCAL_HOSTS:
                raise ValueError(
                    f"FINAL_MODE=1 needs a local SQL_LLM_BASE_URL, got {self.sql_llm_base_url}"
                )
        return self

    @property
    def extra_body(self) -> dict:
        return json.loads(self.llm_extra_body) if self.llm_extra_body else {}

    @property
    def llm_urls(self) -> list[str]:
        """The replica URLs; LLM_BASE_URL alone when LLM_BASE_URLS is empty."""
        urls = [u.strip() for u in self.llm_base_urls.split(",") if u.strip()]
        return urls or [self.llm_base_url]

    @property
    def type_gates(self) -> dict[str, float]:
        gates = json.loads(self.malt_type_gates) if self.malt_type_gates else {}
        return {str(k): float(v) for k, v in gates.items()}

    @property
    def analyze_body(self) -> dict:
        return json.loads(self.analyze_extra_body) if self.analyze_extra_body else {}


settings = Settings()
