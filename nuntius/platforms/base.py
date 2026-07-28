from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IncomingMessage:
    text: str
    user_id: str
    user_name: str
    platform: str
    chat_id: str
    thread_id: str = ""
    raw: dict | None = None


@dataclass
class OutgoingMessage:
    text: str
    chat_id: str
    thread_id: str = ""
    raw: dict | None = None


@dataclass
class PlatformInfo:
    name: str
    description: str
    config_schema: dict[str, dict] = field(default_factory=dict)
    extra_help: str = ""


class PlatformBase(ABC):
    info: PlatformInfo

    def __init__(self, config: dict, agent: Any):
        self.config = config
        self.agent = agent
        self._running = False

    @abstractmethod
    async def start(self):
        ...

    async def stop(self):
        self._running = False

    async def send_message(self, message: OutgoingMessage) -> bool:
        return True

    def get_status(self) -> dict:
        return {"running": self._running}

    def validate_config(self) -> str | None:
        return None
