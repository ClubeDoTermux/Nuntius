import asyncio
from typing import Optional

from ..config import load_config
from ..core.agent import Agent


class Gateway:
    def __init__(self, agent: Optional[Agent] = None):
        self.cfg = load_config()
        self.agent = agent or Agent()
        self.platforms: list = []

    def init_platforms(self):
        p = self.cfg.get("platforms", {})

        if p.get("telegram", {}).get("enabled", False):
            token = p["telegram"].get("token", "")
            if token:
                try:
                    from .telegram import TelegramBot
                    self.platforms.append(TelegramBot(token, self.agent))
                except ImportError:
                    print("Telegram: instale 'python-telegram-bot'")

        if p.get("discord", {}).get("enabled", False):
            token = p["discord"].get("token", "")
            if token:
                try:
                    from .discord import DiscordBot
                    self.platforms.append(DiscordBot(token, self.agent))
                except ImportError:
                    print("Discord: instale 'discord.py'")

    async def run(self):
        self.init_platforms()
        if not self.platforms:
            print("Nenhuma plataforma configurada. Use 'nuntius platform enable <nome>'.")
            return

        tasks = [p.start() for p in self.platforms]
        names = [type(p).__name__ for p in self.platforms]
        print(f"Gateway ativo: {', '.join(names)}")
        await asyncio.gather(*tasks)
