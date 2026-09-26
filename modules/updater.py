import requests
from modules.config import carregar_configuracao
from modules.logger import registrar_log

def verificar_atualizacoes():
    config = carregar_configuracao()
    url_check = f"{config.get('web_base_url')}/api/versao"
    try:
        res = requests.get(url_check, timeout=5)
        if res.status_code == 200:
            data = res.json()
            versao_remota = data.get("versao")
            if versao_remota != config.get("versao_atual"):
                return True, versao_remota
    except Exception as e:
        registrar_log(f"Erro ao verificar atualizações: {str(e)}", "AVISO")
    return False, config.get("versao_atual")
