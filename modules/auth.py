import platform
import subprocess
import hashlib
import json
import os
import time
import requests
from modules.logger import registrar_log
from modules.config import WEB_BASE_URL

SERVER_TOKEN_URL = f"{WEB_BASE_URL}/api/validar_token"
SESSION_FILE = os.path.join("config", "session.json")

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
                # Guarda a sessão localmente válida por 7 dias
                guardar_sessao_local(token, data)
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

def verificar_sessao_local():
    """Verifica se existe uma licença válida guardada no PC (válida por 7 dias offline)"""
    if not os.path.exists(SESSION_FILE):
        return False, None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        timestamp_salvo = dados.get("timestamp", 0)
        tempo_atual = time.time()
        sete_dias_em_segundos = 7 * 24 * 60 * 60  # 604800 segundos
        
        # Se ainda estiver dentro do prazo de 7 dias
        if (tempo_atual - timestamp_salvo) < sete_dias_em_segundos:
            registrar_log("Sessão carregada offline via cache local (Modo 7 dias).")
            return True, dados
    except Exception as e:
        registrar_log(f"Erro ao ler sessão local: {str(e)}", "AVISO")
    return False, None

def guardar_sessao_local(token, dados_servidor):
    """Guarda a sessão localmente com o carimbo de data/hora atual"""
    if not os.path.exists("config"):
        try:
            os.makedirs("config")
        except Exception:
            pass
            
    sessao = {
        "token": token,
        "usuario": dados_servidor.get("usuario", "Técnico"),
        "validade": dados_servidor.get("validade", "Ativa (Offline 7 dias)"),
        "timestamp": time.time()
    }
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(sessao, f, indent=4)
    except Exception as e:
        registrar_log(f"Erro ao gravar sessão local: {str(e)}", "ERRO")
