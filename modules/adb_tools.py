import subprocess
import sys
import os
from modules.logger import registrar_log

def obter_caminho_adb():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, 'bin', 'adb.exe' if os.name == 'nt' else 'adb')

def executar_adb(args):
    adb_path = obter_caminho_adb()
    cmd = f'"{adb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        saida = res.decode('utf-8', errors='ignore').strip()
        registrar_log(f"ADB Executado: {args}")
        return saida
    except subprocess.TimeoutExpired:
        registrar_log(f"Timeout no comando ADB: {args}", "ERRO")
        return "Erro: Timeout na execução do ADB."
    except Exception as e:
        registrar_log(f"Erro ADB ({args}): {str(e)}", "ERRO")
        return f"Erro de Execução ADB: {str(e)}"
