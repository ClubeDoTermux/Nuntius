import asyncio
from datetime import datetime


class Scheduler:
    def __init__(self):
        self.tasks = []

    def add(self, name: str, interval_sec: int, callback):
        self.tasks.append({
            "name": name,
            "interval": interval_sec,
            "callback": callback,
            "last_run": 0,
        })

    async def run(self):
        while True:
            now = datetime.now().timestamp()
            for task in self.tasks:
                if now - task["last_run"] >= task["interval"]:
                    try:
                        if asyncio.iscoroutinefunction(task["callback"]):
                            await task["callback"]()
                        else:
                            task["callback"]()
                    except Exception as e:
                        print(f"Erro no scheduler ({task['name']}): {e}")
                    task["last_run"] = now
            await asyncio.sleep(1)
