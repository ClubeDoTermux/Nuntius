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
            import ast
            tree = ast.parse(code)
            has_blockers = any(
                n.func.attr in ("system", "popen", "exec", "eval")
                for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            )
            if has_blockers:
                return "Codigo com chamadas de sistema nao permitidas."

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                tmp = f.name

            result = subprocess.run(
                [sys.executable, tmp],
                capture_output=True, text=True, timeout=30,
            )
            Path(tmp).unlink(missing_ok=True)

            out = result.stdout.strip() or result.stderr.strip()
            return out[:3000] if out else "Executado sem saida."
        except subprocess.TimeoutExpired:
            return "Codigo excedeu 30s."
        except Exception as e:
            return f"Erro: {e}"


class RunShell(BaseTool):
    name = "run_shell"
    description = "Executa comando no shell (requer confirmacao)"
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Comando"},
            "workdir": {"type": "string", "description": "Diretorio"},
        },
        "required": ["command"],
    }

    async def execute(self, command: str, workdir: str = "") -> str:
        from ..config import load_config
        cfg = load_config()
        if cfg.get("security", {}).get("bash_approval", True):
            return "Aprovacao necessaria. Use /bash no terminal."
        cwd = workdir or "."
        try:
            result = subprocess.run(command, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=60)
            return (result.stdout or result.stderr)[:3000]
        except subprocess.TimeoutExpired:
            return "Comando excedeu 60s."
        except Exception as e:
            return f"Erro: {e}"


class RunJavaScript(BaseTool):
    name = "run_javascript"
    description = "Executa codigo JavaScript (requer node)"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Codigo JavaScript"},
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
                capture_output=True, text=True, timeout=30,
            )
            return (result.stdout or result.stderr)[:3000]
        except FileNotFoundError:
            return "Node.js nao encontrado."
        except subprocess.TimeoutExpired:
            return "Codigo excedeu 30s."
        except Exception as e:
            return f"Erro: {e}"
        finally:
            Path(tmp).unlink(missing_ok=True)


register(RunPython())


class ShellAlias(RunShell):
    name = "shell"
    description = "Alias de run_shell - executa comando no terminal"


register(RunShell())
register(ShellAlias())
try:
    register(RunJavaScript())
except Exception:
    pass
