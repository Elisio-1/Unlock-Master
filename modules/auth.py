import platform
import subprocess
import hashlib
import requests
from modules.logger import registrar_log
from modules.config import carregar_configuracao

config = carregar_configuracao()
WEB_BASE_URL = config.get("web_base_url")
SERVER_TOKEN_URL = f"{WEB_BASE_URL}/api/validar_token"

def get_hwid():
    """Gera o HWID único da máquina para bloqueio rígido contra pirataria"""
    try:
        sistema = platform.system()
        if sistema == "Windows":
            cmd = "wmic csproduct get uuid"
            uuid = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().split('\n')[1].strip()
        elif sistema == "Darwin":
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
            uuid = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().split('"')[3].strip()
        else:
            uuid = platform.node() + platform.machine()
        return hashlib.sha256(uuid.encode()).hexdigest()
    except Exception as e:
        registrar_log(f"Erro ao gerar HWID: {str(e)}", "ERRO")
        return hashlib.sha256((platform.node() + platform.system()).encode()).hexdigest()

def validar_token_servidor(token):
    hwid = get_hwid()
    try:
        response = requests.post(SERVER_TOKEN_URL, json={
            "token": token,
            "hwid": hwid
        }, timeout=12)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "sucesso":
                registrar_log(f"Sessão autorizada para: {data.get('usuario')}")
                return True, data
            else:
                registrar_log(f"Acesso negado pelo servidor: {data.get('mensagem')}", "AVISO")
                return False, data.get("mensagem")
        else:
            registrar_log(f"Falha HTTP ao validar token: {response.status_code}", "ERRO")
            return False, "Erro de comunicação com o servidor central."
    except requests.exceptions.Timeout:
        registrar_log("Timeout na conexão com o servidor de licenças.", "ERRO")
        return False, "Tempo limite excedido ao contactar o servidor."
    except requests.exceptions.ConnectionError:
        registrar_log("Erro de rede: Sem conexão com a internet.", "ERRO")
        return False, "Sem ligação à internet."
    except Exception as e:
        registrar_log(f"Exceção crítica na autenticação: {str(e)}", "ERRO")
        return False, f"Erro crítico: {str(e)}"
