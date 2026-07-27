import random
import string

from nuntius.tools.registry import BaseTool, register


class RandomNumber(BaseTool):
    name = "random_number"
    description = "Generate a random integer between min and max (inclusive)"
    parameters = {
        "type": "object",
        "properties": {
            "min": {"type": "integer", "description": "Minimum value", "default": 0},
            "max": {"type": "integer", "description": "Maximum value", "default": 100},
        },
        "required": [],
    }

    async def execute(self, min: int = 0, max: int = 100) -> str:
        return str(random.randint(min, max))


class RandomUUID(BaseTool):
    name = "random_uuid"
    description = "Generate a random UUID v4 string"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        import uuid
        return str(uuid.uuid4())


class RandomPassword(BaseTool):
    name = "random_password"
    description = "Generate a random password with given length"
    parameters = {
        "type": "object",
        "properties": {
            "length": {"type": "integer", "description": "Password length", "default": 16},
            "use_symbols": {"type": "boolean", "description": "Include symbols", "default": True},
        },
        "required": [],
    }

    async def execute(self, length: int = 16, use_symbols: bool = True) -> str:
        chars = string.ascii_letters + string.digits
        if use_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return "".join(random.choice(chars) for _ in range(length))


def setup(reg):
    register(RandomNumber())
    register(RandomUUID())
    register(RandomPassword())
