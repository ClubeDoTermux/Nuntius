import asyncio
import logging
from pathlib import Path

from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.document._document import Document
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Select,
    Static,
)

from ..config import PROVIDER_INFO, load_config, save_config
from ..core.agent import Agent
from ..tools import registry
from ..version import VERSION, get_local_commit
from .theme import get_theme, get_theme_css, list_themes


class ThemePreviewScreen(ModalScreen):
    def compose(self):
        theme_name = self.app.current_theme_name
        t = get_theme(theme_name)
        yield Container(
            Static("Tema: " + t["name"], classes="preview-title"),
            Static("bg: " + t["background"], classes="preview-swatch", style=f"background: {t['background']}; color: {t['text_primary']}"),
            Static("primary: " + t["primary"], classes="preview-swatch", style=f"background: {t['primary']}"),
            Static("secondary: " + t["secondary"], classes="preview-swatch", style=f"background: {t['secondary']}"),
            Static("accent: " + t["accent"], classes="preview-swatch", style=f"background: {t['accent']}"),
            Static("surface: " + t["surface"], classes="preview-swatch", style=f"background: {t['surface']}; color: {t['text_primary']}"),
            Static("\n[ Exemplo de mensagem ]"),
            Panel(
                "Olá! Como posso ajudar?",
                border_style=t["primary"],
            ),
            Panel(
                "Quero criar um website.",
                border_style=t["secondary"],
            ),
            Button("Fechar preview", variant="primary", id="close-preview"),
            id="theme-preview",
        )

    def on_button_pressed(self, event):
        if event.button.id == "close-preview":
            self.dismiss()


class ThemeScreen(ModalScreen):
    def compose(self):
        with Vertical(id="theme-selector"):
            yield Static("[bold]Selecionar Tema[/bold]", classes="screen-title")
            yield Static("Escolha um tema e veja o preview ao vivo.", classes="screen-subtitle")
            yield ListView(*[ListItem(Static(name)) for name in list_themes()], id="theme-list")
            with Horizontal(classes="button-row"):
                yield Button("Preview", variant="default", id="preview-btn")
                yield Button("Aplicar", variant="primary", id="apply-btn")
                yield Button("Voltar", variant="default", id="back-btn")

    def on_mount(self):
        theme_list = self.query_one("#theme-list", ListView)
        current = list_themes().index(self.app.current_theme_name)
        theme_list.index = current

    def on_list_view_selected(self, event):
        theme_name = str(event.item.children[0].renderable)
        self.app.current_theme_name = theme_name
        self.app.apply_theme(theme_name)

    def on_button_pressed(self, event):
        if event.button.id == "preview-btn":
            self.app.push_screen(ThemePreviewScreen())
        elif event.button.id == "apply-btn":
            self.app.save_theme_preference()
            self.dismiss()
        elif event.button.id == "back-btn":
            self.dismiss()


class ProviderScreen(ModalScreen):
    def compose(self):
        cfg = load_config()
        current_provider = cfg.get("provider", "openai")
        current_model = cfg.get("model", "gpt-4o-mini")

        with Vertical(id="provider-screen"):
            yield Static("[bold]Configuracao do Provedor[/bold]", classes="screen-title")
            yield Static(f"Atual: {current_provider} - {current_model}", classes="screen-subtitle")

            yield Label("Provedor:")
            yield Select(
                [(k, f"{v['name']} ({k})") for k, v in PROVIDER_INFO.items()],
                value=current_provider,
                id="provider-select",
                prompt="Selecione um provedor",
            )
            yield Label("Modelo:")
            yield Input(id="model-input", placeholder="Ex: gpt-4o-mini", value=current_model)
            yield Label("API Key:")
            yield Input(id="api-key-input", placeholder="API Key", password=True)

            with Horizontal(classes="button-row"):
                yield Button("Salvar", variant="primary", id="save-provider")
                yield Button("Voltar", variant="default", id="back-provider")

    def on_button_pressed(self, event):
        if event.button.id == "save-provider":
            cfg = load_config()
            prov = self.query_one("#provider-select", Select).value
            model = self.query_one("#model-input", Input).value
            api_key = self.query_one("#api-key-input", Input).value
            if prov:
                cfg["provider"] = str(prov)
                if model:
                    cfg["model"] = model
                if api_key:
                    pcfg = cfg["providers"].get(str(prov), {})
                    pcfg["api_key"] = api_key
                    cfg["providers"][str(prov)] = pcfg
                save_config(cfg)
                self.app.current_provider = cfg.get("provider", "?")
                self.app.current_model = cfg.get("model", "?")
                self.app.update_header()
                self.dismiss()
        elif event.button.id == "back-provider":
            self.dismiss()


class ToolsScreen(ModalScreen):
    def compose(self):
        tools = registry.get_all()
        with Vertical(id="tools-screen"):
            yield Static(f"[bold]Ferramentas ({len(tools)})[/bold]", classes="screen-title")
            yield Static("Todas as ferramentas disponiveis para o agente.", classes="screen-subtitle")

            table = Table(border_style="dim", expand=True)
            table.add_column("Nome", style="bold cyan")
            table.add_column("Descricao", style="white")
            for t in tools:
                table.add_row(t.name, t.description[:80])
            yield Static(table)
            yield Button("Fechar", variant="primary", id="close-tools")

    def on_button_pressed(self, event):
        if event.button.id == "close-tools":
            self.dismiss()


class HelpScreen(ModalScreen):
    def compose(self):
        with Vertical(id="help-screen"):
            yield Static("[bold]Ajuda - Atalhos e Comandos[/bold]", classes="screen-title")
            yield Static("""
[bold]Atalhos do Teclado[/bold]
  Ctrl+P          Abrir configuracao do provedor
  Ctrl+T          Abrir lista de ferramentas
  Ctrl+N          Nova conversa
  Ctrl+L          Limpar tela
  Ctrl+E          Exportar conversa
  Ctrl+H          Esta ajuda
  Ctrl+Q          Sair
  Esc             Fechar tela atual
  Tab             Navegar entre elementos

[bold]Comandos do Chat (digite /comando)[/bold]
  /help           Mostra ajuda
  /new            Nova conversa
  /clear          Limpa console
  /model          Mostra provedor/modelo
  /providers      Lista provedores
  /skills         Lista skills
  /tools          Lista ferramentas
  /theme          Abrir seletor de temas
  /export         Exportar conversa
  /stats          Estatisticas da sessao
  /learn          Ensinar skill
  /forget         Remover skill
  /exit           Sair
            """.strip())
            yield Button("Fechar", variant="primary", id="close-help")

    def on_button_pressed(self, event):
        if event.button.id == "close-help":
            self.dismiss()


class NuntiusApp(App):
    CSS = """
    Screen {
        background: $background;
    }

    #main-layout {
        height: 100%;
    }

    #chat-panel {
        width: 70%;
        height: 100%;
        border-right: solid $border;
    }

    #chat-panel #chat-history {
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }

    #chat-panel #input-container {
        height: 4;
        padding: 1;
        border-top: solid $border;
    }

    #chat-panel #input-container Input {
        width: 100%;
    }

    #chat-panel #shortcuts-hint {
        height: 1;
        color: $text-dim;
        text-align: center;
    }

    #tool-panel {
        width: 30%;
        height: 100%;
    }

    #tool-panel #tool-header {
        height: 3;
        padding: 0 1;
        border-bottom: solid $border;
        content-align: center middle;
    }

    #tool-panel #tool-content {
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }

    #tool-panel #tool-footer {
        height: 3;
        padding: 0 1;
        border-top: solid $border;
    }

    #tool-panel #tool-footer Label {
        width: 100%;
        text-align: center;
    }

    #theme-preview {
        width: 40;
        height: auto;
        padding: 2;
        background: $surface;
        border: thick $primary;
    }
    #theme-preview .preview-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    #theme-preview .preview-swatch {
        padding: 0 1;
        margin: 1 0;
    }

    #theme-selector, #provider-screen, #tools-screen, #help-screen {
        width: 60;
        height: auto;
        padding: 2;
        background: $surface;
        border: thick $primary;
    }
    #theme-selector #theme-list {
        height: 12;
        margin: 1 0;
    }
    .screen-title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    .screen-subtitle {
        text-align: center;
        color: $text-dim;
        padding-bottom: 1;
    }
    .button-row {
        height: 3;
        align: center middle;
    }
    .button-row Button {
        margin: 0 1;
    }
    #provider-screen Select, #provider-screen Input {
        width: 100%;
        margin: 0 0 1 0;
    }
    #provider-screen Label {
        padding: 0 0 0 0;
        color: $text-secondary;
    }
    """

    BINDINGS = [
        Binding("ctrl+p", "show_providers", "Provedor", show=True),
        Binding("ctrl+t", "show_tools", "Ferramentas", show=True),
        Binding("ctrl+n", "new_conversation", "Nova", show=True),
        Binding("ctrl+l", "clear_chat", "Limpar", show=True),
        Binding("ctrl+e", "export_chat", "Exportar", show=True),
        Binding("ctrl+h", "show_help", "Ajuda", show=True),
        Binding("ctrl+q", "quit_app", "Sair", show=True),
    ]

    current_theme_name = reactive("nuntius")
    current_provider = reactive("")
    current_model = reactive("")
    session_messages = reactive(0)
    session_tools = reactive(0)

    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.agent = Agent()
        self.current_provider = self.cfg.get("provider", "openai")
        self.current_model = self.cfg.get("model", "gpt-4o-mini")
        self._processing = False
        self._streaming_task = None

    def apply_theme(self, theme_name: str):
        self.current_theme_name = theme_name
        t = get_theme(theme_name)
        css = get_theme_css(t)
        self.stylesheet.update(css + self.CSS)
        self.refresh()

    def save_theme_preference(self):
        cfg = load_config()
        cfg["theme"] = self.current_theme_name
        save_config(cfg)

    def update_header(self):
        header = self.query_one("#tool-header", Static)
        header.update(
            f"[bold]{self.current_provider}[/bold] | [bold]{self.current_model}[/bold]\n"
            f"[dim]v{VERSION} | msgs: {self.session_messages}[/dim]"
        )

    def compose(self):
        t = get_theme(self.current_theme_name)
        with Horizontal(id="main-layout"):
            with Vertical(id="chat-panel"):
                yield Static(id="chat-history")
                with Vertical(id="input-container"):
                    yield Input(id="message-input", placeholder="Digite sua mensagem... (/help para comandos)")
                    yield Static(
                        "Ctrl+P:Provedor  Ctrl+T:Ferramentas  Ctrl+N:Nova  Ctrl+H:Ajuda  Ctrl+Q:Sair",
                        id="shortcuts-hint",
                    )
            with Vertical(id="tool-panel"):
                yield Static(id="tool-header")
                yield Static(id="tool-content")
                yield Static(id="tool-footer")

    def on_mount(self):
        self.apply_theme(self.current_theme_name)
        self.update_header()
        self.update_tool_panel()
        self.call_after_refresh(self._focus_input)

    def _focus_input(self):
        try:
            self.query_one("#message-input", Input).focus()
        except Exception:
            pass

    def update_tool_panel(self, tool_name: str = "", tool_result: str = ""):
        tools = registry.get_all()
        tool_lines = []
        for t in tools[:25]:
            icon = "●" if t.name == tool_name else "○"
            tool_lines.append(f"[dim]{icon}[/] [cyan]{t.name}[/]")

        content = self.query_one("#tool-content", Static)
        content.update("\n".join(tool_lines) if tool_lines else "[dim]Nenhuma ferramenta[/dim]")

        footer = self.query_one("#tool-footer", Static)
        if tool_name:
            footer.update(f"[bold]ultima tool:[/bold] [cyan]{tool_name}[/]")

    async def on_input_submitted(self, event: Input.Submitted):
        if self._processing:
            return

        text = event.value.strip()
        if not text:
            return

        input_widget = self.query_one("#message-input", Input)
        input_widget.value = ""

        if text.startswith("/"):
            await self._handle_command(text)
            return

        self._processing = True
        self.session_messages += 1

        chat = self.query_one("#chat-history", Static)
        current = chat.renderable or ""

        user_block = Panel(
            Markdown(text),
            title="[bold]Voce[/bold]",
            title_align="left",
            border_style="secondary",
            padding=(1, 2),
        )
        chat.update(current + "\n" + Text.from_ansi(user_block.__rich__()).plain if current else Text.from_ansi(user_block.__rich__()).plain)

        chat.update(current + "\n\n" + str(user_block) if current else str(user_block))

        try:
            response_buffer = ""
            async for event_data in self.agent.stream_chat(text):
                if event_data["type"] == "content":
                    response_buffer += event_data["data"]
                    chat.update(
                        current
                        + "\n\n" + str(user_block)
                        + "\n\n" + str(Panel(
                            Markdown(response_buffer + " ▌"),
                            title="[bold]Nuntius[/bold]",
                            title_align="left",
                            border_style="primary",
                            padding=(1, 2),
                        ))
                    )
                elif event_data["type"] == "tool_start":
                    self.session_tools += 1
                    tool_name = event_data["data"]
                    tool_panel = self.query_one("#tool-content", Static)
                    self.update_tool_panel(tool_name.split("(")[0], "")
                elif event_data["type"] == "tool_end":
                    name, result = event_data["data"]
                    chat.update(
                        chat.renderable
                        + "\n" + str(Panel(
                            Syntax(
                                result[:300],
                                "python" if result.startswith("{") or result.startswith("[") else "bash",
                                word_wrap=True,
                                theme="monokai",
                            ),
                            title=f"[bold]{name}[/bold]",
                            title_align="left",
                            border_style="warning",
                            padding=(0, 1),
                        ))
                    )
                elif event_data["type"] == "error":
                    chat.update(
                        chat.renderable
                        + "\n" + str(Panel(
                            f"[red]{event_data['data']}[/red]",
                            border_style="error",
                        ))
                    )

            if response_buffer:
                self.agent.learn_from_interaction(text, response_buffer)

        except Exception as e:
            chat.update(
                chat.renderable
                + "\n" + str(Panel(
                    f"[red]Erro: {e}[/red]",
                    border_style="error",
                ))
            )

        self._processing = False
        self._focus_input()

    async def _handle_command(self, text: str):
        cmd = text[1:].strip().lower()
        chat = self.query_one("#chat-history", Static)

        if cmd in ("exit", "quit", "sair"):
            await self.action_quit()
        elif cmd in ("help", "ajuda"):
            self.push_screen(HelpScreen())
        elif cmd in ("clear", "limpar"):
            chat.update("")
        elif cmd in ("new", "nova"):
            self.agent.reset_conversation()
            self.cfg = load_config()
            chat.update("")
            self.session_messages = 0
            self.session_tools = 0
            self.update_header()
        elif cmd == "model":
            prov = self.cfg.get("provider", "?")
            model = self.cfg.get("model", "?")
            chat.update(
                chat.renderable
                + "\n" + str(Panel(
                    f"[bold]Provedor:[/bold] {prov}\n[bold]Modelo:[/bold] {model}",
                    border_style="primary",
                ))
            )
        elif cmd == "providers":
            self.push_screen(ProviderScreen())
        elif cmd in ("tools", "ferramentas"):
            self.push_screen(ToolsScreen())
        elif cmd == "theme":
            self.push_screen(ThemeScreen())
        elif cmd == "export":
            self._export_conversation()
        elif cmd in ("stats", "status"):
            total = len(self.agent.messages)
            chat.update(
                chat.renderable
                + "\n" + str(Panel(
                    f"Mensagens: {total}\n"
                    f"Ferramentas usadas: {self.session_tools}\n"
                    f"Provedor: {self.current_provider}\n"
                    f"Modelo: {self.current_model}",
                    title="Estatisticas",
                    border_style="primary",
                ))
            )
        else:
            chat.update(
                chat.renderable
                + "\n" + str(Panel(
                    f"[yellow]Comando desconhecido: /{cmd}[/yellow]",
                    border_style="warning",
                ))
            )

    def _export_conversation(self):
        from datetime import datetime
        export_dir = Path.home() / ".config" / "nuntius" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"conversa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        lines = [f"# Conversa Nuntius\nData: {datetime.now().isoformat()}\n\n"]
        for msg in self.agent.messages:
            role = msg.get("role", "?").upper()
            content = msg.get("content", "") or ""
            if role == "SYSTEM":
                continue
            lines.append(f"## {role}\n\n{content}\n\n---\n\n")
        path.write_text("".join(lines))
        chat = self.query_one("#chat-history", Static)
        chat.update(
            chat.renderable
            + "\n" + str(Panel(
                f"[green]Conversa exportada: {path}[/green]",
                border_style="success",
            ))
        )

    def action_show_providers(self):
        if not self._processing:
            self.push_screen(ProviderScreen())

    def action_show_tools(self):
        if not self._processing:
            self.push_screen(ToolsScreen())

    def action_new_conversation(self):
        self.agent.reset_conversation()
        self.cfg = load_config()
        self.session_messages = 0
        self.session_tools = 0
        chat = self.query_one("#chat-history", Static)
        chat.update("")
        self.update_header()

    def action_clear_chat(self):
        chat = self.query_one("#chat-history", Static)
        chat.update("")

    def action_export_chat(self):
        if self.agent.messages:
            self._export_conversation()

    def action_show_help(self):
        self.push_screen(HelpScreen())

    def action_quit_app(self):
        self._shutdown()

    def _shutdown(self):
        if self._streaming_task and not self._streaming_task.done():
            self._streaming_task.cancel()
        asyncio.create_task(self._close_agent())

    async def _close_agent(self):
        await self.agent.close()
        self.exit()

    def on_screen_resume(self):
        self._focus_input()
