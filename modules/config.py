import os
import json

# Configurações globais do sistema
WEB_BASE_URL = "https://elisiounlockmaster.onrender.com"
VERSAO_ATUAL = "v2.5.0"
MODO_DEV = False

CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_CONFIG = {
    "web_base_url": WEB_BASE_URL,
    "modo_desenvolvimento": MODO_DEV,
    "versao_atual": VERSAO_ATUAL
}

def carregar_configuracao():
    """Carrega as configurações locais ou retorna os valores padrão se o ficheiro não existir."""
    if not os.path.exists(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR)
        except Exception:
            pass
            
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception:
            pass
        return DEFAULT_CONFIG
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            # Garante que todas as chaves essenciais existem
            for chave, valor in DEFAULT_CONFIG.items():
                if chave not in dados:
                    dados[chave] = valor
            return dados
    except Exception:
        return DEFAULT_CONFIG

def salvar_configuracao(config):
    """Guarda as configurações no ficheiro JSON local."""
    if not os.path.exists(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR)
        except Exception:
            pass
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass
