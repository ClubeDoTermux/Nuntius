# Nuntius AI

                    ╔╗╔┌─┐┌┬┐╔╦╗╔╗╔┬─┐╔╗
                    ║║║│ │ │ ║║║║║║║║║║
                    ║║║│ │ │ ║║║║║║║║║║
                    ╚╩╝└─┘ ┴ ╩╩╝╚╩╝└─┘╚╝

O Mensageiro da IA no Terminal — um agente de IA completo para Termux, Linux e macOS.

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
| `nuntius gateway` | Inicia o gateway para Telegram/Discord |
| `nuntius platform enable <nome>` | Habilita uma plataforma |
| `nuntius platform disable <nome>` | Desabilita uma plataforma |
| `nuntius mcp <nome>` | Configura servidor MCP |
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

| Plataforma | Comando para ativar |
|---|---|
| Telegram | `nuntius platform enable telegram` |
| Discord | `nuntius platform enable discord` |
| GitHub | `nuntius platform enable github` |
| Google Drive | `nuntius platform enable drive` |

## Licença

MIT
