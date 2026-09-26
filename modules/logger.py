import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def inicializar_logger():
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception:
            pass

def registrar_log(mensagem, tipo="INFO"):
    inicializar_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] [{tipo}] {mensagem}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linha)
    except Exception:
        pass
