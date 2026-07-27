import asyncio

from ..core.agent import Agent


class TelegramBot:
    def __init__(self, token: str, agent: Agent):
        self.token = token
        self.agent = agent
        self._running = False

    async def start(self):
        try:
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
        except ImportError:
            print("Telegram: instale 'python-telegram-bot' (pip install python-telegram-bot)")
            return

        app = Application.builder().token(self.token).build()

        async def handle(update: Update, _ctx):
            if not update.message or not update.message.text:
                return
            user_text = update.message.text
            try:
                result = await self.agent.chat(user_text)
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

    async def stop(self):
        self._running = False
