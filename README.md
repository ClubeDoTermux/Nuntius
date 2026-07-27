# Nuntius AI

Um agente de IA completo para rodar no Termux (e outros terminais).

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
| `nuntius` | Inicia o chat interativo |
| `nuntius setup` | Configura provedor, modelo e API Key |
| `nuntius run <mensagem>` | Executa uma mensagem única e sai |
| `nuntius model` | Mostra/altera o provedor e modelo ativos |
| `nuntius gateway` | Inicia o gateway para Telegram/Discord |
| `nuntius platform enable <nome>` | Habilita uma plataforma (telegram, discord, github, drive) |
| `nuntius platform disable <nome>` | Desabilita uma plataforma |
| `nuntius version` | Mostra a versão instalada |

## Comandos do Chat

| Comando | Descrição |
|---|---|
| `/exit` ou `/sair` | Sai do chat |
| `/help` ou `/ajuda` | Mostra ajuda |
| `/clear` ou `/limpar` | Limpa o console |
| `/new` ou `/nova` | Inicia nova conversa |
| `/model` | Mostra provedor e modelo ativos |
| `/providers` | Lista todos os provedores disponíveis |
| `/skills` | Lista skills aprendidas pelo agente |
| `/learn nome: instrucao` | Ensina uma nova skill ao agente |
| `/forget nome` | Remove uma skill aprendida |

## Ferramentas do Agente

### Código e Sistema

| Ferramenta | Descrição |
|---|---|
| `calculator` | Executa operações matemáticas |
| `run_python` | Executa código Python em ambiente isolado |
| `run_javascript` | Executa código JavaScript (requer Node.js) |
| `run_shell` | Executa comando no shell (requer aprovação) |
| `shell` | Atalho para run_shell |
| `bash` | Executa comando no terminal |
| `system_info` | Mostra informações do dispositivo |

### Arquivos

| Ferramenta | Descrição |
|---|---|
| `read` | Lê o conteúdo de um arquivo |
| `write` | Escreve conteúdo em um arquivo |
| `edit` | Edita um arquivo substituindo trechos de texto |
| `grep` | Procura texto em arquivos usando regex |
| `glob` | Busca arquivos por padrão (ex: `**/*.py`) |
| `ls` | Lista arquivos em um diretório |
| `tree` | Mostra a árvore de diretórios |
| `delete` | Exclui permanentemente arquivo/diretório |
| `move` | Move ou renomeia arquivo/diretório |
| `copy` | Copia arquivo ou diretório |
| `organize` | Organiza arquivos por tipo/extensão |
| `download` | Baixa um arquivo da internet |

### Web

| Ferramenta | Descrição |
|---|---|
| `web_search` | Pesquisa na web |
| `web_fetch` | Obtém o conteúdo de uma URL |

### GitHub

| Ferramenta | Descrição |
|---|---|
| `github_list_repos` | Lista seus repositórios |
| `github_create_issue` | Cria uma issue |
| `github_list_issues` | Lista issues de um repositório |

### Google Drive

| Ferramenta | Descrição |
|---|---|
| `drive_list_files` | Lista arquivos do Google Drive |

## Provedores Suportados

| Provedor | Gratuito | Site |
|---|---|---|
| OpenAI | ❌ | platform.openai.com |
| DeepSeek | ❌ | platform.deepseek.com |
| Groq | ✅ | console.groq.com |
| Ollama (local) | ✅ | Localhost |
| NVIDIA NIM | ✅ | build.nvidia.com |
| GitHub Models | ✅ | github.com/marketplace/models |
| OpenRouter | ❌ | openrouter.ai |
| Together AI | ❌ | together.ai |
| Mistral AI | ❌ | mistral.ai |
| xAI (Grok) | ❌ | x.ai |
| Perplexity | ❌ | perplexity.ai |
| Fireworks AI | ✅ | fireworks.ai |

## Plataformas

| Plataforma | Comando para ativar |
|---|---|
| Telegram | `nuntius platform enable telegram` |
| Discord | `nuntius platform enable discord` |
| GitHub | `nuntius platform enable github` |
| Google Drive | `nuntius platform enable drive` |
