from datetime import datetime

from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static


class ChatMessage(Static):
    def __init__(self, role: str, content: str, timestamp: float | None = None):
        super().__init__("")
        self.role = role
        self.content = content
        self.ts = timestamp or datetime.now().timestamp()
        self._update_renderable()

    def _update_renderable(self):
        time_str = datetime.fromtimestamp(self.ts).strftime("%H:%M:%S")
        if self.role == "user":
            self.update(
                Panel(
                    Markdown(self.content),
                    title=f"[bold]{'Voce'}[/bold]  [{time_str}]",
                    title_align="left",
                    border_style="secondary",
                    padding=(1, 2),
                )
            )
        elif self.role == "assistant":
            self.update(
                Panel(
                    Markdown(self.content),
                    title=f"[bold]{'Nuntius'}[/bold]  [{time_str}]",
                    title_align="left",
                    border_style="primary",
                    padding=(1, 2),
                )
            )
        elif self.role == "tool":
            name, result = self.content.split("|", 1) if "|" in self.content else ("tool", self.content)
            self.update(
                Panel(
                    Syntax(
                        result[:500],
                        "python" if result.startswith("{") or result.startswith("[") else "bash",
                        word_wrap=True,
                        theme="monokai",
                    ),
                    title=f"[bold]{name}[/bold]  [{time_str}]",
                    title_align="left",
                    border_style="warning",
                    padding=(0, 1),
                    height=max(3, min(12, result.count("\n") + 3)),
                )
            )
        else:
            self.update(
                Panel(
                    Text(self.content[:200]),
                    title=f"[bold]{self.role}[/bold]  [{time_str}]",
                    title_align="left",
                    border_style="text-dim",
                    padding=(0, 1),
                )
            )
