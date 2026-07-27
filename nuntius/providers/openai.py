import asyncio
import json
import logging
import random
import re
from typing import AsyncGenerator, Optional

import httpx

from .base import BaseProvider, ProviderRegistry

logger = logging.getLogger("nuntius.providers.openai")


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


async def _retry_with_backoff(coro_factory, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except ProviderError as e:
            if e.status == 429 and attempt < max_retries - 1:
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limited (429). Retrying in {wait:.1f}s (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait)
                continue
            raise


class OpenAIProvider(BaseProvider):
    name = "openai"
    default_model = "gpt-4o-mini"

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

        async def _do_request():
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=body,
                    headers=headers,
                )
            except httpx.TimeoutException:
                raise ProviderError(0, "Tempo limite excedido. O servidor demorou muito para responder.")
            except httpx.ConnectError:
                raise ProviderError(0, "Falha de conexao. Verifique sua internet e se a URL esta correta.")
            if response.is_error:
                try:
                    err = response.json()
                    detail = err.get("error", {}).get("message", str(response))
                except Exception:
                    detail = response.text
                raise ProviderError(response.status_code, detail)
            return response.json()
        return await _retry_with_backoff(_do_request)

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

        async def _do_connect():
            c = httpx.AsyncClient(timeout=120)
            try:
                r = await c.send(
                    httpx.Request("POST", f"{self.base_url}/chat/completions", json=body, headers=headers),
                    stream=True,
                )
            except httpx.TimeoutException:
                await c.aclose()
                raise ProviderError(0, "Tempo limite excedido. O servidor demorou muito para responder.")
            except httpx.ConnectError:
                await c.aclose()
                raise ProviderError(0, "Falha de conexao. Verifique sua internet e se a URL esta correta.")
            if r.is_error:
                try:
                    err_text = await r.aread()
                    detail = json.loads(err_text).get("error", {}).get("message", str(r))
                except Exception:
                    detail = str(r)
                await c.aclose()
                raise ProviderError(r.status_code, detail)
            return c, r

        client, response = await _retry_with_backoff(_do_connect)
        try:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue
        finally:
            await response.aclose()
            await client.aclose()

    async def close(self):
        await self.client.aclose()


ProviderRegistry.register("openai", OpenAIProvider)
