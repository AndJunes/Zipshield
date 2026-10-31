"""OpenRouter client built on httpx (already shipped with FastAPI, no extra dependencies).

No disk cache or concurrency: the backend persists the result in the `claims` table.
Retries with exponential backoff, and drops `response_format` and retries once if the
provider rejects it (400/422).
"""

import time

import httpx

from app.core.config import get_settings


class OpenRouterClient:
    def __init__(self, model: str | None = None):
        s = get_settings()
        self.api_key = s.openrouter_api_key
        self.url = s.openrouter_url
        self.model = model or s.openrouter_model
        self.max_tokens = s.llm_max_tokens
        self.temperature = s.llm_temperature
        self.timeout = s.llm_request_timeout
        self.max_retries = s.llm_max_retries

    def chat(self, system: str, user_text: str, image_urls, response_format=None) -> str:
        """Return the model's response text. Raises RuntimeError on failure."""
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Set it in backend/.env "
                "(you can reuse your OpenRouter key)."
            )

        content = [{"type": "text", "text": user_text}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Zipshield Claim Review",
        }
        return self._post_with_retries(payload, headers)

    def _post_with_retries(self, payload, headers) -> str:
        last = None
        dropped_rf = False
        for attempt in range(1, self.max_retries + 1):
            try:
                r = httpx.post(self.url, json=payload, headers=headers, timeout=self.timeout)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        return data["choices"][0]["message"]["content"]
                    except (ValueError, KeyError, IndexError, TypeError) as exc:
                        # 200 with an unexpected body shape (e.g. a moderation payload
                        # without "choices"): same error contract as a network failure,
                        # so the caller always gets a 502 and never a raw 500.
                        raise RuntimeError(
                            f"OpenRouter returned 200 with an unexpected body: {exc}"
                        ) from exc
                # If the provider rejects response_format, drop it and retry once.
                if r.status_code in (400, 422) and "response_format" in payload and not dropped_rf:
                    payload = {k: v for k, v in payload.items() if k != "response_format"}
                    dropped_rf = True
                    continue
                if r.status_code in (429, 500, 502, 503):       # transient -> retry
                    last = f"HTTP {r.status_code}"
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"OpenRouter HTTP {r.status_code}: {r.text[:300]}")
            except httpx.RequestError as e:
                last = str(e)
                time.sleep(2 ** attempt)
        raise RuntimeError(f"OpenRouter failed after {self.max_retries} attempts: {last}")
