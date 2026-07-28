import asyncio
import logging
import signal

from ..config import load_config
from ..core.agent import Agent
from . import list_platforms, load_platform

logger = logging.getLogger("nuntius.gateway")


class Gateway:
    def __init__(self, agent: Agent = None):
        self.cfg = load_config()
        self.agent = agent or Agent()
        self.platforms: list = []
        self._tasks: list = []

    def discover_enabled(self) -> list[tuple[str, dict]]:
        p = self.cfg.get("platforms", {})
        result = []
        for name, pcfg in p.items():
            if isinstance(pcfg, dict) and pcfg.get("enabled", False):
                result.append((name, pcfg))
        return result

    async def run(self):
        enabled = self.discover_enabled()
        if not enabled:
            print("Nenhuma plataforma habilitada. Use 'nuntius platform enable <nome>'.")
            return

        if not list_platforms():
            print("Nenhum adaptador de plataforma registrado.")
            return

        for name, pcfg in enabled:
            platform = load_platform(name, pcfg, self.agent)
            if platform is None:
                print(f"  {name}: adaptador nao encontrado no registro.")
                continue
            self.platforms.append(platform)
            task = asyncio.create_task(platform.start())
            self._tasks.append(task)

        names = [type(p).__name__ for p in self.platforms]
        print(f"Gateway ativo: {', '.join(names)}")

        stop_event = asyncio.Event()

        def _shutdown():
            stop_event.set()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _shutdown)
            except (ValueError, RuntimeError, NotImplementedError):
                pass

        await stop_event.wait()
        print("\nDesligando gateway...")
        await self.stop_all()

    async def stop_all(self):
        for p in self.platforms:
            try:
                await p.stop()
            except Exception as e:
                logger.warning(f"Erro ao desligar {type(p).__name__}: {e}")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self.platforms.clear()
        self._tasks.clear()
