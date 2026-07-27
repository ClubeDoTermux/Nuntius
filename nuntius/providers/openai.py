import json
import re
from typing import AsyncGenerator, Optional

import httpx


def _clean_error(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    lines = [l for l in text.split("\n") if l.strip()][:3]
    return " | ".join(lines)[:300]


class ProviderError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = _clean_error(message)
        super().__init__(f"HTTP {status}: {self.message}")


class OpenAIProvider:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120)

    async def chat_completion(
        self,
        messages: list[dict],
        model: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> dict:
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=body,
            headers=headers,
        )
        if response.is_error:
            try:
                err = response.json()
                detail = err.get("error", {}).get("message", str(response))
            except Exception:
                detail = response.text
            raise ProviderError(response.status_code, detail)
        return response.json()

    async def stream_chat(
        self,
        messages: list[dict],
        model: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[dict, None]:
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=body,
                headers=headers,
            ) as response:
                if response.is_error:
                    try:
                        err = await response.aread()
                        detail = json.loads(err).get("error", {}).get("message", str(response))
                    except Exception:
                        detail = (await response.aread()).decode("utf-8", errors="replace")
                    raise ProviderError(response.status_code, detail)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue

    async def close(self):
        await self.client.aclose()
