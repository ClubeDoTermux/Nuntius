import importlib
import pkgutil
import logging

from .base import PlatformBase, PlatformInfo

_registry: dict[str, type[PlatformBase]] = {}
_log = logging.getLogger("nuntius.platforms")


def register(platform_class: type[PlatformBase]):
    name = platform_class.info.name
    _registry[name] = platform_class


def get_platform(name: str) -> type[PlatformBase] | None:
    _ensure_discovered()
    return _registry.get(name)


def list_platforms() -> dict[str, PlatformInfo]:
    _ensure_discovered()
    return {name: cls.info for name, cls in _registry.items()}


def load_platform(name: str, config: dict, agent) -> PlatformBase | None:
    _ensure_discovered()
    cls = _registry.get(name)
    if cls is None:
        return None
    return cls(config, agent)


_discovered = False


def _ensure_discovered():
    global _discovered
    if _discovered:
        return
    _discovered = True
    import nuntius.platforms as pkg
    pkg_path = pkg.__path__[0]
    for importer, modname, is_pkg in pkgutil.iter_modules([pkg_path]):
        if modname in ("base", "__init__", "gateway"):
            continue
        try:
            importlib.import_module(f"nuntius.platforms.{modname}")
        except Exception as e:
            _log.debug(f"Platform module '{modname}' not loaded: {e}")


__all__ = [
    "PlatformBase", "PlatformInfo",
    "register", "get_platform", "list_platforms", "load_platform",
]
