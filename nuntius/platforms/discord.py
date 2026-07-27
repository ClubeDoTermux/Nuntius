import asyncio

from ..core.agent import Agent


class DiscordBot:
    def __init__(self, token: str, agent: Agent):
        self.token = token
        self.agent = agent

    async def start(self):
        try:
            import discord
        except ImportError:
            print("Discord: instale 'discord.py' (pip install discord.py)")
            return

        intents = discord.Intents.default()
        intents.message_content = True

        class NuntiusClient(discord.Client):
            def __init__(self, nagent):
                super().__init__(intents=intents)
                self.nagent = nagent

            async def on_ready(self):
                print(f"Discord bot conectado como {self.user}")

            async def on_message(self, message):
                if message.author == self.user:
                    return
                if self.user in message.mentions:
                    content = message.content.replace(f"<@{self.user.id}>", "").strip()
                    if content:
                        async with message.channel.typing():
                            result = await self.nagent.chat(content)
                            for chunk in [result[i:i+1900] for i in range(0, len(result), 1900)]:
                                await message.reply(chunk)

        client = NuntiusClient(self.agent)
        await client.start(self.token)
