import logging

import httpx

from .registry import BaseTool, register

logger = logging.getLogger("nuntius.tools.browser")

_browser = None


def _get_browser():
    global _browser
    if _browser is None:
        from ..core.browser import BrowserManager
        _browser = BrowserManager()
    return _browser


async def close_browser():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None


class BrowserOpen(BaseTool):
    name = "browser_open"
    description = "Abre uma URL em navegador headless e retorna o texto da pagina (JavaScript incluso)"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL completa para abrir"},
            "timeout": {"type": "integer", "description": "Timeout em milissegundos", "default": 30000},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, timeout: int = 30000) -> str:
        b = _get_browser()
        if not b.available:
            cfg_url = url
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                try:
                    resp = await client.get(url, headers={"User-Agent": "Nuntius/1.0"})
                    text = resp.text[:8000]
                except Exception as e:
                    text = f"Playwright nao disponivel e fallback HTTP falhou: {e}"
            return text
        return await b.get_page_content(url, timeout)


class BrowserScreenshot(BaseTool):
    name = "browser_screenshot"
    description = "Abre uma URL em navegador headless e salva um screenshot. Retorna o caminho da imagem."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL completa"},
            "timeout": {"type": "integer", "description": "Timeout em milissegundos", "default": 30000},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, timeout: int = 30000) -> str:
        b = _get_browser()
        if not b.available:
            return "Playwright nao instalado. Para usar: pip install 'nuntius[browser]' && playwright install chromium"
        return await b.screenshot(url, timeout)


register(BrowserOpen())
register(BrowserScreenshot())
