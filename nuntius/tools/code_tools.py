import subprocess
import sys
import tempfile
from pathlib import Path

from .registry import BaseTool, register


class RunPython(BaseTool):
    name = "run_python"
    description = "Executa codigo Python e retorna o resultado"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Codigo Python para executar"},
        },
        "required": ["code"],
    }

    async def execute(self, code: str) -> str:
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                tmp = f.name

            result = subprocess.run(
                [sys.executable, tmp],
                capture_output=True, text=True, timeout=120,
            )
            Path(tmp).unlink(missing_ok=True)

            out = result.stdout.strip() or result.stderr.strip()
            return out[:5000] if out else "Executado sem saida."
        except subprocess.TimeoutExpired:
            return "Codigo excedeu 120s."
        except Exception as e:
            return f"Erro: {e}"


class RunShell(BaseTool):
    name = "run_shell"
    description = "Executa comando no shell"
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Comando shell para executar"},
            "workdir": {"type": "string", "description": "Diretorio de trabalho"},
        },
        "required": ["command"],
    }

    async def execute(self, command: str, workdir: str = "") -> str:
        cwd = workdir or "."
        try:
            result = subprocess.run(command, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=120)
            out = result.stdout.strip() or result.stderr.strip()
            return out[:5000] if out else "Comando executado (sem saida)."
        except subprocess.TimeoutExpired:
            return "Comando excedeu 120s."
        except Exception as e:
            return f"Erro: {e}"


class RunJavaScript(BaseTool):
    name = "run_javascript"
    description = "Executa codigo JavaScript (requer Node.js)"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Codigo JavaScript para executar"},
        },
        "required": ["code"],
    }

    async def execute(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            tmp = f.name
        try:
            result = subprocess.run(
                ["node", tmp],
                capture_output=True, text=True, timeout=120,
            )
            return (result.stdout or result.stderr)[:5000]
        except FileNotFoundError:
            return "Node.js nao encontrado. Instale com: pkg install nodejs (Termux) ou apt install nodejs"
        except subprocess.TimeoutExpired:
            return "Codigo excedeu 120s."
        except Exception as e:
            return f"Erro: {e}"
        finally:
            Path(tmp).unlink(missing_ok=True)


class RunGo(BaseTool):
    name = "run_go"
    description = "Executa codigo Go (requer go instalado)"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Codigo Go completo (package main com func main)"},
        },
        "required": ["code"],
    }

    async def execute(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".go", delete=False) as f:
            f.write(code)
            tmp = f.name
        try:
            r = subprocess.run(["go", "run", tmp], capture_output=True, text=True, timeout=120)
            out = r.stdout.strip() or r.stderr.strip()
            return out[:5000] if out else "Executado sem saida."
        except FileNotFoundError:
            return "Go nao encontrado. Instale com: pkg install golang (Termux) ou apt install golang"
        except subprocess.TimeoutExpired:
            return "Codigo excedeu 120s."
        except Exception as e:
            return f"Erro: {e}"
        finally:
            Path(tmp).unlink(missing_ok=True)


class RunRust(BaseTool):
    name = "run_rust"
    description = "Executa codigo Rust (requer rustc instalado)"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Codigo Rust completo (fn main)"},
        },
        "required": ["code"],
    }

    async def execute(self, code: str) -> str:
        import uuid
        tmp_dir = Path(tempfile.gettempdir()) / f"nuntius_rust_{uuid.uuid4().hex[:8]}"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        src = tmp_dir / "main.rs"
        src.write_text(code)
        binary = tmp_dir / "main"
        try:
            r = subprocess.run(["rustc", str(src), "-o", str(binary)], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                return r.stderr.strip()[:2000]
            r2 = subprocess.run([str(binary)], capture_output=True, text=True, timeout=60)
            out = r2.stdout.strip() or r2.stderr.strip()
            return out[:5000] if out else "Executado sem saida."
        except FileNotFoundError:
            return "Rust nao encontrado. Instale com: pkg install rust (Termux) ou https://rustup.rs"
        except subprocess.TimeoutExpired:
            return "Compilacao/execucao excedeu o tempo limite."
        except Exception as e:
            return f"Erro: {e}"
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)


class ShellAlias(RunShell):
    name = "shell"
    description = "Alias de run_shell - executa comando no shell"


# Register all code tools
register(RunPython())
register(RunShell())
register(ShellAlias())
try:
    register(RunJavaScript())
except Exception:
    pass
try:
    register(RunGo())
except Exception:
    pass
try:
    register(RunRust())
except Exception:
    pass
