import datetime

from .registry import BaseTool, register


class Calculator(BaseTool):
    name = "calculator"
    description = "Executa operacoes matematicas simples"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Expressao matematica (ex: 2 + 2 * 3)",
            }
        },
        "required": ["expression"],
    }

    async def execute(self, expression: str) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"Erro: {e}"


class CurrentTime(BaseTool):
    name = "current_time"
    description = "Retorna a data e hora atuais"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")


register(Calculator())
register(CurrentTime())
