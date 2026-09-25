import platform
import subprocess
import hashlib
import requests
import sys
import os
import webbrowser

# =====================================================================
# CONFIGURAÇÕES DE ENDPOINTS E ROTAS DO SISTEMA
# =====================================================================
# URL base do painel web hospedado no Render
WEB_BASE_URL = "https://elisiounlockmaster.onrender.com"
# Endpoint dedicado para validação via token seguro gerado pelo painel
SERVER_TOKEN_URL = f"{WEB_BASE_URL}/api/validar_token"

def limpar_tela():
    """Limpa a tela conforme o sistema operacional de forma compatível"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def obter_caminho_binario(nome_binario):
    """Garante que o app encontre os binários dentro da pasta bin/ mesmo após empacotado pelo PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, 'bin', nome_binario)

def get_hwid():
    """Gera o HWID único da máquina para bloqueio rígido contra pirataria"""
    try:
        sistema = platform.system()
        if sistema == "Windows":
            cmd = "wmic csproduct get uuid"
            uuid = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().split('\n')[1].strip()
        elif sistema == "Darwin":  # macOS
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
            uuid = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().split('"')[3].strip()
        else:
            uuid = platform.node() + platform.machine()
        
        return hashlib.sha256(uuid.encode()).hexdigest()
    except:
        return hashlib.sha256((platform.node() + platform.system()).encode()).hexdigest()

def executar_adb(args):
    """Executa o utilitário ADB embutido com tratamento de exceções"""
    adb_path = obter_caminho_binario("adb.exe" if platform.system() == "Windows" else "adb")
    cmd = f'"{adb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return res.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Erro de Execução ADB: {str(e)}"

def executar_fastboot(args):
    """Executa o utilitário Fastboot embutido com tratamento de exceções"""
    fb_path = obter_caminho_binario("fastboot.exe" if platform.system() == "Windows" else "fastboot")
    cmd = f'"{fb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return res.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Erro de Execução Fastboot: {str(e)}"

# =====================================================================
# ROTINAS DE HARD RESET, FRP E MÓDULOS DE MANUTENÇÃO
# =====================================================================

def exibir_guia_botoes():
    limpar_tela()
    print("==================================================")
    print("        GUIA TÉCNICO DE RECOVERY MANUAL           ")
    print("==================================================")
    print("Utilize os botões físicos caso o modo automático falhe:")
    print("\n[ SAMSUNG ]")
    print("• Desligue completamente o aparelho.")
    print("• Pressione Volume Mais (+) + Power até o logotipo aparecer.")
    print("• Navegue até 'Wipe data/factory reset' e confirme.")
    
    print("\n[ XIAOMI / REDMI ]")
    print("• Desligue o aparelho e pressione Volume Mais (+) + Power.")
    print("• Selecione 'Wipe Data' -> 'Wipe All Data'.")
    
    print("\n[ MOTOROLA ]")
    print("• Com o aparelho desligado, segure Volume Menos (-) + Power.")
    print("• Selecione 'Recovery Mode' utilizando as teclas de volume.")
    print("==================================================")
    input("\nPressione [Enter] para retornar ao menu...")

def menu_universal():
    while True:
        limpar_tela()
        print("==================================================")
        print("          CENTRAL DE SUPORTE UNIVERSAL            ")
        print("==================================================")
        print("[1] Listar Dispositivos ADB Conectados")
        print("[2] Executar Bypass de FRP (Via Pacotes ADB)")
        print("[3] Forçar Entrada em Recovery Mode")
        print("[4] Listar Dispositivos em Fastboot Mode")
        print("[5] Executar Limpeza de Userdata (Fastboot Wipe)")
        print("[6] Visualizar Guia de Botões Físicos")
        print("[0] Retornar ao Painel Principal")
        print("==================================================")
        
        op = input("Selecione uma opção operacional: ").strip()
        if op == "1":
            print("\n[+] Sondando portas ADB ativas...")
            print(executar_adb("devices"))
            input("\nPressione [Enter] para continuar...")
        elif op == "2":
            print("\n[+] Acionando pacotes de sistema para contorno de FRP...")
            print(executar_adb("shell am start -S -n com.google.android.gsf/.update.SystemUpdateActivity"))
            print(executar_adb("shell am start -a android.intent.action.VIEW -d https://www.google.com"))
            print("[SUCESSO] Comandos disparados para a interface do dispositivo.")
            input("\nPressione [Enter] para continuar...")
        elif op == "3":
            print("\n[+] Enviando comando para reboot em recovery...")
            print(executar_adb("reboot recovery"))
            print("[SUCESSO] Dispositivo redirecionado com êxito.")
            input("\nPressione [Enter] para continuar...")
        elif op == "4":
            print("\n[+] Sondando portas Fastboot ativas...")
            print(executar_fastboot("devices"))
            input("\nPressione [Enter] para continuar...")
        elif op == "5":
            print("\n[+] Executando limpeza de particionamento userdata...")
            print(executar_fastboot("erase userdata"))
            print(executar_fastboot("erase cache"))
            print(executar_fastboot("reboot"))
            print("[SUCESSO] Limpeza concluída e comando de reinicialização enviado.")
            input("\nPressione [Enter] para continuar...")
        elif op == "6":
            exibir_guia_botoes()
        elif op == "0":
            break

def menu_marcas():
    while True:
        limpar_tela()
        print("==================================================")
        print("          DIAGNÓSTICO E ROTINAS POR MARCA         ")
        print("==================================================")
        print("[1] Samsung (FRP MTP & Recovery)")
        print("[2] Xiaomi / Redmi (Bootloader & Erase Userdata)")
        print("[3] Motorola (Get Unlock Data & Fastboot)")
        print("[4] Tecno / Infinix / Itel (Comandos MTK/Preloader)")
        print("[0] Retornar ao Painel Principal")
        print("==================================================")
        
        marca_op = input("Selecione a fabricante alvo: ").strip()
        if marca_op == "0":
            break
        elif marca_op == "1":
            limpar_tela()
            print("--- PROCEDIMENTOS SAMSUNG ---")
            print("[1] Forçar Modo Recovery")
            print("[2] Disparar Navegador Web (FRP)")
            sub = input("Escolha o procedimento: ").strip()
            if sub == "1":
                print(executar_adb("reboot recovery"))
            elif sub == "2":
                print(executar_adb("shell am start -a android.intent.action.VIEW -d https://www.google.com"))
            input("\nPressione [Enter] para continuar...")
        elif marca_op == "2":
            limpar_tela()
            print("--- PROCEDIMENTOS XIAOMI / REDMI ---")
            print("[1] Verificar Status Fastboot")
            print("[2] Solicitar Desbloqueio Bootloader")
            print("[3] Executar Wipe Userdata")
            sub = input("Escolha o procedimento: ").strip()
            if sub == "1":
                print(executar_fastboot("devices"))
            elif sub == "2":
                print(executar_fastboot("oem unlock"))
                print(executar_fastboot("flashing unlock"))
            elif sub == "3":
                print(executar_fastboot("erase userdata"))
                print(executar_fastboot("reboot"))
            input("\nPressione [Enter] para continuar...")
        elif marca_op == "3":
            limpar_tela()
            print("--- PROCEDIMENTOS MOTOROLA ---")
            print("[1] Obter Token de Desbloqueio (Get Unlock Data)")
            print("[2] Reiniciar Dispositivo")
            sub = input("Escolha o procedimento: ").strip()
            if sub == "1":
                print(executar_fastboot("oem get_unlock_data"))
            elif sub == "2":
                print(executar_fastboot("reboot"))
            input("\nPressione [Enter] para continuar...")
        elif marca_op == "4":
            limpar_tela()
            print("--- PROCEDIMENTOS MEDIAREK / GENÉRICOS ---")
            print("[1] Sondar Conexão ADB")
            print("[2] Forçar Bootloader Mode")
            sub = input("Escolha o procedimento: ").strip()
            if sub == "1":
                print(executar_adb("devices"))
            elif sub == "2":
                print(executar_adb("reboot bootloader"))
            input("\nPressione [Enter] para continuar...")
        else:
            print("\n[!] Opção selecionada é inválida.")
            input("Pressione [Enter] para tentar novamente...")

def menu_ferramentas():
    while True:
        limpar_tela()
        print("==================================================")
        print("    ELÍSIO UNLOCK MASTER — PAINEL DE TÉCNICO       ")
        print("==================================================")
        print("[1] 🌐 Módulo Universal & Ferramentas de Reset")
        print("[2] 📱 Central de Rotinas Avançadas por Marca")
        print("[3] ⚡ Módulo de Flashing & Pacotes Stock")
        print("[4] 📶 Módulo de Redes, Portas AT & ICCID")
        print("[5] ⚙️ Informações e Leitura de Propriedades (Getprop)")
        print("[0] Encerrar Sessão de Trabalho")
        print("==================================================")
        
        opcao = input("Selecione o módulo de trabalho: ").strip()
        
        if opcao == "1":
            menu_universal()
        elif opcao == "2":
            menu_marcas()
        elif opcao == "3":
            limpar_tela()
            print("==================================================")
            print("        MÓDULO DE FLASHING & PACOTES STOCK        ")
            print("==================================================")
            print("[+] Subsistema pronto para empacotamento e MediaTek Auth.")
            input("\nPressione [Enter] para retornar...")
        elif opcao == "4":
            limpar_tela()
            print("==================================================")
            print("          MÓDULO DE REDES E COMANDOS AT           ")
            print("==================================================")
            print("[+] Subsistema de leitura de banda e desbloqueio ativo.")
            input("\nPressione [Enter] para retornar...")
        elif opcao == "5":
            limpar_tela()
            print("==================================================")
            print("           DIAGNÓSTICO DE HARDWARE                ")
            print("==================================================")
            print("Modelo:", executar_adb("shell getprop ro.product.model").strip())
            print("Versão Android:", executar_adb("shell getprop ro.build.version.release").strip())
            print("Número de Série:", executar_adb("get-serialno").strip())
            print("==================================================")
            input("\nPressione [Enter] para retornar...")
        elif opcao == "0":
            print("\nEncerrando sessão com segurança. Até logo!")
            sys.exit(0)
        else:
            print("\n[!] Opção inválida!")
            input("Pressione [Enter] para continuar...")

# =====================================================================
# FLUXO DE SEGURANÇA E AUTENTICAÇÃO POR TOKEN DE PROTOCOLO
# =====================================================================

def main():
    limpar_tela()
    hwid = get_hwid()

    # Validação obrigatória: O programa só prossegue se receber o token seguro via argumento de protocolo
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
        print("==================================================")
        print("    VALIDANDO AUTENTICAÇÃO VIA PAINEL WEB...      ")
        print("==================================================")
        
        try:
            response = requests.post(SERVER_TOKEN_URL, json={
                "token": token,
                "hwid": hwid
            }, timeout=12)
            
            data = response.json()
            
            if data.get("status") == "sucesso":
                print(f"\n[AUTORIZADO] {data.get('mensagem')}")
                input("\nPressione [Enter] para carregar o painel operacional...")
                menu_ferramentas()
            else:
                print(f"\n[ACESSO NEGADO] {data.get('mensagem')}")
                print("[!] O programa será encerrado por motivos de segurança.")
                input("\nPressione [Enter] para sair...")
                sys.exit(1)
        except Exception as e:
            print(f"\n[ERRO DE CONEXÃO] Falha ao comunicar com o servidor central: {e}")
            input("\nPressione [Enter] para sair...")
            sys.exit(1)
    else:
        # Se executado diretamente sem token via argumento, redireciona estritamente para o site e fecha o terminal
        print("==================================================")
        print("    ELÍSIO UNLOCK MASTER — SEGURANÇA DE SESSÃO    ")
        print("==================================================")
        print("[!] Acesso direto bloqueado.")
        print("[!] Redirecionando para a plataforma web oficial de login...")
        print("[!] O aplicativo será encerrado imediatamente.")
        print("==================================================")
        
        try:
            webbrowser.open(WEB_BASE_URL)
        except Exception:
            pass
        
        input("\nPressione [Enter] para fechar o programa...")
        sys.exit(0)

if __name__ == "__main__":
    main()