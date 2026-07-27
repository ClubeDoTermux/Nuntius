import asyncio
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger("nuntius.browser")

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._available = _PLAYWRIGHT_AVAILABLE
        self._launching = False

    @property
    def available(self) -> bool:
        return self._available

    async def launch(self):
        if self._browser or not self._available or self._launching:
            return
        self._launching = True
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--single-process",
                ],
            )
            self._context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Nuntius/1.0",
                viewport={"width": 1280, "height": 720},
            )
            logger.info("Browser launched")
        except Exception as e:
            self._available = False
            logger.warning(f"Browser launch failed: {e}")
        finally:
            self._launching = False

    async def get_page_content(self, url: str, timeout: int = 30000) -> str:
        await self.launch()
        if not self._context:
            return "Navegador indisponivel."
        try:
            page = await self._context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await page.wait_for_timeout(2000)
            title = await page.title()
            text = await page.evaluate("document.body?.innerText || ''")
            content = text[:8000] if text else ""
            await page.close()
            result = f"Title: {title}\n\n{content}" if content else f"Title: {title}\n(no text content)"
            return result[:10000]
        except Exception as e:
            return f"Erro ao acessar {url}: {e}"

    async def screenshot(self, url: str, timeout: int = 30000) -> str:
        await self.launch()
        if not self._context:
            return "Navegador indisponivel."
        try:
            page = await self._context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await page.wait_for_timeout(2000)
            tmp = Path(tempfile.mkdtemp()) / "nuntius_screenshot.png"
            await page.screenshot(path=str(tmp), full_page=False)
            await page.close()
            return str(tmp)
        except Exception as e:
            return f"Erro ao capturar tela: {e}"

    async def close(self):
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self._available = _PLAYWRIGHT_AVAILABLE
        logger.info("Browser closed")
