from dataclasses import asdict, dataclass


@dataclass
class LLMUsage:
    """One chat call: tokens and timings, for the efficiency report (src/evaluate/metrics.py)."""

    prompt_tokens: int | None = None  # None when the provider does not report usage
    completion_tokens: int | None = None
    ttft_s: float | None = None  # time to first token; None without streaming
    latency_s: float = 0.0  # request sent -> last token
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
