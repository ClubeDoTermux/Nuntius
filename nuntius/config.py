import logging
import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(os.getenv("NUNTIUS_CONFIG_DIR", Path.home() / ".config" / "nuntius"))
DATA_DIR = Path(os.getenv("NUNTIUS_DATA_DIR", Path.home() / ".local" / "share" / "nuntius"))
CONFIG_PATH = CONFIG_DIR / "config.yaml"

PROVIDER_INFO = {
    "openai": {
        "name": "OpenAI",
        "url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "site": "https://platform.openai.com/api-keys",
        "free": False,
    },
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "site": "https://platform.deepseek.com/api_keys",
        "free": False,
    },
    "groq": {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1",
        "models": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        "site": "https://console.groq.com/keys",
        "free": True,
    },
    "ollama": {
        "name": "Ollama (local)",
        "url": "http://localhost:11434/v1",
        "models": [
            "llama3.2", "llama3.1", "mistral", "codellama",
            "qwen2.5", "phi4", "llava",
        ],
        "site": "",
        "free": True,
    },
    "nvidia": {
        "name": "NVIDIA NIM",
        "url": "https://integrate.api.nvidia.com/v1",
        "models": [
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.3-70b-instruct",
            "mistralai/mistral-7b-instruct-v0.3",
            "google/gemma-2-27b-it",
        ],
        "site": "https://build.nvidia.com/explore/discover",
        "free": True,
    },
    "github": {
        "name": "GitHub Models",
        "url": "https://models.inference.ai.azure.com",
        "models": [
            "gpt-4o", "gpt-4o-mini", "gpt-4o-turbo",
            "Phi-3.5-MoE-instruct", "Phi-3.5-mini-instruct",
            "Llama-3.1-70B-Instruct", "Llama-3.1-8B-Instruct",
            "Cohere-command-r-plus-08-2024",
            "Mistral-large-2407", "AI21-Jamba-1.5-Mini",
        ],
        "site": "https://github.com/marketplace/models",
        "free": True,
    },
    "openrouter": {
        "name": "OpenRouter",
        "url": "https://openrouter.ai/api/v1",
        "models": [
            "openai/gpt-4o", "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash",
            "meta-llama/llama-3.1-405b-instruct",
            "mistralai/mistral-large-2411",
            "deepseek/deepseek-chat",
        ],
        "site": "https://openrouter.ai/keys",
        "free": False,
    },
    "together": {
        "name": "Together AI",
        "url": "https://api.together.xyz/v1",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
            "mistralai/Mixtral-8x22B-Instruct-v0.1",
            "deepseek-ai/DeepSeek-V3",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ],
        "site": "https://api.together.ai/settings/api-keys",
        "free": False,
    },
    "mistral": {
        "name": "Mistral AI",
        "url": "https://api.mistral.ai/v1",
        "models": [
            "mistral-large-latest", "mistral-small-latest",
            "open-mistral-nemo", "codestral-latest",
        ],
        "site": "https://console.mistral.ai/api-keys/",
        "free": False,
    },
    "xai": {
        "name": "xAI (Grok)",
        "url": "https://api.x.ai/v1",
        "models": ["grok-beta", "grok-vision-beta"],
        "site": "https://x.ai/api",
        "free": False,
    },
    "perplexity": {
        "name": "Perplexity",
        "url": "https://api.perplexity.ai",
        "models": [
            "sonar-pro", "sonar", "sonar-reasoning-pro",
            "sonar-deep-research",
        ],
        "site": "https://www.perplexity.ai/settings/api",
        "free": False,
    },
    "fireworks": {
        "name": "Fireworks AI",
        "url": "https://api.fireworks.ai/inference/v1",
        "models": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/qwen2p5-coder-32b-instruct",
            "accounts/fireworks/models/deepseek-v3",
        ],
        "site": "https://fireworks.ai/api-keys",
        "free": True,
    },
    "gemini": {
        "name": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": [
            "gemini-2.0-flash", "gemini-2.0-flash-lite",
            "gemini-1.5-pro", "gemini-1.5-flash",
        ],
        "site": "https://aistudio.google.com/apikey",
        "free": True,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "url": "https://api.anthropic.com/v1",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
        "site": "https://console.anthropic.com/",
        "free": False,
    },
}

DEFAULT_CONFIG = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "providers": {name: {"api_key": "", "base_url": info["url"]} for name, info in PROVIDER_INFO.items()},
    "platforms": {
        "telegram": {"enabled": False, "token": ""},
        "discord": {"enabled": False, "token": ""},
        "slack": {"enabled": False, "token": "", "signing_secret": ""},
        "whatsapp": {"enabled": False, "phone_number_id": "", "token": "", "verify_token": "nuntius_verify"},
        "matrix": {"enabled": False, "homeserver": "", "user_id": "", "password": ""},
        "email": {"enabled": False, "imap_server": "", "smtp_server": "", "email": "", "password": "", "imap_port": 993, "smtp_port": 587, "poll_interval": 60},
        "signal": {"enabled": False, "phone_number": "", "signal_cli_path": "signal-cli"},
        "teams": {"enabled": False, "webhook_url": ""},
        "googlechat": {"enabled": False, "webhook_url": ""},
        "line": {"enabled": False, "channel_access_token": "", "channel_secret": ""},
        "irc": {"enabled": False, "server": "", "port": 6697, "nickname": "NuntiusBot", "channels": [], "use_tls": True},
        "webhook": {"enabled": False, "port": 8088, "path": "/webhook", "secret": ""},
        "github": {"enabled": False, "token": ""},
        "drive": {"enabled": False, "credentials_path": ""},
    },
    "mcp_servers": {
        "example": {"command": "python", "args": ["-m", "mcp_server"], "enabled": False},
    },
    "security": {
        "bash_approval": False,
        "dangerous_command_protection": True,
        "block_internal_networks": True,
        "allowed_commands": [],
        "blocked_commands": ["sudo rm", "rm -rf /", "rm -rf /*", "mkfs", "dd if=", "> /dev/sd", "chmod 777 /", "wget -O- | sh", "curl | sh", "mv / ", ":(){ :|:& };:"],
    },
    "auto_learn": {"enabled": True},
    "routing": {
        "enabled": False,
        "roles": {
            "code": {"provider": "", "model": ""},
            "shell": {"provider": "", "model": ""},
            "search": {"provider": "", "model": ""},
            "writer": {"provider": "", "model": ""},
            "debug": {"provider": "", "model": ""},
            "analysis": {"provider": "", "model": ""},
            "plan": {"provider": "", "model": ""},
            "review": {"provider": "", "model": ""},
        },
        "patterns": [
            {"pattern": "\\b(python|javascript|typescript|rust|go|java|c\\+\\+|ruby|php|implement|criar|create|function|classe|class|api|endpoint)\\b", "role": "code"},
            {"pattern": "\\b(bash|shell|terminal|comando|command|install|pkg|apt|pip|npm)\\b", "role": "shell"},
            {"pattern": "\\b(search|pesquisar|google|find|buscar|lookup|pesquisa)\\b", "role": "search"},
            {"pattern": "\\b(write|escrever|document|texto|artigo|post|blog|email)\\b", "role": "writer"},
            {"pattern": "\\b(debug|error|erro|bug|fix|corrigir|fail|exception|traceback|crash)\\b", "role": "debug"},
            {"pattern": "\\b(analyze|analisar|analise|metrics|estatisticas|stats|compared|compare)\\b", "role": "analysis"},
            {"pattern": "\\b(plan|planejar|arquitetura|architecture|design|estrutura|structure|projeto)\\b", "role": "plan"},
            {"pattern": "\\b(review|revisar|code.?review|pr|pull.?request|quality|qualidade)\\b", "role": "review"},
        ],
    },
    "memory": {"enabled": True, "db_path": str(DATA_DIR / "nuntius.db"), "vector_enabled": True, "vector_path": str(DATA_DIR / "chroma"), "auto_retrieval": True, "retrieval_count": 3},
    "tools": {"enabled": True},
    "plugins": {"enabled": True, "plugins_dir": str(CONFIG_DIR / "plugins")},
    "log_level": "WARNING",
}


def _apply_env_overrides(cfg: dict):
    for provider_name in cfg.get("providers", {}):
        env_key = f"NUNTIUS_{provider_name.upper()}_KEY"
        env_val = os.getenv(env_key)
        if env_val:
            cfg["providers"][provider_name]["api_key"] = env_val
    return cfg


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return _apply_env_overrides(DEFAULT_CONFIG.copy())
    with open(CONFIG_PATH) as f:
        user = yaml.safe_load(f) or {}
    merged = DEFAULT_CONFIG.copy()
    if "providers" in user:
        for k, v in user["providers"].items():
            if k in merged["providers"]:
                merged["providers"][k].update(v)
            else:
                merged["providers"][k] = v
    for key in ("provider", "model", "memory", "tools", "platforms", "mcp_servers", "security", "auto_learn", "plugins", "routing"):
        if key in user:
            merged[key] = user[key]
    log_level = merged.get("log_level", "WARNING")
    logging.getLogger("nuntius").setLevel(getattr(logging, log_level.upper(), logging.WARNING))
    return _apply_env_overrides(merged)


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_active_provider(cfg: dict) -> dict:
    name = cfg.get("provider", "openai")
    return cfg.get("providers", {}).get(name, cfg["providers"]["openai"])
