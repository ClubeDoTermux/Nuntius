import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

from nuntius.plugins.manager import PluginManager


@pytest.fixture
def plugin_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


def _create_plugin(pdir: Path, name: str, content: str):
    fpath = pdir / f"{name}.py"
    fpath.write_text(content)
    return fpath


GOOD_PLUGIN = '''
from nuntius.tools.registry import BaseTool, register

class HelloTool(BaseTool):
    name = "hello"
    description = "Say hello"
    parameters = {"type": "object", "properties": {}}
    async def execute(self) -> str:
        return "hello from plugin"

def setup(reg):
    register(HelloTool())
'''

PLUGIN_WITH_REGISTER = '''
from nuntius.tools.registry import BaseTool, register

class ByeTool(BaseTool):
    name = "bye"
    description = "Say bye"
    parameters = {"type": "object", "properties": {}}
    async def execute(self) -> str:
        return "bye from plugin"

def register(reg):
    reg(ByeTool())
'''

BAD_PLUGIN = '''
this is not valid python
'''

NO_SETUP_PLUGIN = '''
x = 1
'''


def test_load_good_plugin(plugin_dir):
    _create_plugin(plugin_dir, "test_good", GOOD_PLUGIN)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.plugin_count() == 1
    assert pm.error_count() == 0
    info = pm.get_plugin("test_good")
    assert info is not None
    assert info.name == "test_good"
    assert info.error == ""


def test_load_plugin_with_register_func(plugin_dir):
    _create_plugin(plugin_dir, "test_register", PLUGIN_WITH_REGISTER)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.plugin_count() == 1
    assert pm.error_count() == 0


def test_syntax_error_plugin(plugin_dir):
    _create_plugin(plugin_dir, "bad_syntax", BAD_PLUGIN)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.error_count() == 1
    info = pm.get_plugin("bad_syntax")
    assert info is not None
    assert "SyntaxError" in info.error or "syntax" in info.error


def test_no_setup_plugin_loads_without_error(plugin_dir):
    _create_plugin(plugin_dir, "noop", NO_SETUP_PLUGIN)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.plugin_count() == 1
    assert pm.error_count() == 0


def test_duplicate_plugin_name(plugin_dir):
    _create_plugin(plugin_dir, "dup", GOOD_PLUGIN)
    _create_plugin(plugin_dir, "dup", NO_SETUP_PLUGIN)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.plugin_count() == 1


def test_skips_init_and_hidden(plugin_dir):
    _create_plugin(plugin_dir, "__init__", GOOD_PLUGIN)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.plugin_count() == 0


def test_nonexistent_dir():
    pm = PluginManager({"plugins_dir": "/nonexistent/plugins"})
    pm.load_all()
    assert pm.plugin_count() == 0


def test_list_plugins(plugin_dir):
    _create_plugin(plugin_dir, "a", GOOD_PLUGIN)
    _create_plugin(plugin_dir, "b", PLUGIN_WITH_REGISTER)
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    plugins = pm.list_plugins()
    names = {p.name for p in plugins}
    assert "a" in names
    assert "b" in names


def test_skips_non_py_files(plugin_dir):
    (plugin_dir / "readme.txt").write_text("not a plugin")
    pm = PluginManager({"plugins_dir": str(plugin_dir)})
    pm.load_all()
    assert pm.plugin_count() == 0
