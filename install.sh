#!/bin/bash
# ============================================================================
# Nuntius AI Installer
# ============================================================================
# Instalacao para Linux, macOS e Android/Termux.
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/ClubeDoTermux/Nuntius/main/install.sh | bash
#
# Opcoes:
#   --skip-setup   Pular configuracao interativa apos instalar
#   --branch NAME  Branch do git para instalar (default: main)
#   --help         Mostra esta ajuda
#
# ============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Config
REPO="ClubeDoTermux/Nuntius"
REPO_URL="https://github.com/${REPO}.git"
NUNTIUS_HOME="${NUNTIUS_HOME:-$HOME/.nuntius}"
INSTALL_DIR="${NUNTIUS_HOME}/nuntius"
BRANCH="main"
RUN_SETUP=true

# Detectar modo nao-interativo
if [ -t 0 ]; then
    IS_INTERACTIVE=true
else
    IS_INTERACTIVE=false
fi

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-setup) RUN_SETUP=false; shift ;;
        --branch) BRANCH="$2"; shift 2 ;;
        -h|--help)
            echo "Nuntius AI Installer"
            echo ""
            echo "Uso: install.sh [OPCOES]"
            echo ""
            echo "Opcoes:"
            echo "  --skip-setup  Pular configuracao interativa"
            echo "  --branch NAME Branch do git para instalar"
            echo "  -h, --help    Mostra esta ajuda"
            exit 0
            ;;
        *) echo "Opcao desconhecida: $1"; exit 1 ;;
    esac
done

# ============================================================================
# Funcoes auxiliares
# ============================================================================

print_banner() {
    echo ""
    echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ███╗   ██╗██╗   ██╗███╗   ██╗████████╗██╗██╗   ██╗███████╗"
    echo -e "${CYAN}  ████╗  ██║██║   ██║████╗  ██║╚══██╔══╝██║██║   ██║██╔════╝"
    echo -e "${CYAN}  ██╔██╗ ██║██║   ██║██╔██╗ ██║   ██║   ██║██║   ██║███████╗"
    echo -e "${CYAN}  ██║╚██╗██║██║   ██║██║╚██╗██║   ██║   ██║██║   ██║╚════██║"
    echo -e "${CYAN}  ██║ ╚████║╚██████╔╝██║ ╚████║   ██║   ██║╚██████╔╝███████║"
    echo -e "${CYAN}  ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═════╝ ╚══════╝"
    echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}              N U N T I U S   A I   v0.2.1${NC}"
    echo -e "${CYAN}         O Mensageiro da IA no Terminal${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${YELLOW}  █ Provedor: ${GREEN}OpenAI${NC}        ${YELLOW}█ Modelo: ${GREEN}gpt-4o-mini${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}github.com/ClubeDoTermux/Nuntius ${NC}"
    echo ""
}

log_info()    { echo -e "${CYAN}->${NC} $1"; }
log_success() { echo -e "${GREEN}ok${NC} $1"; }
log_warn()    { echo -e "${YELLOW}!!${NC} $1"; }
log_error()   { echo -e "${RED}XX${NC} $1"; }

is_termux() {
    [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"/com.termux/files/usr"* ]]
}

prompt_yes_no() {
    local question="$1"
    local default="${2:-yes}"
    local answer

    case "$default" in
        y|Y|yes|YES|1) prompt_suffix="[Y/n]" ;;
        *) prompt_suffix="[y/N]" ;;
    esac

    if [ "$IS_INTERACTIVE" = false ]; then
        case "$default" in y|Y|yes|YES|1) return 0 ;; *) return 1 ;; esac
    fi

    read -r -p "$question $prompt_suffix " answer || answer=""
    answer="${answer,,}"
    case "$answer" in
        y|yes|"") [ "$default" = "y" ] || [ "$default" = "Y" ] || [ "$default" = "yes" ] || [ "$default" = "YES" ] || [ "$default" = "1" ] ;;
        *) return 1 ;;
    esac
}

# ============================================================================
# Deteccao de SO
# ============================================================================

detect_os() {
    case "$(uname -s)" in
        Linux*)
            if is_termux; then
                OS="android"
                DISTRO="termux"
            else
                OS="linux"
                if [ -f /etc/os-release ]; then
                    . /etc/os-release
                    DISTRO="$ID"
                else
                    DISTRO="unknown"
                fi
            fi
            ;;
        Darwin*)
            OS="macos"
            DISTRO="macos"
            ;;
        *)
            OS="unknown"
            DISTRO="unknown"
            ;;
    esac
    log_success "Detectado: $OS ($DISTRO)"
}

# ============================================================================
# Verificacao de dependencias
# ============================================================================

check_git() {
    log_info "Verificando Git..."
    if command -v git &>/dev/null; then
        log_success "Git $(git --version | awk '{print $3}') encontrado"
        return 0
    fi

    if [ "$DISTRO" = "termux" ]; then
        log_info "Instalando Git via pkg..."
        pkg install -y git >/dev/null
        if command -v git &>/dev/null; then
            log_success "Git instalado"
            return 0
        fi
    fi

    log_error "Git nao encontrado. Instale o git e tente novamente."
    if [ "$DISTRO" = "termux" ]; then
        log_info "  pkg install git"
    elif [ "$OS" = "linux" ]; then
        log_info "  sudo apt install git  (ou use seu gerenciador de pacotes)"
    elif [ "$OS" = "macos" ]; then
        log_info "  brew install git"
    fi
    exit 1
}

check_python() {
    log_info "Verificando Python..."
    if command -v python3 &>/dev/null; then
        PYTHON="python3"
    elif command -v python &>/dev/null; then
        PYTHON="python"
    else
        PYTHON=""
    fi

    if [ -n "$PYTHON" ] && $PYTHON -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
        log_success "Python $($PYTHON --version 2>&1) encontrado"
        return 0
    fi

    if [ "$DISTRO" = "termux" ]; then
        log_info "Instalando Python via pkg..."
        pkg install -y python >/dev/null
        PYTHON="python3"
        log_success "Python $($PYTHON --version 2>&1) instalado"
        return 0
    fi

    log_error "Python 3.8+ nao encontrado. Instale o Python e tente novamente."
    if [ "$DISTRO" = "termux" ]; then
        log_info "  pkg install python"
    elif [ "$OS" = "linux" ]; then
        log_info "  sudo apt install python3 python3-pip python3-venv"
    elif [ "$OS" = "macos" ]; then
        log_info "  brew install python@3.11"
    fi
    exit 1
}

check_pip() {
    log_info "Verificando pip..."
    PIP=""
    if $PYTHON -m pip --version >/dev/null 2>&1; then
        PIP="$PYTHON -m pip"
    elif command -v pip3 &>/dev/null; then
        PIP="pip3"
    elif command -v pip &>/dev/null; then
        PIP="pip"
    fi

    if [ -z "$PIP" ]; then
        log_info "Instalando pip..."
        if [ "$DISTRO" = "termux" ]; then
            pkg install -y python-pip >/dev/null
        else
            $PYTHON -m ensurepip --upgrade >/dev/null 2>&1 || true
        fi
        PIP="$PYTHON -m pip"
    fi

    log_success "pip disponivel"
}

install_system_deps() {
    if [ "$DISTRO" = "termux" ]; then
        log_info "Instalando dependencias do sistema para Termux..."
        pkg install -y clang rust make pkg-config libffi openssl ca-certificates curl ripgrep 2>/dev/null || true
        log_success "Dependencias do Termux verificadas"
    fi
}

# ============================================================================
# Instalacao
# ============================================================================

clone_repo() {
    log_info "Instalando Nuntius em $INSTALL_DIR..."

    if [ -d "$INSTALL_DIR" ]; then
        log_info "Instalacao existente encontrada. Atualizando..."
        cd "$INSTALL_DIR"
        git fetch origin "$BRANCH"
        git checkout "$BRANCH"
        if ! git pull --ff-only origin "$BRANCH" 2>/dev/null; then
            log_warn "Resetando para origin/$BRANCH..."
            git reset --hard "origin/$BRANCH"
        fi
    else
        mkdir -p "$NUNTIUS_HOME"
        git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    fi
    log_success "Repositorio baixado em $INSTALL_DIR"
}

install_python_deps() {
    log_info "Instalando dependencias Python..."

    $PIP install --upgrade pip setuptools wheel 2>/dev/null || true

    # Tenta instalar com flags diferentes dependendo do sistema
    if $PIP install --break-system-packages -e "$INSTALL_DIR" 2>/dev/null; then
        :
    elif $PIP install -e "$INSTALL_DIR" 2>/dev/null; then
        :
    else
        $PIP install --user -e "$INSTALL_DIR"
    fi

    log_success "Dependencias Python instaladas"
}

create_command() {
    log_info "Configurando comando 'nuntius'..."

    local link_dir=""
    if [ "$DISTRO" = "termux" ] && [ -n "${PREFIX:-}" ]; then
        link_dir="$PREFIX/bin"
    elif [ "$(id -u)" -eq 0 ]; then
        link_dir="/usr/local/bin"
    else
        link_dir="$HOME/.local/bin"
    fi

    mkdir -p "$link_dir"
    local wrapper="$link_dir/nuntius"
    cat > "$wrapper" << 'WRAPPER'
#!/bin/sh
exec python3 -m nuntius "$@"
WRAPPER
    chmod +x "$wrapper"

    if [ "$DISTRO" = "termux" ]; then
        if ! grep -q "nuntius" "$HOME/.bashrc" 2>/dev/null; then
            echo 'alias nuntius="python3 -m nuntius"' >> "$HOME/.bashrc"
        fi
    fi

    log_success "Comando 'nuntius' disponivel em $link_dir"
    log_info "  Se necessario, adicione ao PATH: export PATH=\"\$PATH:$link_dir\""
}

run_setup_wizard() {
    if [ "$RUN_SETUP" = false ]; then
        log_info "Pulando configuracao (--skip-setup)"
        log_info "Execute 'nuntius setup' manualmente depois."
        return 0
    fi

    log_info "Iniciando configuracao..."
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${BOLD}  Configuracao do Nuntius${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    echo -e "Provedores disponiveis:"
    echo -e "  ${GREEN}openai${NC}     - OpenAI"
    echo -e "  ${GREEN}deepseek${NC}   - DeepSeek"
    echo -e "  ${GREEN}groq${NC}       - Groq (gratuito)"
    echo -e "  ${GREEN}ollama${NC}     - Ollama (local)"
    echo -e "  ${GREEN}nvidia${NC}     - NVIDIA NIM (gratuito)"
    echo -e "  ${GREEN}github${NC}     - GitHub Models (gratuito)"
    echo -e "  ${GREEN}openrouter${NC} - OpenRouter"
    echo -e "  ${GREEN}together${NC}   - Together AI"
    echo -e "  ${GREEN}mistral${NC}    - Mistral AI"
    echo -e "  ${GREEN}xai${NC}        - xAI (Grok)"
    echo -e "  ${GREEN}perplexity${NC} - Perplexity"
    echo -e "  ${GREEN}fireworks${NC}  - Fireworks AI (gratuito)"
    echo ""

    read -r -p "Digite o codigo do provedor (default: openai): " provider
    provider="${provider:-openai}"
    model=""
    case "$provider" in
        deepseek) model="deepseek-chat" ;;
        groq) model="llama3-70b-8192" ;;
        ollama) model="llama3.2" ;;
        nvidia) model="nvidia/llama-3.1-nemotron-70b-instruct" ;;
        github) model="gpt-4o-mini" ;;
        openrouter) model="openai/gpt-4o-mini" ;;
        together) model="meta-llama/Llama-3.3-70B-Instruct-Turbo" ;;
        mistral) model="mistral-small-latest" ;;
        xai) model="grok-beta" ;;
        perplexity) model="sonar-pro" ;;
        fireworks) model="accounts/fireworks/models/llama-v3p3-70b-instruct" ;;
        *) provider="openai"; model="gpt-4o-mini" ;;
    esac

    api_key=""
    if [ "$provider" != "ollama" ]; then
        echo ""
        read -r -p "Digite sua API Key (deixe vazio para configurar depois): " api_key
    fi

    echo ""
    echo -e "${CYAN}Configurando...${NC}"

    # Salva a configuracao via Python
    $PYTHON -c "
import os, yaml
from pathlib import Path

config_dir = Path(os.environ.get('NUNTIUS_CONFIG_DIR', str(Path.home() / '.config' / 'nuntius')))
config_path = config_dir / 'config.yaml'
config_dir.mkdir(parents=True, exist_ok=True)

defaults = {
    'provider': '$provider',
    'model': '$model',
    'providers': {
        'openai': {'api_key': '', 'base_url': 'https://api.openai.com/v1'},
        'deepseek': {'api_key': '', 'base_url': 'https://api.deepseek.com/v1'},
        'groq': {'api_key': '', 'base_url': 'https://api.groq.com/openai/v1'},
        'ollama': {'api_key': '', 'base_url': 'http://localhost:11434/v1'},
        'nvidia': {'api_key': '', 'base_url': 'https://integrate.api.nvidia.com/v1'},
        'github': {'api_key': '', 'base_url': 'https://models.inference.ai.azure.com'},
        'openrouter': {'api_key': '', 'base_url': 'https://openrouter.ai/api/v1'},
        'together': {'api_key': '', 'base_url': 'https://api.together.xyz/v1'},
        'mistral': {'api_key': '', 'base_url': 'https://api.mistral.ai/v1'},
        'xai': {'api_key': '', 'base_url': 'https://api.x.ai/v1'},
        'perplexity': {'api_key': '', 'base_url': 'https://api.perplexity.ai'},
        'fireworks': {'api_key': '', 'base_url': 'https://api.fireworks.ai/inference/v1'},
    },
    'platforms': {
        'telegram': {'enabled': False, 'token': ''},
        'discord': {'enabled': False, 'token': ''},
        'github': {'enabled': False, 'token': ''},
        'drive': {'enabled': False, 'credentials_path': ''},
    },
    'security': {'bash_approval': True},
    'auto_learn': {'enabled': True},
    'memory': {'enabled': True},
    'tools': {'enabled': True},
}

if config_path.exists():
    with open(config_path) as f:
        existing = yaml.safe_load(f) or {}
else:
    existing = {}

cfg = {**defaults, **existing}
cfg['provider'] = '$provider'
cfg['model'] = '$model'
if '$api_key':
    cfg['providers']['$provider']['api_key'] = '$api_key'

with open(config_path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)

print(f'Configuracao salva em {config_path}')
"

    log_success "Configuracao concluida!"
    echo ""
    echo -e "${GREEN}Para comecar, execute: nuntius${NC}"
}

# ============================================================================
# Main
# ============================================================================

main() {
    print_banner
    detect_os
    check_git
    check_python
    check_pip
    install_system_deps
    clone_repo
    install_python_deps
    create_command
    run_setup_wizard

    echo ""
    echo -e "${GREEN}${BOLD}  Instalacao concluida!${NC}"
    echo ""
    echo -e "  ${CYAN}->${NC} Execute ${BOLD}nuntius${NC} para comecar"
    echo -e "  ${CYAN}->${NC} ${BOLD}nuntius setup${NC} para reconfigurar"
    echo -e "  ${CYAN}->${NC} ${BOLD}nuntius --help${NC} para ver todos os comandos"
    echo ""
}

main "$@"
