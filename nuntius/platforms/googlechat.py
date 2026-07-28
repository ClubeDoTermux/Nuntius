from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class GoogleChatBot(PlatformBase):
    info = PlatformInfo(
        name="googlechat",
        description="Google Chat via webhook (incoming)",
        config_schema={
            "webhook_url": {"type": "string", "description": "URL do webhook do Google Chat", "required": True},
        },
        extra_help="Crie um webhook em: Espaco > Gerenciar webhooks.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        import asyncio

        webhook_url = self.config.get("webhook_url", "")
        if not webhook_url:
            print("Google Chat: webhook_url nao configurada.")
            return

        self._running = True
        print("Google Chat bot rodando via webhook...")

        try:
            from aiohttp import web
        except ImportError:
            print("Google Chat: instale 'aiohttp' (pip install aiohttp) para receber mensagens.")
            return

        app = web.Application()

        async def handle(request):
            data = await request.json()
            text = data.get("text", "").strip()
            space = data.get("space", {}).get("name", "?")
            user_name = data.get("user", {}).get("displayName", "?")
            user_id = data.get("user", {}).get("name", "?")

            if not text:
                return web.Response(text="OK")

            msg_obj = IncomingMessage(
                text=text,
                user_id=user_id,
                user_name=user_name,
                platform="googlechat",
                chat_id=space,
            )
            result = await self.agent.chat(msg_obj.text)
            import httpx
            async with httpx.AsyncClient() as client:
                for chunk in [result[i:i+4000] for i in range(0, len(result), 4000)]:
                    await client.post(webhook_url, json={"text": chunk})
            return web.Response(text="OK")

        app.router.add_post("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8082)
        await site.start()
        print("Google Chat webhook escutando em http://0.0.0.0:8082/")

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


register(GoogleChatBot)
