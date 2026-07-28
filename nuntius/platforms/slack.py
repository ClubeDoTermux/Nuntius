from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class SlackBot(PlatformBase):
    info = PlatformInfo(
        name="slack",
        description="Slack bot usando Slack SDK",
        config_schema={
            "token": {"type": "string", "description": "Bot User OAuth Token (xoxb-*)", "required": True},
            "signing_secret": {"type": "string", "description": "Signing Secret do app Slack", "required": False},
        },
        extra_help="Crie um app em https://api.slack.com/apps",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        try:
            from slack_bolt.adapter.socket_mode import SocketModeHandler
            from slack_bolt import App
        except ImportError:
            print("Slack: instale 'slack-bolt' (pip install slack-bolt)")
            return

        token = self.config.get("token", "")
        if not token:
            print("Slack: token nao configurado.")
            return

        app = App(token=token)

        @app.event("message")
        def handle_message(event, say):
            text = event.get("text", "")
            if not text:
                return
            if event.get("bot_id"):
                return
            user_id = event.get("user", "?")
            channel = event.get("channel", "?")
            msg = IncomingMessage(
                text=text,
                user_id=user_id,
                user_name=f"slack:{user_id}",
                platform="slack",
                chat_id=channel,
                thread_id=event.get("thread_ts", ""),
            )
            result = self.agent.chat(msg.text)
            import asyncio
            result = asyncio.run(result)
            chunks = [result[i:i+3800] for i in range(0, len(result), 3800)]
            for chunk in chunks:
                say(text=chunk, thread_ts=event.get("ts"))

        app_signing_secret = self.config.get("signing_secret", "")
        if app_signing_secret:
            from slack_bolt.adapter.socket_mode import SocketModeHandler
            self._running = True
            print("Slack bot rodando (Socket Mode)...")
            handler = SocketModeHandler(app, app_signing_secret)
            handler.start()
        else:
            self._running = True
            print("Slack bot rodando (RTM, aguardando eventos)...")
            import time
            while self._running:
                time.sleep(1)

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            from slack_sdk import WebClient
            client = WebClient(token=self.config["token"])
            client.chat_postMessage(channel=message.chat_id, text=message.text)
            return True
        except Exception:
            return False


register(SlackBot)
