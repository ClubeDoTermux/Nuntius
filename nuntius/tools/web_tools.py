import httpx

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
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Nuntius/1.0"})
                text = resp.text[:5000]
            return text
        except Exception as e:
            return f"Erro ao acessar URL: {e}"


register(WebSearch())
register(WebFetch())
