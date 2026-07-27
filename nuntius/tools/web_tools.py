import httpx

from ..config import load_config
from .registry import BaseTool, register


class WebSearch(BaseTool):
    name = "web_search"
    description = "Pesquisa na web e retorna resultados"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Termo de pesquisa"},
        },
        "required": ["query"],
    }

    async def execute(self, query: str) -> str:
        try:
            import urllib.parse
            encoded = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers={"User-Agent": "Nuntius/1.0"})
                data = resp.json()
            answer = data.get("AbstractText", "")
            results = data.get("Results", [])
            if answer:
                return answer
            if results:
                return "\n".join(r.get("Text", "") for r in results[:5])
            return f"Sem resultados para: {query}"
        except Exception as e:
            return f"Erro na busca: {e}"


class WebFetch(BaseTool):
    name = "web_fetch"
    description = "Obtem o conteudo de uma URL"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL completa"},
        },
        "required": ["url"],
    }

    async def execute(self, url: str) -> str:
        cfg = load_config()
        if cfg.get("security", {}).get("block_internal_networks", True):
            from urllib.parse import urlparse
            import socket
            hostname = urlparse(url).hostname
            if hostname:
                host_lower = hostname.lower()
                if host_lower in ("localhost", "127.0.0.1", "0.0.0.0"):
                    return "Acesso negado: URLs de rede interna nao sao permitidas por seguranca."
                try:
                    addrs = socket.getaddrinfo(host_lower, None)
                    for family, type_, proto, canonname, sockaddr in addrs:
                        ip = sockaddr[0]
                        if ip.startswith("10.") or ip.startswith("169.254."):
                            return "Acesso negado: URLs de rede interna nao sao permitidas por seguranca."
                        if ip.startswith("172."):
                            parts = ip.split(".")
                            if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                                return "Acesso negado: URLs de rede interna nao sao permitidas por seguranca."
                        if ip.startswith("192.168."):
                            return "Acesso negado: URLs de rede interna nao sao permitidas por seguranca."
                except Exception:
                    pass
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Nuntius/1.0"})
                text = resp.text[:5000]
            return text
        except Exception as e:
            return f"Erro ao acessar URL: {e}"


register(WebSearch())
register(WebFetch())
