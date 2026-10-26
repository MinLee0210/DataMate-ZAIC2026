import time
from dataclasses import asdict, dataclass

from openai import OpenAI

from src.config import settings
from src.modules.base import BaseModules


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


class LLM(BaseModules):
    """OpenAI-compatible chat client: a hosted provider (dev_free) or local vLLM (final).

    Temperature, seed and max tokens are fixed from settings so reruns are reproducible.
    Every call appends an `LLMUsage` record; `pop_usage()` hands them to the caller's trace.
    Streaming (LLM_STREAM, default on) only changes how the reply arrives, not what is generated;
    it is needed to measure time to first token.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        super().__init__()
        self.model = model or settings.llm_model
        self.base_url = base_url or settings.llm_base_url
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self._client: OpenAI | None = None
        self.usage: list[LLMUsage] = []

    @property
    def client(self) -> OpenAI:
        # created on first use so the app can start without an endpoint
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url, api_key=self.api_key, timeout=settings.llm_timeout_s
            )
        return self._client

    def pop_usage(self) -> list[LLMUsage]:
        usage, self.usage = self.usage, []
        return usage

    def complete(self, messages: list[dict[str, str]], seed: int | None = None) -> str:
        record = LLMUsage()
        started = time.perf_counter()
        try:
            request = {
                "model": self.model,
                "messages": messages,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "seed": settings.seed if seed is None else seed,
                "extra_body": settings.extra_body or None,
            }
            if settings.llm_stream:
                return self._stream(request, record, started)
            response = self.client.chat.completions.create(**request)
            if response.usage:
                record.prompt_tokens = response.usage.prompt_tokens
                record.completion_tokens = response.usage.completion_tokens
            return response.choices[0].message.content or ""
        except Exception as e:
            record.error = f"{type(e).__name__}: {e}"
            raise
        finally:
            record.latency_s = round(time.perf_counter() - started, 4)
            self.usage.append(record)

    def _stream(self, request: dict, record: LLMUsage, started: float) -> str:
        stream = self.client.chat.completions.create(
            **request, stream=True, stream_options={"include_usage": True}
        )
        parts: list[str] = []
        for chunk in stream:
            if chunk.usage:  # the last chunk, with include_usage
                record.prompt_tokens = chunk.usage.prompt_tokens
                record.completion_tokens = chunk.usage.completion_tokens
            for choice in chunk.choices:
                delta = choice.delta
                piece = delta.content or ""
                if record.ttft_s is None and (piece or getattr(delta, "reasoning_content", None)):
                    record.ttft_s = round(time.perf_counter() - started, 4)
                parts.append(piece)
        return "".join(parts)
