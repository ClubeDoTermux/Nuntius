import logging

from ..config import load_config, save_config
from ..routing import get_resolver, DEFAULT_ROLES
from ..tools.registry import BaseTool, register

logger = logging.getLogger("nuntius.tools.routing")


class GetRouting(BaseTool):
    name = "get_routing"
    description = "Mostra a configuracao de roteamento de agentes por modelo"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        cfg = load_config()
        resolver = get_resolver(cfg)
        if not resolver.is_enabled():
            return "Roteamento desabilitado. Ative em config.yaml: routing.enabled: true"
        summary = resolver.routing_summary()
        if not summary:
            return "Nenhuma rota configurada."
        lines = ["Roteamento de Agentes por Modelo:"]
        for r in summary:
            src = f"  [{r['role']}] -> {r['provider']}/{r['model']}"
            if r["description"]:
                src += f" ({r['description']})"
            lines.append(src)
        return "\n".join(lines)


class SetRoute(BaseTool):
    name = "set_route"
    description = "Configura roteamento para uma funcao de agente"
    parameters = {
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "description": "Funcao do agente",
                "enum": list(DEFAULT_ROLES.keys()),
            },
            "provider": {"type": "string", "description": "Nome do provedor (openai, deepseek, groq, gemini, etc)"},
            "model": {"type": "string", "description": "Nome do modelo"},
        },
        "required": ["role", "provider", "model"],
    }

    async def execute(self, role: str, provider: str, model: str) -> str:
        cfg = load_config()
        if "routing" not in cfg:
            cfg["routing"] = {"enabled": True, "roles": {}, "patterns": []}
        cfg["routing"]["enabled"] = True
        if "roles" not in cfg["routing"]:
            cfg["routing"]["roles"] = {}
        cfg["routing"]["roles"][role] = {"provider": provider, "model": model}
        save_config(cfg)
        get_resolver(cfg)
        return f"Rota definida: [{role}] -> {provider}/{model}"


class EnableRouting(BaseTool):
    name = "enable_routing"
    description = "Ativa ou desativa o roteamento de agentes"
    parameters = {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "description": "True para ativar, False para desativar"},
        },
        "required": ["enabled"],
    }

    async def execute(self, enabled: bool) -> str:
        cfg = load_config()
        if "routing" not in cfg:
            cfg["routing"] = {"enabled": enabled, "roles": {}, "patterns": []}
        cfg["routing"]["enabled"] = enabled
        save_config(cfg)
        return f"Roteamento {'ativado' if enabled else 'desativado'}."


register(GetRouting())
register(SetRoute())
register(EnableRouting())
