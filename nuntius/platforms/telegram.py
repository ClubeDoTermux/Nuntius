from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class TelegramBot(PlatformBase):
    info = PlatformInfo(
        name="telegram",
        description="Telegram bot usando python-telegram-bot",
        config_schema={
            "token": {"type": "string", "description": "Token do bot do Telegram (via @BotFather)", "required": True},
        },
        extra_help="Obtenha o token em @BotFather no Telegram.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)

    async def start(self):
        try:
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
        except ImportError:
            print("Telegram: instale 'python-telegram-bot' (pip install python-telegram-bot)")
            return

        token = self.config.get("token", "")
        if not token:
            print("Telegram: token nao configurado.")
            return

        app = Application.builder().token(token).build()

        async def handle(update: Update, _ctx):
            if not update.message or not update.message.text:
                return
            user_text = update.message.text
            msg = IncomingMessage(
                text=user_text,
                user_id=str(update.effective_user.id) if update.effective_user else "?",
                user_name=update.effective_user.full_name if update.effective_user else "?",
                platform="telegram",
                chat_id=str(update.effective_chat.id) if update.effective_chat else "?",
                thread_id=str(update.message.message_thread_id or ""),
            )
            try:
                result = await self.agent.chat(msg.text)
                chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            except Exception as e:
                await update.message.reply_text(f"Erro: {e}")

        async def start_cmd(update: Update, _ctx):
            await update.message.reply_text("Nuntius ativo! Envie sua mensagem.")

        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

        self._running = True
        print("Telegram bot rodando...")
        await app.run_polling(drop_pending_updates=True)

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            from telegram import Bot
            bot = Bot(token=self.config["token"])
            await bot.send_message(chat_id=message.chat_id, text=message.text)
            return True
        except Exception:
            return False


register(TelegramBot)
