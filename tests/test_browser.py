import pytest


def test_browser_manager_import():
    from nuntius.core.browser import BrowserManager
    bm = BrowserManager()
    assert bm.available is False  # playwright not installed in CI
    assert bm._launching is False
    assert bm._browser is None


def test_browser_manager_close_no_launch():
    from nuntius.core.browser import BrowserManager
    bm = BrowserManager()
    import asyncio
    asyncio.run(bm.close())
    assert bm._browser is None


def test_browser_tools_fallback():
    from nuntius.tools.browser_tools import BrowserOpen, BrowserScreenshot
    tool = BrowserOpen()
    assert tool.name == "browser_open"
    assert "url" in tool.parameters["properties"]
    assert "timeout" in tool.parameters["properties"]
    assert "required" in tool.parameters
    assert "url" in tool.parameters["required"]
    tool2 = BrowserScreenshot()
    assert tool2.name == "browser_screenshot"
    assert "url" in tool2.parameters["properties"]


def test_browser_tools_registered():
    from nuntius.tools.registry import _tools
    assert "browser_open" in _tools
    assert "browser_screenshot" in _tools
