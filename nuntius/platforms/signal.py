from ..core.agent import Agent
from . import register
from .base import IncomingMessage, OutgoingMessage, PlatformBase, PlatformInfo


class SignalBot(PlatformBase):
    info = PlatformInfo(
        name="signal",
        description="Signal messenger via signal-cli (dbus/rest)",
        config_schema={
            "phone_number": {"type": "string", "description": "Numero do Signal no formato +5511999999999", "required": True},
            "signal_cli_path": {"type": "string", "description": "Caminho do binario signal-cli (default: signal-cli)", "required": False},
        },
        extra_help="Instale o signal-cli: https://github.com/AsamK/signal-cli. Registre o numero com 'signal-cli -u <numero> register'.",
    )

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config, agent)
        self.process = None

    async def start(self):
        import asyncio

        phone = self.config.get("phone_number", "")
        cli_path = self.config.get("signal_cli_path", "signal-cli")
        if not phone:
            print("Signal: phone_number obrigatorio.")
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                cli_path, "-u", phone, "daemon",
                "--json", "--no-auto-receive",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            print(f"Signal: signal-cli nao encontrado em '{cli_path}'. Instale de https://github.com/AsamK/signal-cli")
            return

        self.process = proc
        self._running = True
        print("Signal bot rodando...")

        async for line in proc.stdout:
            if not self._running:
                break
            line = line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                import json
                data = json.loads(line)
                if data.get("envelope", {}).get("dataMessage"):
                    msg_data = data["envelope"]["dataMessage"]
                    text = msg_data.get("message", "")
                    source = data["envelope"].get("source", phone)
                    if text and source != phone:
                        msg_obj = IncomingMessage(
                            text=text,
                            user_id=source,
                            user_name=f"signal:{source}",
                            platform="signal",
                            chat_id=source,
                        )
                        result = await self.agent.chat(msg_obj.text)
                        await self._send_signal(cli_path, phone, source, result)
            except json.JSONDecodeError:
                pass

    async def _send_signal(self, cli_path: str, sender: str, recipient: str, text: str):
        import asyncio
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            proc = await asyncio.create_subprocess_exec(
                cli_path, "-u", sender, "send", "-m", chunk, recipient,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()

    async def stop(self):
        self._running = False
        if self.process and self.process.returncode is None:
            self.process.terminate()
            import asyncio
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()

    async def send_message(self, message: OutgoingMessage) -> bool:
        try:
            phone = self.config.get("phone_number", "")
            cli_path = self.config.get("signal_cli_path", "signal-cli")
            await self._send_signal(cli_path, phone, message.chat_id, message.text)
            return True
        except Exception:
            return False


register(SignalBot)
