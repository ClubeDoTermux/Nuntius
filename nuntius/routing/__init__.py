import logging
import re

from ..config import load_config, get_active_provider
from ..providers.base import ProviderRegistry

logger = logging.getLogger("nuntius.routing")

DEFAULT_ROLES = {
    "code": {"description": "Codificacao e implementacao"},
    "shell": {"description": "Comandos shell e automacao"},
    "search": {"description": "Pesquisa web e leitura de documentacao"},
    "writer": {"description": "Escrita e revisao de conteudo"},
    "debug": {"description": "Analise de erros e debugging"},
    "analysis": {"description": "Analise de dados e raciocinio logico"},
    "plan": {"description": "Planejamento e arquitetura"},
    "review": {"description": "Revisao de codigo e qualidade"},
}

DEFAULT_PATTERNS = [
    {"pattern": r"\b(python|javascript|typescript|rust|go|java|c\+\+|ruby|php|swift|kotlin|scala)\b", "role": "code"},
    {"pattern": r"\b(implement|criar|create|function|classe|class|metodo|method|api|endpoint)\b", "role": "code"},
    {"pattern": r"\b(bash|shell|terminal|comando|command|install|pkg|apt|pip|npm)\b", "role": "shell"},
    {"pattern": r"\b(search|pesquisar|google|find|buscar|lookup|pesquisa|pesquise)\b", "role": "search"},
    {"pattern": r"\b(write|escrever|document|documentar|texto|artigo|post|blog|email|mensagem)\b", "role": "writer"},
    {"pattern": r"\b(debug|error|erro|bug|fix|corrigir|fail|fault|exception|traceback|crash)\b", "role": "debug"},
    {"pattern": r"\b(analyze|analisar|analise|analyze|compared|compare|metrics|estatisticas|stats)\b", "role": "analysis"},
    {"pattern": r"\b(plan|planejar|arquitetura|architecture|design|estrutura|structure|projeto)\b", "role": "plan"},
    {"pattern": r"\b(review|revisar|code.?review|pr|pull.?request|quality|qualidade)\b", "role": "review"},
]


class RouteResolver:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.routing_cfg = self.config.get("routing", {})
        self._resolved_cache: dict[str, tuple[str, str, object]] = {}

    def is_enabled(self) -> bool:
        return self.routing_cfg.get("enabled", False)

    def get_role_config(self, role: str) -> dict | None:
        roles = self.routing_cfg.get("roles", {})
        return roles.get(role)

    def resolve_role(self, role: str) -> tuple[str, str, dict | None]:
        if not self.is_enabled():
            return self._default_provider_model()
        role_cfg = self.get_role_config(role)
        if role_cfg:
            provider_name = role_cfg.get("provider", "")
            model = role_cfg.get("model", "")
            if provider_name and model:
                prov = self._build_provider(provider_name)
                return (provider_name, model, prov)
        return self._default_provider_model()

    def resolve_task(self, task: str) -> tuple[str, str, dict | None, str]:
        if not self.is_enabled():
            prov_name, model, prov = self._default_provider_model()
            return (prov_name, model, prov, "")

        task_lower = task.lower()
        patterns = self.routing_cfg.get("patterns", DEFAULT_PATTERNS)

        for entry in patterns:
            try:
                if re.search(entry["pattern"], task_lower):
                    role = entry.get("role", "")
                    role_cfg = self.get_role_config(role)
                    if role_cfg:
                        provider_name = role_cfg.get("provider", "")
                        model = role_cfg.get("model", "")
                        if provider_name and model:
                            prov = self._build_provider(provider_name)
                            return (provider_name, model, prov, role)
            except re.error:
                continue

        prov_name, model, prov = self._default_provider_model()
        return (prov_name, model, prov, "")

    def _default_provider_model(self) -> tuple[str, str, object | None]:
        pname = self.config.get("provider", "openai")
        model = self.config.get("model", "gpt-4o-mini")
        try:
            provider_cfg = get_active_provider(self.config)
            prov = ProviderRegistry.create(
                pname,
                api_key=provider_cfg.get("api_key", ""),
                base_url=provider_cfg.get("base_url", ""),
            )
            return (pname, model, prov)
        except Exception as e:
            logger.warning(f"Failed to create default provider '{pname}': {e}")
            return (pname, model, None)

    def _build_provider(self, provider_name: str) -> object | None:
        try:
            providers = self.config.get("providers", {})
            pcfg = providers.get(provider_name)
            if not pcfg:
                logger.warning(f"Provider '{provider_name}' not found in config")
                return None
            return ProviderRegistry.create(
                provider_name,
                api_key=pcfg.get("api_key", ""),
                base_url=pcfg.get("base_url", ""),
            )
        except Exception as e:
            logger.warning(f"Failed to create provider '{provider_name}': {e}")
            return None

    def routing_summary(self) -> list[dict]:
        if not self.is_enabled():
            return []
        roles = self.routing_cfg.get("roles", {})
        result = []
        for role, rcfg in roles.items():
            result.append({
                "role": role,
                "provider": rcfg.get("provider", ""),
                "model": rcfg.get("model", ""),
                "description": DEFAULT_ROLES.get(role, {}).get("description", ""),
            })
        return result


_default_resolver = None


def get_resolver(config: dict | None = None) -> RouteResolver:
    global _default_resolver
    if config is not None:
        return RouteResolver(config)
    if _default_resolver is None:
        _default_resolver = RouteResolver()
    return _default_resolver


def reset_resolver():
    global _default_resolver
    _default_resolver = None
