from ..config import load_config
from ..platforms.github_platform import GitHubClient
from .registry import BaseTool, register


_client = None


def _get_client():
    global _client
    if _client is None:
        cfg = load_config()
        token = cfg.get("platforms", {}).get("github", {}).get("token", "")
        if token:
            _client = GitHubClient(token)
    return _client


class GitHubListRepos(BaseTool):
    name = "github_list_repos"
    description = "Lista seus repositorios no GitHub"
    parameters = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Max de repositorios"}
        },
    }

    async def execute(self, limit: int = 10) -> str:
        c = _get_client()
        if not c:
            return "GitHub nao configurado. Configure o token em 'nuntius setup'."
        repos = c.list_repos(limit)
        return "\n".join(repos) if repos else "Nenhum repositorio encontrado."


class GitHubCreateIssue(BaseTool):
    name = "github_create_issue"
    description = "Cria uma issue no GitHub"
    parameters = {
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "repositorio (ex: usuario/repo)"},
            "title": {"type": "string", "description": "titulo da issue"},
            "body": {"type": "string", "description": "corpo da issue"},
        },
        "required": ["repo", "title"],
    }

    async def execute(self, repo: str, title: str, body: str = "") -> str:
        c = _get_client()
        if not c:
            return "GitHub nao configurado."
        url = c.create_issue(repo, title, body)
        return f"Issue criada: {url}"


class GitHubListIssues(BaseTool):
    name = "github_list_issues"
    description = "Lista issues de um repositorio GitHub"
    parameters = {
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "repositorio (ex: usuario/repo)"},
            "state": {"type": "string", "description": "open, closed, all"},
        },
        "required": ["repo"],
    }

    async def execute(self, repo: str, state: str = "open") -> str:
        c = _get_client()
        if not c:
            return "GitHub nao configurado."
        issues = c.list_issues(repo, state)
        return "\n".join(issues) if issues else "Nenhuma issue encontrada."


register(GitHubListRepos())
register(GitHubCreateIssue())
register(GitHubListIssues())
