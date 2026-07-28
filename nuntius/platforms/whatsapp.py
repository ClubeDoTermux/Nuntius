from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class WhatsAppBot(PlatformBase):
    info = PlatformInfo(
        name="whatsapp",
        description="WhatsApp via WhatsApp Cloud API (Meta)",
        config_schema={
            "phone_number_id": {"type": "string", "description": "ID do numero de telefone no Meta Business", "required": True},
            "token": {"type": "string", "description": "Token de acesso permanente do Meta", "required": True},
            "verify_token": {"type": "string", "description": "Token de verificacao do webhook", "required": False},
        },
        extra_help="Configure em https://developers.facebook.com/docs/whatsapp/cloud-api",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)
        self._webhook_server = None

    async def start(self):
        phone_id = self.config.get("phone_number_id", "")
        token = self.config.get("token", "")
        if not phone_id or not token:
            print("WhatsApp: phone_number_id e token sao obrigatorios.")
            return

        try:
            from aiohttp import web
        except ImportError:
            print("WhatsApp: instale 'aiohttp' (pip install aiohttp)")
            return

        verify_token = self.config.get("verify_token", "nuntius_verify")

        async def webhook(request):
            if request.method == "GET":
                hub_mode = request.query.get("hub.mode")
                hub_token = request.query.get("hub.verify_token")
                hub_challenge = request.query.get("hub.challenge")
                if hub_mode == "subscribe" and hub_token == verify_token:
                    return web.Response(text=hub_challenge)
                return web.Response(status=403)

            data = await request.json()
            if data.get("object") == "whatsapp_business_account":
                for entry in data.get("entry", []):
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        for msg in value.get("messages", []):
                            if msg.get("type") == "text":
                                from_num = msg.get("from", "?")
                                text = msg.get("text", {}).get("body", "")
                                msg_obj = IncomingMessage(
                                    text=text,
                                    user_id=from_num,
                                    user_name=f"whatsapp:{from_num}",
                                    platform="whatsapp",
                                    chat_id=from_num,
                                )
                                result = await self.agent.chat(msg_obj.text)
                                await self._send_whatsapp(phone_id, token, from_num, result)
            return web.Response(text="OK")

        app = web.Application()
        app.router.add_route("*", "/webhook", webhook)
        runner = web.AppRunner(app)
        await runner.setup()
        self._webhook_server = runner
        self._running = True
        print("WhatsApp webhook rodando em http://0.0.0.0:8080/webhook")
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()

        while self._running:
            import asyncio
            await asyncio.sleep(1)

    async def _send_whatsapp(self, phone_id: str, token: str, to: str, text: str):
        import httpx
        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"preview_url": False, "body": chunk},
            }
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, headers=headers)

    async def stop(self):
        self._running = False
        if self._webhook_server:
            await self._webhook_server.cleanup()

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            phone_id = self.config.get("phone_number_id", "")
            token = self.config.get("token", "")
            await self._send_whatsapp(phone_id, token, message.chat_id, message.text)
            return True
        except Exception:
            return False


register(WhatsAppBot)
