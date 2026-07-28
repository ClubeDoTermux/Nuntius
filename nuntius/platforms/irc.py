import asyncio

from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class IRCBot(PlatformBase):
    info = PlatformInfo(
        name="irc",
        description="Internet Relay Chat (IRC)",
        config_schema={
            "server": {"type": "string", "description": "Servidor IRC (ex: irc.libera.chat)", "required": True},
            "port": {"type": "integer", "description": "Porta (default: 6697)", "required": False},
            "nickname": {"type": "string", "description": "Nickname do bot", "required": True},
            "channels": {"type": "array", "description": "Lista de canais para entrar (ex: ['#nuntius', '#bot'])", "required": True},
            "password": {"type": "string", "description": "Senha do NickServ (opcional)", "required": False},
            "use_tls": {"type": "boolean", "description": "Usar TLS/SSL (default: true)", "required": False},
        },
        extra_help="Use um servidor IRC publico como Libera.Chat ou OFTC.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)
        self.reader = None
        self.writer = None

    async def start(self):
        try:
            import irctokens
        except ImportError:
            print("IRC: instale 'irctokens' (pip install irctokens)")
            return

        server = self.config.get("server", "")
        port = self.config.get("port", 6697)
        nickname = self.config.get("nickname", "NuntiusBot")
        channels = self.config.get("channels", [])
        password = self.config.get("password", "")
        use_tls = self.config.get("use_tls", True)

        if not server or not channels:
            print("IRC: server e channels sao obrigatorios.")
            return

        self._running = True
        print(f"IRC bot conectando a {server}:{port} como {nickname}...")

        while self._running:
            try:
                import ssl
                reader, writer = await asyncio.open_connection(
                    server, port,
                    ssl=ssl.create_default_context() if use_tls else None,
                )
                self.reader = reader
                self.writer = writer

                writer.write(f"NICK {nickname}\r\n".encode())
                writer.write(f"USER {nickname} 0 * :Nuntius AI Bot\r\n".encode())
                if password:
                    writer.write(f"PRIVMSG NickServ :IDENTIFY {password}\r\n".encode())
                await writer.drain()

                while self._running:
                    try:
                        line = await asyncio.wait_for(reader.readline(), timeout=300)
                    except asyncio.TimeoutError:
                        writer.write(f"PING :keepalive\r\n".encode())
                        await writer.drain()
                        continue

                    if not line:
                        break

                    decoded = line.decode("utf-8", errors="replace").strip()
                    tokens = irctokens.tokenise(decoded)

                    if tokens.command == "001":
                        for ch in channels:
                            writer.write(f"JOIN {ch}\r\n".encode())
                        await writer.drain()
                        print(f"IRC conectado a {len(channels)} canais")

                    elif tokens.command == "PING":
                        writer.write(f"PONG {tokens.params[-1]}\r\n".encode())
                        await writer.drain()

                    elif tokens.command == "PRIVMSG":
                        sender = tokens.hostmask or "?"
                        target = tokens.params[0]
                        text = tokens.params[-1]
                        channel = target if target.startswith("#") else sender

                        if text.startswith(f"{nickname}:"):
                            text = text[len(nickname)+1:].strip()
                        elif not target.startswith("#"):
                            pass
                        else:
                            continue

                        if not text:
                            continue

                        msg_obj = IncomingMessage(
                            text=text,
                            user_id=sender,
                            user_name=sender.split("!")[0] if "!" in sender else sender,
                            platform="irc",
                            chat_id=channel,
                        )
                        result = await self.agent.chat(msg_obj.text)
                        for chunk in [result[i:i+400] for i in range(0, len(result), 400)]:
                            writer.write(f"PRIVMSG {channel} :{chunk}\r\n".encode())
                        await writer.drain()

            except Exception as e:
                if self._running:
                    print(f"IRC desconectado ({e}), reconectando em 10s...")
                    await asyncio.sleep(10)
            finally:
                if self.writer:
                    try:
                        self.writer.close()
                    except Exception:
                        pass

    async def stop(self):
        self._running = False
        if self.writer:
            try:
                self.writer.write(b"QUIT :Nuntius desligando\r\n")
                await self.writer.drain()
                self.writer.close()
            except Exception:
                pass

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            if self.writer and not self.writer.is_closing():
                for chunk in [message.text[i:i+400] for i in range(0, len(message.text), 400)]:
                    self.writer.write(f"PRIVMSG {message.chat_id} :{chunk}\r\n".encode())
                await self.writer.drain()
                return True
            return False
        except Exception:
            return False


register(IRCBot)
