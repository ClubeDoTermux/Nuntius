import asyncio
import json

from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class WebhookBot(PlatformBase):
    info = PlatformInfo(
        name="webhook",
        description="Webhook HTTP generico para integracoes customizadas",
        config_schema={
            "port": {"type": "integer", "description": "Porta do servidor HTTP (default: 8088)", "required": False},
            "path": {"type": "string", "description": "Caminho do webhook (default: /webhook)", "required": False},
            "secret": {"type": "string", "description": "Token de seguranca opcional (header X-Nuntius-Secret)", "required": False},
        },
        extra_help="Envie POST requests para http://host:port/path com JSON {text: ..., user_id: ..., user_name: ...}",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        try:
            from aiohttp import web
        except ImportError:
            print("Webhook: instale 'aiohttp' (pip install aiohttp)")
            return

        port = self.config.get("port", 8088)
        path = self.config.get("path", "/webhook")
        secret = self.config.get("secret", "")

        app = web.Application()

        async def handle(request):
            if secret:
                provided = request.headers.get("X-Nuntius-Secret", "")
                if provided != secret:
                    return web.Response(status=403, text="Forbidden")

            data = await request.json()
            text = data.get("text", "")
            if not text and data.get("message"):
                text = data["message"]

            if not text:
                return web.Response(status=400, text="text required")

            msg_obj = IncomingMessage(
                text=text,
                user_id=data.get("user_id", data.get("userId", "webhook")),
                user_name=data.get("user_name", data.get("userName", "Webhook User")),
                platform="webhook",
                chat_id=data.get("chat_id", data.get("channel", "default")),
                raw=data,
            )
            result = await self.agent.chat(msg_obj.text)
            return web.Response(
                text=json.dumps({"response": result}),
                content_type="application/json",
            )

        app.router.add_post(path, handle)
        app.router.add_get(path + "/health", lambda r: web.Response(text="OK"))

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        self._running = True
        print(f"Webhook rodando em http://0.0.0.0:{port}{path}")

        while self._running:
            await asyncio.sleep(1)

    async def send_message(self, message: OutgoingMessage) -> bool:
        return True


register(WebhookBot)
