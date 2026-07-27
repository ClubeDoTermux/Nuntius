from ..config import load_config
from ..platforms.drive import DriveClient
from .registry import BaseTool, register


_client = None


def _get_client():
    global _client
    if _client is None:
        cfg = load_config()
        creds = cfg.get("platforms", {}).get("drive", {}).get("credentials_path", "")
        if creds:
            _client = DriveClient(creds)
    return _client


class DriveListFiles(BaseTool):
    name = "drive_list_files"
    description = "Lista arquivos do Google Drive"
    parameters = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Max de arquivos"}
        },
    }

    async def execute(self, limit: int = 10) -> str:
        c = _get_client()
        if not c:
            return "Google Drive nao configurado."
        files = c.list_files(limit)
        return "\n".join(files) if files else "Nenhum arquivo encontrado."


register(DriveListFiles())
