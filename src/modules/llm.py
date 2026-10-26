from openai import OpenAI

from src.config import settings
from src.modules.base import BaseModules


class LLM(BaseModules):
    """OpenAI-compatible chat client: a hosted provider (dev_free) or local vLLM (final).

    Temperature, seed and max tokens are fixed from settings so reruns are reproducible.
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

    @property
    def client(self) -> OpenAI:
        # created on first use so the app can start without an endpoint
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url, api_key=self.api_key, timeout=settings.llm_timeout_s
            )
        return self._client

    def complete(self, messages: list[dict[str, str]], seed: int | None = None) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            seed=settings.seed if seed is None else seed,
            extra_body=settings.extra_body or None,
        )
        return response.choices[0].message.content or ""
