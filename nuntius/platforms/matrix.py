from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class MatrixBot(PlatformBase):
    info = PlatformInfo(
        name="matrix",
        description="Matrix bot usando matrix-nio",
        config_schema={
            "homeserver": {"type": "string", "description": "URL do homeserver (ex: https://matrix.org)", "required": True},
            "user_id": {"type": "string", "description": "ID do usuario do bot (@user:server)", "required": True},
            "password": {"type": "string", "description": "Senha ou access token do bot", "required": True},
        },
        extra_help="Crie uma conta Matrix para o bot em qualquer homeserver.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)
        self.client = None

    async def start(self):
        try:
            from nio import AsyncClient, RoomMessageText
        except ImportError:
            print("Matrix: instale 'matrix-nio' (pip install matrix-nio)")
            return

        hs = self.config.get("homeserver", "")
        user_id = self.config.get("user_id", "")
        password = self.config.get("password", "")
        if not hs or not user_id or not password:
            print("Matrix: homeserver, user_id e password sao obrigatorios.")
            return

        client = AsyncClient(hs, user_id)
        self.client = client
        await client.login(password)

        async def message_cb(room, event):
            if event.sender == client.user:
                return
            text = event.body
            msg = IncomingMessage(
                text=text,
                user_id=event.sender,
                user_name=event.sender,
                platform="matrix",
                chat_id=room.room_id,
            )
            result = await self.agent.chat(msg_obj.text)
            chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for chunk in chunks:
                await client.room_send(
                    room_id=room.room_id,
                    message_type="m.room.message",
                    content={"msgtype": "m.text", "body": chunk},
                )

        client.add_event_callback(message_cb, RoomMessageText)

        self._running = True
        print("Matrix bot rodando...")
        await client.sync_forever(timeout=30000)

    async def stop(self):
        self._running = False
        if self.client:
            await self.client.close()

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            if self.client:
                await self.client.room_send(
                    room_id=message.chat_id,
                    message_type="m.room.message",
                    content={"msgtype": "m.text", "body": message.text},
                )
                return True
            return False
        except Exception:
            return False


register(MatrixBot)
