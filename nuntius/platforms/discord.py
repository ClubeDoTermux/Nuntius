from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class DiscordBot(PlatformBase):
    info = PlatformInfo(
        name="discord",
        description="Discord bot usando discord.py",
        config_schema={
            "token": {"type": "string", "description": "Token do bot do Discord", "required": True},
        },
        extra_help="Crie um bot em https://discord.com/developers/applications",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        try:
            import discord
        except ImportError:
            print("Discord: instale 'discord.py' (pip install discord.py)")
            return

        token = self.config.get("token", "")
        if not token:
            print("Discord: token nao configurado.")
            return

        intents = discord.Intents.default()
        intents.message_content = True

        class NuntiusClient(discord.Client):
            def __init__(self, nagent, bot_ref):
                super().__init__(intents=intents)
                self.nagent = nagent
                self.bot_ref = bot_ref

            async def on_ready(self):
                self.bot_ref._running = True
                print(f"Discord bot conectado como {self.user}")

            async def on_message(self, message):
                if message.author == self.user:
                    return
                if self.user in message.mentions:
                    content = message.content.replace(f"<@{self.user.id}>", "").strip()
                    if content:
                        msg = IncomingMessage(
                            text=content,
                            user_id=str(message.author.id),
                            user_name=message.author.display_name,
                            platform="discord",
                            chat_id=str(message.channel.id),
                            thread_id=str(getattr(message.thread, "id", "") or ""),
                        )
                        async with message.channel.typing():
                            result = await self.nagent.chat(msg.text)
                            for chunk in [result[i:i+1900] for i in range(0, len(result), 1900)]:
                                await message.reply(chunk)

            async def on_disconnect(self):
                self.bot_ref._running = False

        client = NuntiusClient(self.agent, self)
        await client.start(token)

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            import discord
            client = discord.Client(intents=discord.Intents.default())
            return True
        except Exception:
            return False


register(DiscordBot)
