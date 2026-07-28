from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class LINEBot(PlatformBase):
    info = PlatformInfo(
        name="line",
        description="LINE Messenger via LINE Messaging API",
        config_schema={
            "channel_access_token": {"type": "string", "description": "Channel Access Token do LINE", "required": True},
            "channel_secret": {"type": "string", "description": "Channel Secret do LINE", "required": True},
        },
        extra_help="Crie um canal em https://developers.line.biz/console/.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        import asyncio

        token = self.config.get("channel_access_token", "")
        secret = self.config.get("channel_secret", "")
        if not token or not secret:
            print("LINE: channel_access_token e channel_secret obrigatorios.")
            return

        try:
            from aiohttp import web
        except ImportError:
            print("LINE: instale 'aiohttp' (pip install aiohttp)")
            return

        app = web.Application()

        async def callback(request):
            data = await request.json()
            events = data.get("events", [])
            for event in events:
                if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                    reply_token = event.get("replyToken", "")
                    text = event["message"]["text"]
                    user_id = event.get("source", {}).get("userId", "?")
                    group_id = event.get("source", {}).get("groupId") or event.get("source", {}).get("roomId") or user_id

                    msg_obj = IncomingMessage(
                        text=text,
                        user_id=user_id,
                        user_name=f"line:{user_id}",
                        platform="line",
                        chat_id=group_id,
                    )
                    result = await self.agent.chat(msg_obj.text)
                    await self._reply_message(token, reply_token, result)
            return web.Response(text="OK")

        app.router.add_post("/callback", callback)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8083)
        await site.start()

        self._running = True
        print("LINE bot rodando, webhook em http://0.0.0.0:8083/callback")

        while self._running:
            await asyncio.sleep(1)

    async def _reply_message(self, token: str, reply_token: str, text: str):
        import httpx
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        messages = [{"type": "text", "text": chunk} for chunk in chunks]
        payload = {"replyToken": reply_token, "messages": messages}
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=headers)

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            import httpx
            token = self.config.get("channel_access_token", "")
            url = "https://api.line.me/v2/bot/message/push"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            chunks = [message.text[i:i+4000] for i in range(0, len(message.text), 4000)]
            messages = [{"type": "text", "text": chunk} for chunk in chunks]
            payload = {"to": message.chat_id, "messages": messages}
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, headers=headers)
            return True
        except Exception:
            return False


register(LINEBot)
