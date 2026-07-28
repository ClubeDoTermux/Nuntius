# Nuntius AI

<p align="center">
  <a href="https://clubedotermux.github.io/Nuntius/"><img src="https://img.shields.io/badge/📖_Site_oficial-clubedotermux.github.io/Nuntius-gold?style=flat-square" alt="Site"></a>
  <a href="https://github.com/ClubeDoTermux/Nuntius/releases"><img src="https://img.shields.io/github/v/release/ClubeDoTermux/Nuntius?style=flat-square&label=versão" alt="Version"></a>
  <a href="https://github.com/ClubeDoTermux/Nuntius/actions"><img src="https://img.shields.io/github/actions/workflow/status/ClubeDoTermux/Nuntius/test.yml?style=flat-square&label=tests" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
</p>

                    ╔╗╔┌─┐┌┬┐╔╦╗╔╗╔┬─┐╔╗
                    ║║║│ │ │ ║║║║║║║║║║
                    ║║║│ │ │ ║║║║║║║║║║
                    ╚╩╝└─┘ ┴ ╩╩╝╚╩╝└─┘╚╝

O Mensageiro da IA no Terminal — um agente de IA completo para Termux, Linux e macOS.

📖 **Site oficial**: [clubedotermux.github.io/Nuntius](https://clubedotermux.github.io/Nuntius/) — comandos, instalação e documentação.

## Instalação

```bash
curl -fsSL https://raw.githubusercontent.com/ClubeDoTermux/Nuntius/main/install.sh | bash
```

Ou manualmente:

```bash
pkg update && pkg upgrade
pkg install python git
pip install git+https://github.com/ClubeDoTermux/Nuntius.git
nuntius setup
```

## Comandos CLI

| Comando | Descrição |
|---|---|
| `nuntius` | Inicia o chat interativo com banner |
| `nuntius setup` | Configura provedor, modelo e API Key |
| `nuntius run <mensagem>` | Executa uma mensagem única e sai |
| `nuntius model` | Mostra/altera o provedor e modelo ativos |
| `nuntius gateway` | Inicia o gateway multi-plataforma |
| `nuntius platform list` | Lista plataformas disponíveis e status |
| `nuntius platform enable <nome>` | Habilita e configura uma plataforma |
| `nuntius platform disable <nome>` | Desabilita uma plataforma |
| `nuntius mcp <nome>` | Configura servidor MCP |
| `nuntius tui` | Interface TUI avançada com painéis, temas e atalhos |
| `nuntius version` | Mostra a versão e banner |

## Comandos do Chat

| Comando | Descrição |
|---|---|
| `/exit` `/quit` `/sair` | Sai do chat |
| `/help` `/ajuda` | Mostra ajuda detalhada |
| `/clear` `/limpar` | Limpa o console |
| `/new` `/nova` | Inicia nova conversa |
| `/model` | Mostra provedor e modelo ativos |
| `/providers` | Lista todos os provedores disponíveis |
| `/skills` | Lista skills aprendidas |
| `/learn nome: instrucao` | Ensina uma nova skill |
| `/forget nome` | Remove uma skill |
| `/mcp` | Mostra status dos servidores MCP |

## Novidades

### Banner Interativo
Ao iniciar o Nuntius, um banner colorido com logotipo ASCII, informações do provedor/modelo ativo, versão e comandos úteis é exibido.

### Suporte a MCP (Model Context Protocol)
Conecte servidores MCP para estender as capacidades do agente com ferramentas externas. Configure no `config.yaml`:

```yaml
mcp_servers:
  meu_servidor:
    command: "python"
    args: ["-m", "meu_mcp_server"]
    enabled: true
```

### TUI Avancada (Textual)

Uma interface TUI moderna com painel dividido, temas customizaveis e atalhos de teclado.

```bash
pip install nuntius[tui]
nuntius tui
```

**Layout:**
- **Painel esquerdo (70%)**: Historico da conversa com mensagens do usuario, assistente e ferramentas
- **Painel direito (30%)**: Status do provedor/modelo, ferramentas disponiveis, estatisticas da sessao

**Atalhos:**
| Atalho | Acao |
|---|---|
| `Ctrl+P` | Configurar provedor/modelo |
| `Ctrl+T` | Listar ferramentas |
| `Ctrl+N` | Nova conversa |
| `Ctrl+L` | Limpar chat |
| `Ctrl+E` | Exportar conversa |
| `Ctrl+H` | Ajuda |
| `Ctrl+Q` | Sair |

**Temas:** 6 temas inclusos (Nuntius, Dracula, Monokai, Nord, Light, Gruvbox) com preview ao vivo. Use `/theme` no chat ou o atalho no seletor de temas.

### Provedores
Mais de 14 provedores suportados! Destaques:

| Provedor | Gratuito | Site |
|---|---|---|
| OpenAI | ❌ | platform.openai.com |
| DeepSeek | ❌ | platform.deepseek.com |
| Groq | ✅ | console.groq.com |
| Ollama (local) | ✅ | Localhost |
| NVIDIA NIM | ✅ | build.nvidia.com |
| GitHub Models | ✅ | github.com/marketplace/models |
| OpenRouter | ❌ | openrouter.ai |
| Google Gemini | ✅ | aistudio.google.com |
| Anthropic Claude | ❌ | console.anthropic.com |
| Fireworks AI | ✅ | fireworks.ai |

### Roteamento Inteligente por Modelo

Atribua diferentes modelos a diferentes tarefas automaticamente:

```yaml
# config.yaml
routing:
  enabled: true
  roles:
    code:
      provider: "deepseek"
      model: "deepseek-chat"
    search:
      provider: "groq"
      model: "llama3-70b-8192"
    writer:
      provider: "openai"
      model: "gpt-4o-mini"
```

**Como funciona:**
- O `RouteResolver` analisa a tarefa e identifica o role (code, search, writer, debug, etc.)
- O subagente é criado com o provedor/modelo específico do role
- Se desabilitado, usa o provedor/modelo global padrão

**Comandos:**
- `/routing` no chat TUI/CLI - mostra as rotas configuradas
- `set_route(role, provider, model)` - configura uma rota via ferramenta

**Funções pré-definidas:** code, shell, search, writer, debug, analysis, plan, review

## Ferramentas do Agente

O Nuntius possui ferramentas para:

- **Código**: run_python, run_javascript, run_shell, bash
- **Arquivos**: read, write, edit, grep, glob, ls, tree, delete, move, copy, organize, download
- **Web**: web_search, web_fetch
- **GitHub**: listar/criar issues, listar repositórios
- **Google Drive**: listar arquivos
- **Sistema**: calculator, current_time, system_info
- **MCP**: ferramentas carregadas de servidores externos

## Plataformas

O Nuntius suporta **12+ plataformas de mensageria** com uma arquitetura plugável. Cada plataforma é um adaptador independente que se registra automaticamente.

### Gateway Multi-Plataforma

| Plataforma | Tipo | Dependência | Ativação |
|---|---|---|---|
| Telegram | Bot | `python-telegram-bot` | `nuntius platform enable telegram` |
| Discord | Bot | `discord.py` | `nuntius platform enable discord` |
| Slack | Bot | `slack-bolt` | `nuntius platform enable slack` |
| WhatsApp | Cloud API | `aiohttp` | `nuntius platform enable whatsapp` |
| Matrix | Bot | `matrix-nio` | `nuntius platform enable matrix` |
| E-mail | IMAP/SMTP | (built-in) | `nuntius platform enable email` |
| Signal | signal-cli | `signal-cli` | `nuntius platform enable signal` |
| Microsoft Teams | Webhook | `aiohttp` | `nuntius platform enable teams` |
| Google Chat | Webhook | `aiohttp` | `nuntius platform enable googlechat` |
| LINE | Messaging API | `aiohttp` | `nuntius platform enable line` |
| IRC | Protocolo | `irctokens` | `nuntius platform enable irc` |
| Webhook Genérico | HTTP | `aiohttp` | `nuntius platform enable webhook` |
| GitHub | API Client | `PyGithub` | `nuntius platform enable github` |
| Google Drive | API Client | `google-*` | `nuntius platform enable drive` |

### Como usar

```bash
# Listar plataformas disponíveis
nuntius platform list

# Habilitar uma plataforma (o CLI pergunta as credenciais)
nuntius platform enable telegram

# Iniciar o gateway com todas as plataformas habilitadas
nuntius gateway
```

### Instalar dependências por plataforma

```bash
pip install nuntius[telegram]    # Apenas Telegram
pip install nuntius[discord]     # Apenas Discord
pip install nuntius[platforms]   # Todas as plataformas de mensageria
pip install nuntius[all]         # Tudo (incluindo MCP, browser, etc)
```

### Arquitetura

Cada plataforma estende `PlatformBase` e se autoregistra no registry. O Gateway descobre dinamicamente todos os adaptadores instalados e inicia apenas os habilitados no `config.yaml`. Adaptadores com dependências faltantes são ignorados graciosamente.

## Licença

MIT
