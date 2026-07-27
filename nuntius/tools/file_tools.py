import subprocess
from pathlib import Path

from ..config import load_config
from .registry import BaseTool, register


class ReadFile(BaseTool):
    name = "read"
    description = "Le o conteudo de um arquivo"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Caminho do arquivo"},
            "offset": {"type": "integer", "description": "Linha inicial (1-indexed)"},
            "limit": {"type": "integer", "description": "Maximo de linhas"},
        },
        "required": ["path"],
    }

    async def execute(self, path: str, offset: int = 0, limit: int = 200) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Arquivo nao encontrado: {path}"
        if not p.is_file():
            return f"Nao e um arquivo: {path}"
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if offset:
            lines = lines[offset - 1:]
        if limit and len(lines) > limit:
            lines = lines[:limit]
            lines.append(f"\n... [truncado, total {len(text.splitlines())} linhas]")
        return "\n".join(lines)


class WriteFile(BaseTool):
    name = "write"
    description = "Escreve conteudo em um arquivo (sobrescreve)"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Caminho do arquivo"},
            "content": {"type": "string", "description": "Conteudo a escrever"},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str, content: str) -> str:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Arquivo salvo: {path} ({len(content)} bytes)"


class EditFile(BaseTool):
    name = "edit"
    description = "Edita um arquivo trocando trechos de texto"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Caminho do arquivo"},
            "old_string": {"type": "string", "description": "Texto a ser substituido"},
            "new_string": {"type": "string", "description": "Texto novo"},
        },
        "required": ["path", "old_string", "new_string"],
    }

    async def execute(self, path: str, old_string: str, new_string: str) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Arquivo nao encontrado: {path}"
        text = p.read_text(encoding="utf-8", errors="replace")
        if old_string not in text:
            return "Texto antigo nao encontrado no arquivo."
        count = text.count(old_string)
        text = text.replace(old_string, new_string)
        p.write_text(text, encoding="utf-8")
        return f"Arquivo editado: {path} ({count} ocorrencia{'s' if count > 1 else ''})"


class Grep(BaseTool):
    name = "grep"
    description = "Procura texto em arquivos (regex)"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Padrao regex"},
            "path": {"type": "string", "description": "Diretorio para buscar"},
            "include": {"type": "string", "description": "Filtro de arquivo (ex: *.py)"},
        },
        "required": ["pattern"],
    }

    async def execute(self, pattern: str, path: str = ".", include: str = "") -> str:
        import re
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            return f"Diretorio nao encontrado: {path}"
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Erro na regex: {e}"
        results = []
        try:
            for f in root.rglob("*"):
                if f.is_file():
                    if include:
                        import fnmatch
                        if not fnmatch.fnmatch(f.name, include):
                            continue
                    try:
                        text = f.read_text(encoding="utf-8", errors="replace")
                        for i, line in enumerate(text.splitlines(), 1):
                            if regex.search(line):
                                rel = str(f.relative_to(root))
                                results.append(f"{rel}:{i}:{line[:200]}")
                                if len(results) >= 100:
                                    break
                    except Exception:
                        pass
                if len(results) >= 100:
                    break
        except Exception as e:
            return f"Erro: {e}"
        if not results:
            return "Nenhum resultado."
        out = "\n".join(results)
        if len(out) > 3000:
            out = out[:3000] + "\n... (truncado)"
        return out


class Glob(BaseTool):
    name = "glob"
    description = "Busca arquivos por padrao (ex: **/*.py)"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Padrao glob (ex: **/*.py)"},
            "path": {"type": "string", "description": "Diretorio base"},
        },
        "required": ["pattern"],
    }

    async def execute(self, pattern: str, path: str = ".") -> str:
        root = Path(path).expanduser().resolve()
        matches = [str(p.relative_to(root)) for p in root.rglob(pattern) if p.is_file()]
        if not matches:
            return "Nenhum arquivo encontrado."
        limited = matches[:50]
        text = "\n".join(limited)
        if len(matches) > 50:
            text += f"\n... (+{len(matches) - 50} arquivos)"
        return text


class Bash(BaseTool):
    name = "bash"
    description = "Executa comando no terminal"
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Comando a executar"},
            "workdir": {"type": "string", "description": "Diretorio de trabalho"},
            "timeout": {"type": "integer", "description": "Timeout em segundos"},
        },
        "required": ["command"],
    }

    async def execute(self, command: str, workdir: str = "", timeout: int = 60) -> str:
        cfg = load_config()
        if cfg.get("security", {}).get("bash_approval", True):
            return "Execute bash approvals com /bash ou desative em config."

        cwd = workdir or "."
        try:
            result = subprocess.run(
                command, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=timeout,
            )
            out = result.stdout or result.stderr
            return out[:3000] if out else "Comando executado (sem saida)."
        except subprocess.TimeoutExpired:
            return "Comando excedeu o tempo limite."
        except Exception as e:
            return f"Erro: {e}"


class Ls(BaseTool):
    name = "ls"
    description = "Lista arquivos em um diretorio"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Caminho do diretorio"},
        },
    }

    async def execute(self, path: str = ".") -> str:
        p = Path(path).expanduser().resolve()
        if not p.is_dir():
            return f"Diretorio nao encontrado: {path}"
        items = []
        for entry in sorted(p.iterdir()):
            suffix = "/" if entry.is_dir() else ""
            items.append(f"{entry.name}{suffix}")
        return "\n".join(items)


class DirTree(BaseTool):
    name = "tree"
    description = "Mostra a arvore de diretorios"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Diretorio raiz"},
            "depth": {"type": "integer", "description": "Profundidade maxima"},
        },
    }

    async def execute(self, path: str = ".", depth: int = 2) -> str:
        root = Path(path).expanduser().resolve()
        result = []

        def walk(dirpath: Path, level: int):
            if level > depth:
                return
            try:
                entries = sorted(dirpath.iterdir())
            except PermissionError:
                return
            for entry in entries:
                indent = "  " * level
                suffix = "/" if entry.is_dir() else ""
                result.append(f"{indent}{entry.name}{suffix}")
                if entry.is_dir():
                    walk(entry, level + 1)

        walk(root, 0)
        return "\n".join(result[:200])


class DeleteFile(BaseTool):
    name = "delete"
    description = "Exclui permanentemente um arquivo ou diretorio"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Caminho do arquivo ou diretorio"},
            "recursive": {"type": "boolean", "description": "Se true, exclui diretorios recursivamente"},
        },
        "required": ["path"],
    }

    async def execute(self, path: str, recursive: bool = False) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Nao encontrado: {path}"
        if p.is_dir():
            if recursive:
                import shutil
                shutil.rmtree(p)
                return f"Diretorio excluido: {path}"
            return f"E um diretorio. Use recursive=true para excluir."
        p.unlink()
        return f"Arquivo excluido: {path}"


class MoveFile(BaseTool):
    name = "move"
    description = "Move ou renomeia um arquivo/diretorio"
    parameters = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Caminho de origem"},
            "dest": {"type": "string", "description": "Caminho de destino"},
        },
        "required": ["source", "dest"],
    }

    async def execute(self, source: str, dest: str) -> str:
        src = Path(source).expanduser().resolve()
        dst = Path(dest).expanduser().resolve()
        if not src.exists():
            return f"Origem nao encontrada: {source}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return f"Movido: {source} -> {dest}"


class CopyFile(BaseTool):
    name = "copy"
    description = "Copia um arquivo ou diretorio"
    parameters = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Caminho de origem"},
            "dest": {"type": "string", "description": "Caminho de destino"},
        },
        "required": ["source", "dest"],
    }

    async def execute(self, source: str, dest: str) -> str:
        import shutil
        src = Path(source).expanduser().resolve()
        dst = Path(dest).expanduser().resolve()
        if not src.exists():
            return f"Origem nao encontrada: {source}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return f"Copiado: {source} -> {dest}"


class Organize(BaseTool):
    name = "organize"
    description = "Organiza arquivos em um diretorio por tipo/extensao"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Diretorio a organizar"},
            "dry_run": {"type": "boolean", "description": "Se true, apenas mostra o que faria"},
        },
        "required": ["path"],
    }

    async def execute(self, path: str = ".", dry_run: bool = True) -> str:
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            return f"Diretorio nao encontrado: {path}"
        categories = {
            "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico"],
            "Documentos": [".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".xlsx", ".pptx"],
            "Codigo": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".php"],
            "Web": [".html", ".css", ".jsx", ".tsx", ".vue", ".json", ".xml", ".yaml", ".yml"],
            "Arquivos": [".zip", ".tar", ".gz", ".rar", ".7z"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".webm"],
            "Musica": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
        }
        moved = []
        for entry in root.iterdir():
            if entry.is_file():
                ext = entry.suffix.lower()
                for cat, exts in categories.items():
                    if ext in exts:
                        target = root / cat
                        if dry_run:
                            moved.append(f"[{cat}] {entry.name}")
                        else:
                            target.mkdir(exist_ok=True)
                            entry.rename(target / entry.name)
                            moved.append(f"[{cat}] {entry.name}")
                        break
                else:
                    other = root / "Outros"
                    if dry_run:
                        moved.append(f"[Outros] {entry.name}")
                    else:
                        other.mkdir(exist_ok=True)
                        entry.rename(other / entry.name)
                        moved.append(f"[Outros] {entry.name}")
        if dry_run:
            return "Simulacao de organizacao:\n" + "\n".join(moved[:50]) + "\n\nUse dry_run=false para executar."
        return "Organizado:\n" + "\n".join(moved[:50])


class Download(BaseTool):
    name = "download"
    description = "Baixa um arquivo da internet"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL do arquivo"},
            "output": {"type": "string", "description": "Caminho para salvar (opcional)"},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, output: str = "") -> str:
        import httpx
        if not output:
            output = Path(url).name or "download"
        dest = Path(output).expanduser().resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        return f"Baixado: {url} -> {dest} ({len(resp.content)} bytes)"


class SystemInfo(BaseTool):
    name = "system_info"
    description = "Mostra informacoes do dispositivo/sistema"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        import platform
        info = [
            f"Sistema: {platform.system()} {platform.release()}",
            f"Arquitetura: {platform.machine()}",
            f"Hostname: {platform.node()}",
            f"Python: {platform.python_version()}",
            f"Diretorio atual: {Path('.').resolve()}",
        ]
        try:
            import shutil
            total, used, free = shutil.disk_usage(Path.home())
            info.append(f"Disco: livre {free // (1024**3)}GB / total {total // (1024**3)}GB")
        except Exception:
            pass
        try:
            import psutil
            info.append(f"CPU: {psutil.cpu_percent()}%")
            info.append(f"RAM: {psutil.virtual_memory().percent}%")
        except ImportError:
            pass
        return "\n".join(info)


register(ReadFile())
register(WriteFile())
register(EditFile())
register(Grep())
register(Glob())
register(Ls())
register(DirTree())
register(DeleteFile())
register(MoveFile())
register(CopyFile())
register(Organize())
register(Download())
register(SystemInfo())
register(Bash())
