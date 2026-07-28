import asyncio

from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class TeamsBot(PlatformBase):
    info = PlatformInfo(
        name="teams",
        description="Microsoft Teams via webhook (incoming/outgoing)",
        config_schema={
            "webhook_url": {"type": "string", "description": "URL do Incoming Webhook do Teams", "required": True},
        },
        extra_help="Crie um webhook em: Configuracoes do Canal > Conectores > Incoming Webhook.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        import httpx

        webhook_url = self.config.get("webhook_url", "")
        if not webhook_url:
            print("Teams: webhook_url nao configurada.")
            return

        self._running = True
        print("Teams bot rodando via webhook...")

        try:
            from aiohttp import web
        except ImportError:
            print("Teams: instale 'aiohttp' (pip install aiohttp) para receber mensagens.")
            return

        app = web.Application()

        async def handle(request):
            data = await request.json()
            text = data.get("text", "")
            from_id = data.get("from", {}).get("id", "?")
            channel_id = data.get("channelData", {}).get("channel", {}).get("id", "?")

            msg_obj = IncomingMessage(
                text=text,
                user_id=from_id,
                user_name=data.get("from", {}).get("name", "?"),
                platform="teams",
                chat_id=channel_id or data.get("conversation", {}).get("id", "?"),
            )
            result = await self.agent.chat(msg_obj.text)
            async with httpx.AsyncClient() as client:
                for chunk in [result[i:i+4000] for i in range(0, len(result), 4000)]:
                    await client.post(webhook_url, json={"text": chunk})
            return web.Response(text="OK")

        app.router.add_post("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8081)
        await site.start()
        print("Teams webhook escutando em http://0.0.0.0:8081/")

        while self._running:
            await asyncio.sleep(1)

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            import httpx
            webhook_url = self.config.get("webhook_url", "")
            if not webhook_url:
                return False
            async with httpx.AsyncClient() as client:
                for chunk in [message.text[i:i+4000] for i in range(0, len(message.text), 4000)]:
                    await client.post(webhook_url, json={"text": chunk})
            return True
        except Exception:
            return False


register(TeamsBot)
