# Nuntius AI

Um agente de IA completo para rodar no Termux (e outros terminais).

## Instalação no Termux

```bash
pkg update && pkg upgrade
pkg install python git
pip install nuntius
```

Ou instalacao local:

```bash
git clone https://github.com/SEU_USUARIO/Nuntius.git
cd Nuntius
pip install -e .
```

## Uso

```bash
# Configurar (primeiro uso)
nuntius setup

# Iniciar chat interativo
nuntius

# Executar mensagem unica
nuntius run "Qual a capital do Brasil?"

# Gateway para Telegram/Discord
nuntius gateway
```

## Configuracao

Suporta OpenAI, DeepSeek, Groq, Ollama e qualquer API compatível com OpenAI.

```bash
nuntius setup
```

## Provedores gratuitos

- **Groq** - gratuito, modelos Llama 3
- **Ollama** - local, 100% gratuito
