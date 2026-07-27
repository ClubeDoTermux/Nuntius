import asyncio
import shutil

import click
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

    try:
        while True:
            user_input = Prompt.ask(f"\n[bold]Voce[/bold]")
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
                                ("/learn nome: instrucao", "cyan"),
                                ("  Ensina uma skill", DIM), ("\n", ""),
                                ("/forget nome", "cyan"),
                                ("  Remove uma skill", DIM), ("\n", ""),
                                ("/mcp ", ACCENT),
                                ("  Mostra status dos servidores MCP", DIM),
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
                    continue
                elif cmd == "skills":
                    skills = agent.skills.list_skills()
                    if skills:
                        console.print(Panel(
                            "\n".join(f"  [{GREEN}]\u2713[/] {s}" for s in skills),
                            title="Skills Aprendidas",
                            border_style=GOLD,
                        ))
                    else:
                        console.print("[dim]Nenhuma skill aprendida.[/dim]")
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
                    console.print(f"[red]Erro do provedor: {e.message}[/red]")
                except Exception as e:
                    console.print(f"[red]Erro: {e}[/red]")
    finally:
        await agent.close()


if __name__ == "__main__":
    cli()
