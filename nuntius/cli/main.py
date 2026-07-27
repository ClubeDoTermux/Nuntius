import asyncio

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

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
from ..version import VERSION

GOLD = "gold1"
console = Console()

PROVIDER_NAMES = list(PROVIDER_INFO.keys())


def show_providers_table():
    table = Table(title="Provedores disponiveis", border_style=GOLD)
    table.add_column("Codigo", style=GOLD)
    table.add_column("Nome", style="green")
    table.add_column("Gratis")
    for key, info in PROVIDER_INFO.items():
        free_tag = "[green]Sim[/green]" if info["free"] else "[yellow]Nao[/yellow]"
        table.add_row(key, info["name"], free_tag)
    console.print(table)


def show_models(info: dict):
    table = Table(title=f"Modelos disponiveis - {info['name']}", border_style=GOLD)
    table.add_column("#", style=GOLD, justify="right")
    table.add_column("Modelo", style="white")
    for i, m in enumerate(info.get("models", []), 1):
        table.add_row(str(i), m)
    console.print(table)


def pick_model(info: dict, current: str = "") -> str:
    models = info.get("models", [])
    if not models:
        return Prompt.ask(f"[{GOLD}]Modelo[/{GOLD}]", default=current or info["model"])
    show_models(info)
    default = current or info.get("model", models[0])
    answer = Prompt.ask(
        f"[{GOLD}]Modelo[/{GOLD}] (digite o nome completo)",
        default=default,
    )
    return answer


def get_info_key(info: dict, key: str, default=""):
    return info.get(key, default)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    ensure_dirs()
    if ctx.invoked_subcommand is None:
        try:
            asyncio.run(interactive_chat())
        except KeyboardInterrupt:
            console.print(f"\n[{GOLD}]Ate logo![/{GOLD}]")


def run_setup(cfg: dict = None):
    ensure_dirs()
    if cfg is None:
        cfg = load_config()
    console.print(Panel.fit("[bold]Configuracao do Nuntius[/bold]", border_style=GOLD))

    show_providers_table()

    provider = Prompt.ask(
        f"[{GOLD}]Provedor de IA[/{GOLD}] (digite o codigo)",
        choices=PROVIDER_NAMES,
        default=cfg.get("provider", "openai"),
    )
    cfg["provider"] = provider
    info = PROVIDER_INFO[provider]
    prov_cfg = cfg["providers"][provider]

    if info.get("site"):
        console.print(f"[dim]Obtem sua API Key em:[/dim] [{GOLD}]{info['site']}[/{GOLD}]")

    api_key = Prompt.ask(
        f"[{GOLD}]API Key[/{GOLD}]" + (" (deixe vazio se for local)" if provider == "ollama" else ""),
        default=prov_cfg.get("api_key", ""),
    )
    prov_cfg["api_key"] = api_key

    base_url = Prompt.ask(
        f"[{GOLD}]Base URL[/{GOLD}]",
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
    prompt = " ".join(message) if message else Prompt.ask(f"[{GOLD}]Mensagem[/{GOLD}]")
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
def version():
    """Mostra a versao do Nuntius."""
    console.print(f"Nuntius v{VERSION}")


async def single_run(prompt: str):
    cfg = load_config()
    provider_cfg = cfg.get("providers", {}).get(cfg.get("provider", "openai"), {})
    if not provider_cfg.get("api_key") and cfg.get("provider") != "ollama":
        console.print("[red]API Key nao configurada. Execute 'nuntius setup' primeiro.[/red]")
        return

    agent = Agent()
    try:
        async for event in agent.stream_chat(prompt):
            if event["type"] == "content":
                console.print(event["data"], end="")
            elif event["type"] == "tool_start":
                console.print(f"\n[dim]{event['data']}[/dim]")
            elif event["type"] == "tool_end":
                name, result = event["data"]
                console.print(f"\n[dim] {name}: {result[:200]}[/dim]")
            elif event["type"] == "error":
                console.print(f"\n[red]{event['data']}[/red]")
        console.print()
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
    finally:
        await agent.close()


def make_banner(cfg: dict, update_msg: str) -> str:
    provider = cfg.get("provider", "openai")
    model = cfg.get("model", "gpt-4o-mini")
    pname = PROVIDER_INFO.get(provider, {}).get("name", provider)
    mod = model.split("/")[-1] if "/" in model else model
    banner = (
        f"\n"
        f"  ┌────────────────────────────────────────────┐\n"
        f"  │            N U N T I U S  A I             │\n"
        f"  │         v{VERSION}                            │\n"
        f"  │  {pname} - {mod}           │\n"
        f"  │  /help · /exit                             │\n"
        f"  └────────────────────────────────────────────┘\n"
    )
    if update_msg:
        banner += f"\n  {update_msg}\n"
    return banner


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
    console.print(make_banner(cfg, ""))

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
                    console.print(Panel.fit(
                        "[bold]Comandos no chat:[/bold]\n"
                        "  /exit          Sai do chat\n"
                        "  /help          Mostra esta mensagem\n"
                        "  /clear         Limpa o console\n"
                        "  /new           Nova conversa\n"
                        "  /model         Mostra modelo ativo\n"
                        "  /providers     Lista provedores\n"
                        "  /skills        Lista skills aprendidas\n"
                        "  /learn         /learn nome: instrucao\n"
                        "  /forget        /forget nome\n"
                        "\n[bold]Comandos externos:[/bold]\n"
                        "  nuntius gateway   Inicia Telegram/Discord\n"
                        "  nuntius setup     Configura o Nuntius",
                        border_style=GOLD,
                    ))
                    continue
                elif cmd in ("clear", "limpar"):
                    console.clear()
                    continue
                elif cmd in ("new", "nova"):
                    agent.reset_conversation()
                    console.print("Nova conversa")
                    continue
                elif cmd == "model":
                    console.print(f"Provedor: {cfg.get('provider')} | Modelo: {cfg.get('model')}")
                    continue
                elif cmd == "providers":
                    show_providers_table()
                    continue
                elif cmd == "skills":
                    skills = agent.skills.list_skills()
                    if skills:
                        for s in skills:
                            console.print(f"- {s}")
                    else:
                        console.print("Nenhuma skill aprendida.")
                    continue
                elif cmd.startswith("learn "):
                    rest = cmd[6:].strip()
                    if ":" in rest:
                        name, instruction = rest.split(":", 1)
                        agent.skills.learn(name.strip(), instruction.strip())
                        console.print(f"Skill '{name.strip()}' aprendida!")
                    else:
                        console.print("Use: /learn nome: instrucao")
                    continue
                elif cmd.startswith("forget "):
                    name = cmd[7:].strip()
                    agent.skills.forget(name)
                    console.print(f"Skill '{name}' removida.")
                    continue
                else:
                    console.print(f"Comando desconhecido: /{cmd}")
                    continue

            console.print(f"\n[dim]Processando...[/dim]")
            try:
                async for event in agent.stream_chat(user_input):
                    if event["type"] == "content":
                        console.print(event["data"], end="")
                    elif event["type"] == "tool_start":
                        console.print(f"\n[dim]{event['data']}[/dim]")
                    elif event["type"] == "tool_end":
                        name, result = event["data"]
                        console.print(f"\n[dim] {name}: {result[:200]}[/dim]")
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
