import subprocess
import sys
import os
from modules.logger import registrar_log

def obter_caminho_fastboot():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, 'bin', 'fastboot.exe' if os.name == 'nt' else 'fastboot')

def executar_fastboot(args):
    fb_path = obter_caminho_fastboot()
    cmd = f'"{fb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        saida = res.decode('utf-8', errors='ignore').strip()
        registrar_log(f"Fastboot Executado: {args}")
        return saida
    except subprocess.TimeoutExpired:
        registrar_log(f"Timeout no comando Fastboot: {args}", "ERRO")
        return "Erro: Timeout na execução do Fastboot."
    except Exception as e:
        registrar_log(f"Erro Fastboot ({args}): {str(e)}", "ERRO")
        return f"Erro de Execução Fastboot: {str(e)}"
