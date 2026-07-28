import asyncio
import logging
import shutil

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import ANSI

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nuntius")
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.status import Status
from rich.style import Style
from rich.table import Table
from rich.text import Text

from pathlib import Path

from ..config import (
    CONFIG_DIR,
    PROVIDER_INFO,
    ensure_dirs,
    load_config,
    save_config,
)
from ..core.agent import Agent
from ..platforms.gateway import Gateway
from ..providers.openai import ProviderError
from ..version import VERSION, get_local_commit, get_local_branch

GOLD = "gold1"
CYAN = "cyan"
ACCENT = "bold cyan"
MAGENTA = "magenta"
DIM = "grey62"
GREEN = "green"
RED = "red1"
console = Console()

PROVIDER_NAMES = list(PROVIDER_INFO.keys())

BANNER_ART = """\
  ███╗   ██╗██╗   ██╗███╗   ██╗████████╗██╗██╗   ██╗███████╗
  ████╗  ██║██║   ██║████╗  ██║╚══██╔══╝██║██║   ██║██╔════╝
  ██╔██╗ ██║██║   ██║██╔██╗ ██║   ██║   ██║██║   ██║███████╗
  ██║╚██╗██║██║   ██║██║╚██╗██║   ██║   ██║██║   ██║╚════██║
  ██║ ╚████║╚██████╔╝██║ ╚████║   ██║   ██║╚██████╔╝███████║
  ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═════╝ ╚══════╝"""


def pager_print(text, title=""):
    lines = text.split("\n")
    term_height = shutil.get_terminal_size().lines - 3
    if len(lines) > term_height:
        from rich.table import Table
        t = Table(title=title, border_style=GOLD)
        t.add_column("", style="white")
        for line in lines:
            t.add_row(line)
        with console.pager():
            console.print(t)
    else:
        console.print(text)


def make_banner(cfg: dict) -> Panel:
    provider = cfg.get("provider", "openai")
    model = cfg.get("model", "gpt-4o-mini")
    pname = PROVIDER_INFO.get(provider, {}).get("name", provider)
    mod = model.split("/")[-1] if "/" in model else model

    commit = get_local_commit()
    branch = get_local_branch()
    ver = f"v{VERSION}"
    if commit:
        ver += f" [{DIM}]{commit}[/{DIM}]"

    info_lines = [
        f"  [{CYAN}]█[/] [{DIM}]Provedor:[/] [{GOLD}]{pname}[/{GOLD}]   [{CYAN}]█[/] [{DIM}]Modelo:[/] [{GOLD}]{mod}[/{GOLD}]",
        f"  [{CYAN}]█[/] [{DIM}]Comandos:[/] [{GREEN}]/help[/] [{RED}]/exit[/] [{CYAN}]/new[/] [{GOLD}]/model[/]",
    ]

    mcp_cfg = cfg.get("mcp_servers", {})
    mcp_enabled = [k for k, v in mcp_cfg.items() if isinstance(v, dict) and v.get("enabled")]
    if mcp_enabled:
        info_lines.append(f"  [{CYAN}]█[/] [{DIM}]MCP:[/] [cyan]{', '.join(mcp_enabled)}[/]")

    inner = Group(
        Text(f"╔═══════════════════════════════════════════════════════════╗", style=GOLD),
        Align.center(Text(BANNER_ART, style=CYAN)),
        Align.center(Text(f"N U N T I U S   A I   {ver}", style=GOLD)),
        Align.center(Text(f"O Mensageiro da IA no Terminal  [{DIM}]{branch}[/{DIM}]", style=DIM)),
        Text(f"╠═══════════════════════════════════════════════════════════╣", style=GOLD),
        Text("\n".join(info_lines)),
        Text(f"╚═══════════════════════════════════════════════════════════╝", style=GOLD),
    )

    return inner


def show_providers_table():
    table = Table(title="Provedores Disponiveis", border_style=GOLD, header_style=GOLD)
    table.add_column("Codigo", style=GOLD)
    table.add_column("Nome", style=GREEN)
    table.add_column("Gratis")
    table.add_column("Site", style=DIM)
    for key, info in PROVIDER_INFO.items():
        free_tag = "[green]Sim[/green]" if info["free"] else "[yellow]Nao[/yellow]"
        site = info.get("site", "") or "[dim]-[/dim]"
        table.add_row(key, info["name"], free_tag, site)
    console.print(table)


def show_models(info: dict):
    table = Table(title=f"Modelos - {info['name']}", border_style=GOLD, header_style=GOLD)
    table.add_column("#", style=GOLD, justify="right")
    table.add_column("Modelo", style="white")
    for i, m in enumerate(info.get("models", []), 1):
        table.add_row(str(i), m)
    console.print(table)


def pick_model(info: dict, current: str = "") -> str:
    models = info.get("models", [])
    if not models:
        return Prompt.ask(f"[bold {GOLD}]Modelo[/bold {GOLD}]", default=current or info["model"])
    show_models(info)
    default = current or info.get("model", models[0])
    answer = Prompt.ask(
        f"[bold {GOLD}]Modelo[/bold {GOLD}] (digite o nome completo)",
        default=default,
    )
    return answer


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    ensure_dirs()
    cfg = load_config()
    log_level = cfg.get("log_level", "WARNING")
    logging.getLogger("nuntius").setLevel(getattr(logging, log_level.upper(), logging.WARNING))
    log.debug(f"Log level: {log_level}")
    if ctx.invoked_subcommand is None:
        try:
            asyncio.run(interactive_chat())
        except KeyboardInterrupt:
            console.print(f"\n[bold {GOLD}]Ate logo![/bold {GOLD}]")


def run_setup(cfg: dict = None):
    ensure_dirs()
    if cfg is None:
        cfg = load_config()
    console.print(Panel.fit("[bold]Configuracao do Nuntius[/bold]", border_style=GOLD))

    show_providers_table()

    provider = Prompt.ask(
        f"[bold {GOLD}]Provedor de IA[/bold {GOLD}] (digite o codigo)",
        choices=PROVIDER_NAMES,
        default=cfg.get("provider", "openai"),
    )
    cfg["provider"] = provider
    info = PROVIDER_INFO[provider]
    prov_cfg = cfg["providers"][provider]

    if info.get("site"):
        console.print(f"[dim]Obtenha sua API Key em:[/dim] [bold {GOLD}]{info['site']}[/bold {GOLD}]")

    api_key = Prompt.ask(
        f"[bold {GOLD}]API Key[/bold {GOLD}]" + (" (deixe vazio se for local)" if provider == "ollama" else ""),
        default=prov_cfg.get("api_key", ""),
    )
    prov_cfg["api_key"] = api_key

    base_url = Prompt.ask(
        f"[bold {GOLD}]Base URL[/bold {GOLD}]",
        default=prov_cfg.get("base_url", info["url"]),
    )
    if base_url:
        prov_cfg["base_url"] = base_url

    model = pick_model(info, cfg.get("model", ""))
    cfg["model"] = model

    save_config(cfg)
    console.print(f"\n[green]Configuracao salva em:[/green] {CONFIG_DIR / 'config.yaml'}")
    return cfg


_SHOWED_403_HINT = False


def _handle_provider_error(e: ProviderError, cfg: dict):
    global _SHOWED_403_HINT
    pname = cfg.get("provider", "openai")
    model = cfg.get("model", "gpt-4o-mini")
    base = cfg.get("providers", {}).get(pname, {}).get("base_url", "")
    msg = f"[red]Erro do provedor:[/red] {e.message}"

    if e.status == 403 or e.status == 401:
        if not _SHOWED_403_HINT:
            _SHOWED_403_HINT = True
            console.print(Panel.fit(
                f"[red]Erro {e.status}:[/red] {e.message}\n\n"
                f"[yellow]Provedor:[/yellow] {pname}\n"
                f"[yellow]Modelo:[/yellow] {model}\n"
                f"[yellow]Endpoint:[/yellow] {base}\n\n"
                f"[green]Solucoes:[/green]\n"
                f"  1. Execute [bold]nuntius setup[/bold] para configurar um provedor gratuito\n"
                f"  2. Verifique se a API Key esta correta em: {CONFIG_DIR / 'config.yaml'}\n"
                f"  3. Provedores gratuitos: [bold]groq[/bold], [bold]github[/bold], [bold]nvidia[/bold], [bold]fireworks[/bold]",
                border_style="red",
                title="Falha de Autenticacao",
            ))
        else:
            console.print(msg)
    else:
        console.print(msg)


@cli.command()
def setup():
    """Configura o Nuntius pela primeira vez."""
    run_setup()
    console.print(f"[green]Execute [/green][bold {GOLD}]nuntius[/bold {GOLD}][green] para comecar.[/green]")


@cli.command()
@click.argument("message", nargs=-1)
def run(message):
    """Executa uma mensagem unica."""
    prompt = " ".join(message) if message else Prompt.ask(f"[bold {GOLD}]Mensagem[/bold {GOLD}]")
    asyncio.run(single_run(prompt))


@cli.command()
def model():
    """Gerencia o modelo e provedor ativos."""
    cfg = load_config()
    current = cfg.get("provider", "openai")
    current_model = cfg.get("model", "gpt-4o-mini")

    console.print(f"[bold {GOLD}]Provedor:[/bold {GOLD}] {current} ({PROVIDER_INFO.get(current, {}).get('name', current)})")
    console.print(f"[bold {GOLD}]Modelo:[/bold {GOLD}] {current_model}")

    if click.confirm(f"[{GOLD}]Deseja alterar?[/{GOLD}]", default=False):
        run_setup(cfg)


@cli.command()
def gateway():
    """Inicia o gateway para Telegram/Discord."""
    cfg = load_config()
    p = cfg.get("platforms", {})
    enabled = [k for k, v in p.items() if isinstance(v, dict) and v.get("enabled")]
    if not enabled:
        console.print("[yellow]Nenhuma plataforma habilitada.[/yellow]")
        console.print("[bold]Use:[/bold] nuntius platform enable <nome>")
        return
    gw = Gateway()
    asyncio.run(gw.run())


@cli.group()
def platform():
    """Configura plataformas (Telegram, Discord, etc)."""


@platform.command()
@click.argument("name")
def enable(name: str):
    """Habilita uma plataforma (telegram, discord, github, drive)."""
    cfg = load_config()
    name = name.lower()
    if name not in cfg.get("platforms", {}):
        console.print(f"[red]Plataforma desconhecida: {name}[/red]")
        return
    platform_cfg = cfg["platforms"][name]
    platform_cfg["enabled"] = True

    if name == "telegram":
        token = Prompt.ask("Token do Telegram", default=platform_cfg.get("token", ""))
        platform_cfg["token"] = token
    elif name == "discord":
        token = Prompt.ask("Token do Discord", default=platform_cfg.get("token", ""))
        platform_cfg["token"] = token
    elif name == "github":
        token = Prompt.ask("Token do GitHub", default=platform_cfg.get("token", ""))
        platform_cfg["token"] = token
    elif name == "drive":
        creds = Prompt.ask("Caminho do credentials.json", default=platform_cfg.get("credentials_path", ""))
        platform_cfg["credentials_path"] = creds

    save_config(cfg)
    console.print(f"[green]Plataforma '{name}' habilitada![/green]")


@platform.command()
@click.argument("name")
def disable(name: str):
    """Desabilita uma plataforma."""
    cfg = load_config()
    if name in cfg.get("platforms", {}):
        cfg["platforms"][name]["enabled"] = False
        save_config(cfg)
        console.print(f"[yellow]Plataforma '{name}' desabilitada.[/yellow]")


@cli.command()
@click.argument("name")
def mcp(name: str):
    """Gerencia servidores MCP."""
    cfg = load_config()
    servers = cfg.get("mcp_servers", {})
    if name not in servers:
        console.print(f"[red]Servidor MCP desconhecido: {name}[/red]")
        console.print(f"[dim]Servidores configurados: {', '.join(servers.keys()) or 'nenhum'}[/dim]")
        return
    server = servers[name]
    if click.confirm(f"[{GOLD}]Habilitar servidor MCP '{name}'?[/{GOLD}]", default=not server.get("enabled", False)):
        server["enabled"] = not server.get("enabled", False)
        status = "habilitado" if server["enabled"] else "desabilitado"
        save_config(cfg)
        console.print(f"[green]MCP '{name}' {status}![/green]")
    command = Prompt.ask("Comando", default=server.get("command", ""))
    if command:
        server["command"] = command
    args_str = Prompt.ask("Argumentos (separados por espaco)", default=" ".join(server.get("args", [])))
    server["args"] = args_str.split() if args_str else []
    save_config(cfg)
    console.print(f"[green]Servidor MCP '{name}' configurado![/green]")


@cli.command()
def version():
    """Mostra a versao do Nuntius."""
    console.print(make_banner(load_config()))


async def single_run(prompt: str):
    cfg = load_config()
    provider_cfg = cfg.get("providers", {}).get(cfg.get("provider", "openai"), {})
    if not provider_cfg.get("api_key") and cfg.get("provider") != "ollama":
        console.print("[red]API Key nao configurada. Execute 'nuntius setup' primeiro.[/red]")
        return

    agent = Agent()
    try:
        with Status("[dim]Processando...[/dim]", spinner="dots"):
            async for event in agent.stream_chat(prompt):
                if event["type"] == "content":
                    console.print(event["data"], end="")
                elif event["type"] == "tool_start":
                    console.print(f"\n[dim]{event['data']}[/dim]")
                elif event["type"] == "tool_end":
                    name, result = event["data"]
                    console.print(f"\n[dim]  {name}: {result[:200]}[/dim]")
                elif event["type"] == "error":
                    console.print(f"\n[red]{event['data']}[/red]")
        console.print()
    except ProviderError as e:
        _handle_provider_error(e, cfg)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
    finally:
        await agent.close()


async def interactive_chat():
    cfg = load_config()
    provider_cfg = cfg.get("providers", {}).get(cfg.get("provider", "openai"), {})
    if not provider_cfg.get("api_key") and cfg.get("provider") != "ollama":
        console.print(Panel.fit(
            f"[yellow]Nenhuma API Key configurada![/yellow]\n"
            f"Execute [bold {GOLD}]nuntius setup[/bold {GOLD}] para configurar.",
            border_style="yellow",
        ))
        if click.confirm(f"[{GOLD}]Deseja configurar agora?[/{GOLD}]", default=True):
            run_setup(cfg)
            cfg = load_config()
            provider_cfg = cfg.get("providers", {}).get(cfg.get("provider", "openai"), {})
            if not provider_cfg.get("api_key"):
                return

    agent = Agent()
    console.print(make_banner(cfg))
    console.print()

    session = PromptSession(history=InMemoryHistory())

    try:
        while True:
            try:
                user_input = await session.prompt_async("\n\x1b[1mVoce\x1b[0m ")
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            if user_input.startswith("/"):
                cmd = user_input[1:].strip().lower()
                if cmd in ("exit", "quit", "sair"):
                    break
                elif cmd in ("help", "ajuda"):
                    help_panel = Panel.fit(
                        Group(
                            Text.assemble(("\n", ""), ("[ Comandos do Chat ]", f"bold {GOLD}"), ("\n", "")),
                            Rule(style=DIM),
                            Text.assemble(
                                ("/exit  ", RED), ("/quit  ", RED), ("/sair", RED),
                                ("  Sai do chat", DIM), ("\n", ""),
                                ("/help  ", GREEN), ("/ajuda", GREEN),
                                ("  Mostra esta ajuda", DIM), ("\n", ""),
                                ("/clear ", ACCENT), ("/limpar", ACCENT),
                                ("  Limpa o console", DIM), ("\n", ""),
                                ("/new   ", GOLD), ("/nova", GOLD),
                                ("  Nova conversa", DIM), ("\n", ""),
                                ("/model ", GOLD),
                                ("  Mostra provedor/modelo ativos", DIM), ("\n", ""),
                                ("/providers ", GOLD),
                                ("  Lista provedores disponiveis", DIM), ("\n", ""),
                                ("/skills ", "cyan"),
                                ("  Lista skills aprendidas", DIM), ("\n", ""),
                                ("/good ", GREEN), ("/bom ", GREEN), ("/ok", GREEN),
                                ("  Marca interacao como bem-sucedida", DIM), ("\n", ""),
                                ("/bad ", RED), ("/ruim ", RED), ("/fail", RED),
                                ("  Marca interacao como mal-sucedida", DIM), ("\n", ""),
                                ("/feedback ", GOLD), ("/stats ", GOLD),
                                ("  Estatisticas de aprendizado", DIM), ("\n", ""),
                                ("/learn nome: instrucao", "cyan"),
                                ("  Ensina uma skill", DIM), ("\n", ""),
                                ("/forget nome", "cyan"),
                                ("  Remove uma skill", DIM), ("\n", ""),
                                ("/mcp ", ACCENT),
                                ("  Mostra status dos servidores MCP", DIM), ("\n", ""),
                                ("/subagents ", "cyan"),
                                ("  Lista subagentes ativos", DIM),
                            ),
                            Rule(style=DIM),
                            Text.assemble(
                                ("\n[ Comandos Externos ]", f"bold {GOLD}"),
                                ("\n", ""),
                                ("  nuntius setup        ", DIM),
                                ("Configurar provedor/API", "white"),
                                ("\n", ""),
                                ("  nuntius gateway      ", DIM),
                                ("Iniciar Telegram/Discord", "white"),
                                ("\n", ""),
                                ("  nuntius platform     ", DIM),
                                ("Gerenciar plataformas", "white"),
                                ("\n", ""),
                                ("  nuntius mcp <nome>   ", DIM),
                                ("Configurar servidor MCP", "white"),
                                ("\n", ""),
                                ("  nuntius run <msg>    ", DIM),
                                ("Mensagem unica", "white"),
                            ),
                        ),
                        border_style=GOLD,
                        title="Ajuda",
                    )
                    console.print(help_panel)
                    continue
                elif cmd in ("clear", "limpar"):
                    console.clear()
                    console.print(make_banner(cfg))
                    continue
                elif cmd in ("new", "nova"):
                    agent.reset_conversation()
                    cfg = load_config()
                    console.print("[green]Nova conversa iniciada![/green]")
                    continue
                elif cmd == "model":
                    p = cfg.get("provider", "openai")
                    m = cfg.get("model", "gpt-4o-mini")
                    pname = PROVIDER_INFO.get(p, {}).get("name", p)
                    console.print(Panel.fit(
                        Text.assemble(
                            ("Provedor: ", DIM), (f"{p} ({pname})", GOLD), ("\n", ""),
                            ("Modelo:   ", DIM), (f"{m}", "white"),
                        ),
                        border_style=GOLD,
                        title="Configuracao Ativa",
                    ))
                    continue
                elif cmd == "providers":
                    show_providers_table()
                    console.print("[dim]Use setas ou Page Up/Down para navegar, 'q' para sair[/dim]")
                    continue
                elif cmd == "skills":
                    skills = agent.skills.list_skills()
                    if skills:
                        content = "\n".join(f"  [{GREEN}]\u2713[/] {s}" for s in skills)
                        pager_print(content, title="Skills Aprendidas")
                    else:
                        console.print("[dim]Nenhuma skill aprendida.[/dim]")
                    continue
                elif cmd in ("tools", "ferramentas"):
                    from ..tools.registry import get_all
                    from rich.table import Table
                    all_tools = get_all()
                    tbl = Table(title=f"Ferramentas ({len(all_tools)})", border_style=GOLD)
                    tbl.add_column("Nome", style="cyan")
                    tbl.add_column("Descricao", style="white")
                    for t in all_tools:
                        tbl.add_row(t.name, t.description[:60])
                    with console.pager():
                        console.print(tbl)
                    continue
                elif cmd == "providers":
                    from ..providers import ProviderRegistry
                    from rich.table import Table
                    registered = ProviderRegistry.list()
                    tbl = Table(title=f"Provedores ({len(registered)})", border_style=GOLD)
                    tbl.add_column("Nome", style="cyan")
                    for p in sorted(registered):
                        tbl.add_row(p)
                    console.print(tbl)
                    continue
                elif cmd == "mcp":
                    mcp_cfg = cfg.get("mcp_servers", {})
                    if not mcp_cfg:
                        console.print("[dim]Nenhum servidor MCP configurado.[/dim]")
                        console.print("Adicione em ~/.config/nuntius/config.yaml ou use: nuntius mcp <nome>")
                    else:
                        table = Table(title="Servidores MCP", border_style=GOLD, header_style=GOLD)
                        table.add_column("Nome", style=GOLD)
                        table.add_column("Comando", style="white")
                        table.add_column("Status")
                        for k, v in mcp_cfg.items():
                            status = "[green]Ativo[/green]" if v.get("enabled") else "[dim]Inativo[/dim]"
                            cmd_display = v.get("command", "")
                            args_display = " ".join(v.get("args", []))
                            full_cmd = f"{cmd_display} {args_display}".strip()
                            table.add_row(k, full_cmd, status)
                        console.print(table)
                    continue
                elif cmd.startswith("search"):
                    query = cmd[7:].strip()
                    if not query:
                        console.print("[yellow]Use: /search <termo>[/yellow]")
                        continue
                    if not agent.vector_memory or not agent.vector_memory.available:
                        console.print("[yellow]Memoria vetorial indisponivel. Instale chromadb: pip install chromadb[/yellow]")
                        continue
                    from rich.table import Table
                    results = agent.vector_memory.search(query, n_results=10)
                    if not results:
                        console.print("[dim]Nenhum resultado encontrado.[/dim]")
                        continue
                    tbl = Table(title=f"Busca: {query}", border_style=GOLD)
                    tbl.add_column("Conversa", style="cyan")
                    tbl.add_column("Papel", style=DIM)
                    tbl.add_column("Conteudo", style="white")
                    for r in results:
                        tbl.add_row(r.get("conv_id", "?"), r.get("role", "?"), r.get("content", "")[:120])
                    with console.pager():
                        console.print(tbl)
                    continue
                elif cmd in ("scheduled", "tasks", "cron"):
                    from ..core.scheduler import list_tasks
                    tasks = list_tasks()
                    if not tasks:
                        console.print("[dim]Nenhuma tarefa agendada.[/dim]")
                        continue
                    tbl = Table(title="Tarefas Agendadas (cron)", border_style=GOLD)
                    tbl.add_column("ID", style="cyan")
                    tbl.add_column("Cron", style=GOLD)
                    tbl.add_column("Comando", style="white")
                    for t in tasks:
                        tbl.add_row(t["id"], t["cron"], t["command"])
                    console.print(tbl)
                    continue
                elif cmd in ("plugins", "plug"):
                    if not agent.plugin_manager:
                        console.print("[yellow]Sistema de plugins desabilitado.[/yellow]")
                        continue
                    plugins = agent.plugin_manager.list_plugins()
                    if not plugins:
                        console.print("[dim]Nenhum plugin carregado.[/dim]")
                        continue
                    tbl = Table(title="Plugins", border_style=GREEN)
                    tbl.add_column("Nome", style="cyan")
                    tbl.add_column("Caminho", style=DIM)
                    tbl.add_column("Status")
                    for p in plugins:
                        status = f"[red]Erro[/]" if p.error else "[green]OK[/]"
                        tbl.add_row(p.name, p.path, status)
                    console.print(tbl)
                    continue
                elif cmd in ("subagents", "agents", "sub"):
                    from ..tools.orchestrator_tools import _get_orch
                    orch = _get_orch()
                    agents = orch.list_subagents()
                    if not agents:
                        console.print("[dim]Nenhum subagente ativo.[/dim]")
                        continue
                    tbl = Table(title="Subagentes", border_style="cyan")
                    tbl.add_column("ID", style="cyan")
                    tbl.add_column("Funcao", style=GOLD)
                    tbl.add_column("Tarefa", style="white")
                    tbl.add_column("Status")
                    for a in agents:
                        s = a["status"]
                        status_icon = "[green]done[/]" if s == "done" else "[yellow]running[/]" if s == "running" else "[red]error[/]"
                        tbl.add_row(a["id"], a["role"], a["task"][:50], status_icon)
                    console.print(tbl)
                    continue
                elif cmd in ("good", "bom", "ok"):
                    if agent.learning_loop:
                        msg = agent.learning_loop.mark_good()
                        console.print(f"[green]{msg}[/green]")
                    else:
                        console.print("[yellow]Loop de aprendizado desabilitado.[/yellow]")
                    continue
                elif cmd in ("bad", "ruim", "fail"):
                    if agent.learning_loop:
                        msg = agent.learning_loop.mark_bad()
                        console.print(f"[red]{msg}[/red]")
                    else:
                        console.print("[yellow]Loop de aprendizado desabilitado.[/yellow]")
                    continue
                elif cmd in ("feedback", "stats", "estatisticas"):
                    if not agent.learning_loop:
                        console.print("[yellow]Loop de aprendizado desabilitado.[/yellow]")
                        continue
                    stats = agent.learning_loop.get_stats()
                    s = stats.get("skills", {})
                    tbl = Table(title="Aprendizado", border_style=GOLD)
                    tbl.add_column("Metrica", style=GOLD)
                    tbl.add_column("Valor", style="white")
                    tbl.add_row("Padroes registrados", str(s.get("total_patterns", 0)))
                    tbl.add_row("Licoes confiaveis", str(s.get("reliable_lessons", 0)))
                    tools = stats.get("tools", {})
                    for tname, tstats in sorted(tools.items()):
                        rate = tstats["successes"] / max(tstats["total"], 1) * 100
                        tbl.add_row(f"  {tname}", f"{rate:.0f}% ({tstats['successes']}/{tstats['total']})")
                    console.print(tbl)
                    continue
                elif cmd.startswith("learn "):
                    rest = cmd[6:].strip()
                    if ":" in rest:
                        name, instruction = rest.split(":", 1)
                        agent.skills.learn(name.strip(), instruction.strip())
                        console.print(f"[green]Skill '{name.strip()}' aprendida![/green]")
                    else:
                        console.print("[yellow]Use: /learn nome: instrucao[/yellow]")
                    continue
                elif cmd.startswith("forget "):
                    name = cmd[7:].strip()
                    agent.skills.forget(name)
                    console.print(f"[yellow]Skill '{name}' removida.[/yellow]")
                    continue
                elif cmd in ("history", "historico"):
                    history_msgs = agent.messages.copy()
                    if not history_msgs:
                        console.print("[dim]Nenhuma mensagem no historico.[/dim]")
                        continue
                    from rich.table import Table
                    tbl = Table(title="Historico da Conversa", border_style=GOLD)
                    tbl.add_column("#", style=GOLD)
                    tbl.add_column("Papel", style="cyan")
                    tbl.add_column("Conteudo", style="white")
                    for i, msg in enumerate(history_msgs):
                        role = msg.get("role", "?")
                        content = (msg.get("content", "") or "")[:100]
                        if role == "system":
                            content = "(system prompt)"
                        tbl.add_row(str(i), role, content)
                    console.print(tbl)
                    continue
                elif cmd.startswith("export"):
                    from datetime import datetime
                    export_path = cmd[6:].strip() or f"nuntius_conversa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    exp_path = Path(export_path).expanduser().resolve()
                    lines = [f"# Conversa Nuntius\n", f"Data: {datetime.now().isoformat()}\n", f"Provedor: {cfg.get('provider')}\n", f"Modelo: {cfg.get('model')}\n\n"]
                    for msg in agent.messages:
                        role = msg.get("role", "?").upper()
                        content = msg.get("content", "") or ""
                        if role == "SYSTEM":
                            continue
                        lines.append(f"## **{role}**\n\n{content}\n\n---\n\n")
                    exp_path.parent.mkdir(parents=True, exist_ok=True)
                    exp_path.write_text("".join(lines), encoding="utf-8")
                    console.print(f"[green]Conversa exportada para:[/green] {exp_path}")
                    continue
                elif cmd in ("stats", "status"):
                    total = len(agent.messages)
                    tool_count = sum(1 for m in agent.messages if m.get("role") == "tool")
                    user_count = sum(1 for m in agent.messages if m.get("role") == "user")
                    asst_count = sum(1 for m in agent.messages if m.get("role") == "assistant")
                    console.print(Panel.fit(
                        f"Mensagens: {total} (user: {user_count}, assistant: {asst_count}, tools: {tool_count})\n"
                        f"Provedor: {cfg.get('provider')} | Modelo: {cfg.get('model')}",
                        title="Estatisticas", border_style=GOLD,
                    ))
                    continue
                elif cmd == "cache":
                    from ..tools.registry import get_cache_size, clear_cache
                    console.print(Panel.fit(
                        f"Cache ativo: {get_cache_size()} entradas\n"
                        f"Use [bold]/cache limpar[/bold] para limpar",
                        title="Cache", border_style=GOLD,
                    ))
                    continue
                elif cmd.startswith("cache "):
                    sub = cmd[6:].strip()
                    if sub in ("clear", "limpar"):
                        from ..tools.registry import clear_cache
                        clear_cache()
                        console.print("[green]Cache limpo.[/green]")
                    continue
                else:
                    console.print(f"[red]Comando desconhecido: /{cmd}[/red]")
                    continue

            with Status("[dim]Processando...[/dim]", spinner="dots"):
                try:
                    async for event in agent.stream_chat(user_input):
                        if event["type"] == "content":
                            console.print(event["data"], end="")
                        elif event["type"] == "tool_start":
                            console.print(f"\n[dim]{event['data']}[/dim]")
                        elif event["type"] == "tool_end":
                            name, result = event["data"]
                            console.print(f"\n[dim]  {name}: {result[:200]}[/dim]")
                        elif event["type"] == "error":
                            console.print(f"\n[red]{event['data']}[/red]")
                        elif event["type"] == "done":
                            agent.learn_from_interaction(user_input, event["data"])
                    console.print()
                except ProviderError as e:
                    _handle_provider_error(e, cfg)
                except Exception as e:
                    console.print(f"[red]Erro: {e}[/red]")
    finally:
        await agent.close()


if __name__ == "__main__":
    cli()
