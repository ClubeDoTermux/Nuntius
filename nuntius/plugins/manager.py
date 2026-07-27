import importlib
import importlib.util
import logging
import sys
from pathlib import Path

logger = logging.getLogger("nuntius.plugins")

BUILTIN_DIR = Path(__file__).parent / "builtin"


class PluginInfo:
    def __init__(self, name: str, path: str = "", error: str = ""):
        self.name = name
        self.path = path
        self.error = error

    def __repr__(self):
        return f"PluginInfo(name={self.name!r}, path={self.path!r}, error={self.error!r})"


class PluginManager:
    def __init__(self, config: dict | None = None):
        self.plugins: dict[str, PluginInfo] = {}
        config = config or {}
        self._dirs: list[Path] = []

        dirs_to_load = config.get("plugins_dir", "")
        if isinstance(dirs_to_load, str):
            dirs_to_load = [d.strip() for d in dirs_to_load.split(",") if d.strip()]

        for d in dirs_to_load:
            p = Path(d).expanduser().resolve()
            self._dirs.append(p)

        if config.get("load_builtins", False) and BUILTIN_DIR.is_dir():
            self._dirs.append(BUILTIN_DIR)

    def load_all(self):
        for d in self._dirs:
            self.load_directory(d)

    def load_directory(self, directory: str | Path):
        if not directory.is_dir():
            logger.debug(f"Plugin directory not found: {directory}")
            return

        for fpath in sorted(directory.iterdir()):
            if fpath.suffix != ".py":
                continue
            if fpath.name.startswith("__"):
                continue
            self._load_file(fpath)

    def _load_file(self, fpath: Path):
        mod_name = fpath.stem
        try:
            if mod_name in self.plugins:
                logger.warning(f"Duplicate plugin '{mod_name}', skipping {fpath}")
                return

            spec = importlib.util.spec_from_file_location(f"nuntius_plugin_{mod_name}", fpath)
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {fpath}")

            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod.__name__] = mod
            spec.loader.exec_module(mod)

            if hasattr(mod, "setup"):
                from ..tools.registry import register
                mod.setup(register)
            elif hasattr(mod, "register"):
                from ..tools.registry import register
                mod.register(register)
            else:
                logger.warning(f"Plugin '{mod_name}' has no setup() or register() function")

            self.plugins[mod_name] = PluginInfo(name=mod_name, path=str(fpath))
            logger.info(f"Loaded plugin: {mod_name} from {fpath}")
        except SyntaxError as e:
            msg = f"Syntax error in {fpath}: {e}"
            logger.warning(msg)
            self.plugins[mod_name] = PluginInfo(name=mod_name, path=str(fpath), error=msg)
        except Exception as e:
            msg = f"Failed to load {fpath}: {e}"
            logger.warning(msg)
            self.plugins[mod_name] = PluginInfo(name=mod_name, path=str(fpath), error=msg)

    def list_plugins(self) -> list[PluginInfo]:
        return list(self.plugins.values())

    def get_plugin(self, name: str) -> PluginInfo | None:
        return self.plugins.get(name)

    def plugin_count(self) -> int:
        return len(self.plugins)

    def error_count(self) -> int:
        return sum(1 for p in self.plugins.values() if p.error)
