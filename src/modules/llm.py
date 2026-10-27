import time

from openai import OpenAI

from src.config import settings
from src.models import LLMUsage
from src.modules.base import BaseModules


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

    def complete(
        self,
        messages: list[dict[str, str]],
        seed: int | None = None,
        extra_body: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """`extra_body` is merged over LLM_EXTRA_BODY for this call (e.g. thinking for one step)."""
        record = LLMUsage()
        started = time.perf_counter()
        try:
            body = {**settings.extra_body, **(extra_body or {})}
            request = {
                "model": self.model,
                "messages": messages,
                "temperature": settings.llm_temperature,
                "max_tokens": max_tokens or settings.llm_max_tokens,
                "seed": settings.seed if seed is None else seed,
                "extra_body": body or None,
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
