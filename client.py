import platform
import subprocess
import hashlib
import requests
import sys
import os
import time
import json
import threading
import customtkinter as ctk

# ==========================================
# CONFIGURAÇÕES DO SERVIDOR (Render)
# ==========================================
SERVER_URL = "https://elisiounlockmaster.onrender.com/api/validar_hwid"
SESSION_FILE = os.path.join("config", "session.json")
VERSAO_ATUAL = "v2.5.0"

# ==========================================
# FUNÇÕES DE HARDWARE, ADB E FASTBOOT
# ==========================================
def obter_caminho_binario(nome_binario):
    """Garante que o app encontre os binários dentro da pasta bin/ mesmo após compilado"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, 'bin', nome_binario)

def get_hwid():
    """Gera o HWID único da máquina para bloqueio de pirataria"""
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
    except:
        return hashlib.sha256((platform.node() + platform.system()).encode()).hexdigest()

def executar_adb(args):
    adb_path = obter_caminho_binario("adb.exe" if platform.system() == "Windows" else "adb")
    cmd = f'"{adb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=12)
        return res.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return f"Erro: {str(e)}"

def executar_fastboot(args):
    fb_path = obter_caminho_binario("fastboot.exe" if platform.system() == "Windows" else "fastboot")
    cmd = f'"{fb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=12)
        return res.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return f"Erro: {str(e)}"

# ==========================================
# GESTÃO DE SESSÃO LOCAL (7 Dias Offline)
# ==========================================
def verificar_sessao_7_dias():
    """Permite abrir o programa offline durante 7 dias sem gastar internet"""
    if not os.path.exists(SESSION_FILE):
        return False, None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        timestamp_salvo = dados.get("timestamp", 0)
        if (time.time() - timestamp_salvo) < (7 * 24 * 60 * 60):
            return True, dados.get("username", "Técnico")
    except:
        pass
    return False, None

def guardar_sessao_local(username):
    if not os.path.exists("config"):
        try:
            os.makedirs("config")
        except:
            pass
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": username, "timestamp": time.time()}, f, indent=4)
    except:
        pass


# ==========================================
# INTERFACE GRÁFICA MODERNA (BANCADA)
# ==========================================
class ElisioUnlockMasterApp(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title(f"Elísio Unlock Master — Painel do Técnico ({VERSAO_ATUAL})")
        self.geometry("1150x720")
        self.minsize(980, 600)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Centralizar na tela
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.criar_barra_lateral()
        self.criar_painel_principal()
        
        # Monitor USB em segundo plano
        self.ativo = True
        threading.Thread(target=self.loop_monitoramento_usb, daemon=True).start()

    def criar_barra_lateral(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="⚡ ELÍSIO MASTER", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkLabel(info_frame, text=f"👤 {self.username}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="🛡️ Sessão Ativa (7d Offline)", font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(anchor="w")
        
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#34495e").grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        
        # Botões de Abas da Bancada
        ctk.CTkButton(self.sidebar, text="🌐 Módulo Universal & FRP", command=lambda: self.mudar_aba("universal")).grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="📱 Rotinas por Marca", command=lambda: self.mudar_aba("marcas")).grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚡ Flashing & Fastboot", command=lambda: self.mudar_aba("flash")).grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="📖 Guia Manual (Botões)", command=lambda: self.mudar_aba("guia")).grid(row=6, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚙️ Informações do Aparelho", command=lambda: self.mudar_aba("info")).grid(row=7, column=0, padx=20, pady=8, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="Encerrar Sistema", fg_color="#c0392b", hover_color="#e74c3c", command=self.fechar_sistema).grid(row=9, column=0, padx=20, pady=20, sticky="ew")

    def criar_painel_principal(self):
        self.main_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_panel.grid(row=0, column=1, sticky="nsew")
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)
        
        # Header de Estado USB
        self.header_frame = ctk.CTkFrame(self.main_panel, height=60, fg_color="#262626")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        self.lbl_status_device = ctk.CTkLabel(self.header_frame, text="🔌 Aguardando dispositivo na porta USB...", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f1c40f")
        self.lbl_status_device.pack(side="left", padx=20, pady=15)
        
        # Conteúdo Dinâmico + Consola
        self.content_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.frame_botoes = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.frame_botoes.grid(row=0, column=0, sticky="nsew")
        
        # Consola Verde Integrada
        log_container = ctk.CTkFrame(self.content_frame)
        log_container.grid(row=1, column=0, sticky="nsew", pady=(15, 0))
        self.txt_log = ctk.CTkTextbox(log_container, fg_color="#0d0d0d", text_color="#00ff00", font=ctk.CTkFont(family="Consolas", size=13))
        self.txt_log.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.escrever_log(f"[{time.strftime('%H:%M:%S')}] Elísio Unlock Master carregado com sucesso.")
        self.mudar_aba("universal")

    def limpar_botoes(self):
        for widget in self.frame_botoes.winfo_children():
            widget.destroy()

    def mudar_aba(self, nome):
        self.limpar_botoes()
        if nome == "universal":
            self.aba_universal()
        elif nome == "marcas":
            self.aba_marcas()
        elif nome == "flash":
            self.aba_flash()
        elif nome == "guia":
            self.aba_guia()
        elif nome == "info":
            self.aba_info()

    def escrever_log(self, texto):
        self.txt_log.insert("end", str(texto) + "\n")
        self.txt_log.see("end")

    # --- IMPLEMENTAÇÃO DAS ABAS DE BANCADA ---
    def aba_universal(self):
        ctk.CTkLabel(self.frame_botoes, text="Módulo Universal Android & Hard Reset", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        r1 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r1.pack(fill="x", pady=5)
        ctk.CTkButton(r1, text="Listar Dispositivos ADB", command=lambda: self.escrever_log(executar_adb("devices"))).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Remover FRP (ADB Direto)", fg_color="#d35400", hover_color="#e67e22", command=self.acao_frp).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Forçar Recovery Mode", command=lambda: self.escrever_log(executar_adb("reboot recovery"))).pack(side="left", padx=5)

    def aba_marcas(self):
        ctk.CTkLabel(self.frame_botoes, text="Rotinas Avançadas por Fabricante", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        r1 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r1.pack(fill="x", pady=5)
        self.combo_marca = ctk.CTkComboBox(r1, values=["Samsung", "Xiaomi / Redmi", "Motorola", "Tecno / Infinix / Itel"], width=220)
        self.combo_marca.pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Executar Rotina da Marca", command=self.acao_marca).pack(side="left", padx=10)

    def aba_flash(self):
        ctk.CTkLabel(self.frame_botoes, text="Módulo Fastboot & Limpeza de Dados", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        r1 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r1.pack(fill="x", pady=5)
        ctk.CTkButton(r1, text="Listar Fastboot Devices", command=lambda: self.escrever_log(executar_fastboot("devices"))).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Wipe Userdata (Hard Reset)", fg_color="#c0392b", hover_color="#e74c3c", command=self.acao_wipe).pack(side="left", padx=5)

    def aba_guia(self):
        ctk.CTkLabel(self.frame_botoes, text="Guia de Hard Reset Manual por Botões Físicos", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 5))
        texto_guia = (
            "[ SAMSUNG ] Segure Volume Mais (+) + Power até a logo -> Wipe data/factory reset.\n"
            "[ XIAOMI / REDMI ] Segure Volume Mais (+) + Power -> Wipe Data -> Wipe All Data.\n"
            "[ MOTOROLA ] Segure Volume Menos (-) + Power -> Recovery Mode -> Power + Vol Mais.\n"
            "[ TECNO / INFINIX ] Segure Volume Mais (+) + Power -> Solte Power na logo."
        )
        lbl = ctk.CTkLabel(self.frame_botoes, text=texto_guia, justify="left", font=ctk.CTkFont(size=12), text_color="#bdc3c7")
        lbl.pack(anchor="w", padx=5, pady=5)

    def aba_info(self):
        ctk.CTkLabel(self.frame_botoes, text="Informações Completas do Aparelho", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkButton(self.frame_botoes, text="Ler Getprop do Dispositivo", command=self.acao_info).pack(anchor="w", padx=5, pady=5)

    # --- AÇÕES DOS BOTÕES DE BANCADA ---
    def acao_frp(self):
        self.escrever_log("\n[+] Executando bypass de FRP via pacotes de sistema...")
        self.escrever_log(executar_adb("shell am start -S -n com.google.android.gsf/.update.SystemUpdateActivity"))
        self.escrever_log(executar_adb("shell am start -a android.intent.action.VIEW -d https://www.google.com"))

    def acao_wipe(self):
        self.escrever_log("\n[+] Executando limpeza de userdata via Fastboot...")
        self.escrever_log(executar_fastboot("erase userdata"))
        self.escrever_log(executar_fastboot("erase cache"))
        self.escrever_log(executar_fastboot("reboot"))
        self.escrever_log("[+] Processo concluído.")

    def acao_info(self):
        self.escrever_log("\n--- DIAGNÓSTICO DO APARELHO ---")
        self.escrever_log("Modelo: " + executar_adb("shell getprop ro.product.model"))
        self.escrever_log("Android: " + executar_adb("shell getprop ro.build.version.release"))
        self.escrever_log("Serial: " + executar_adb("get-serialno"))

    def acao_marca(self):
        marca = self.combo_marca.get()
        self.escrever_log(f"\n[+] A aplicar rotina para: {marca}")
        if "Samsung" in marca:
            self.escrever_log(executar_adb("shell am start -a android.intent.action.DIAL -d tel:%2A%230%2A%23"))
        elif "Xiaomi" in marca:
            self.escrever_log(executar_fastboot("oem unlock"))
        elif "Motorola" in marca:
            self.escrever_log(executar_fastboot("oem get_unlock_data"))
        else:
            self.escrever_log(executar_adb("reboot bootloader"))

    def loop_monitoramento_usb(self):
        while self.ativo:
            try:
                res = executar_adb("get-state")
                if "device" in res:
                    modelo = executar_adb("shell getprop ro.product.model")
                    lbl = f"🟢 Conectado ADB: {modelo}" if modelo else "🟢 Dispositivo ADB Conectado"
                    self.lbl_status_device.configure(text=lbl, text_color="#2ecc71")
                else:
                    res_fb = executar_fastboot("devices")
                    if "fastboot" in res_fb:
                        self.lbl_status_device.configure(text="⚡ Dispositivo em Fastboot", text_color="#f1c40f")
                    else:
                        self.lbl_status_device.configure(text="🔌 Nenhum dispositivo detetado na porta USB", text_color="#e74c3c")
            except:
                pass
            time.sleep(3)

    def fechar_sistema(self):
        self.ativo = False
        self.destroy()
        sys.exit(0)


# ==========================================
# JANELA DE LOGIN MODERNA (Conectada ao Render)
# ==========================================
class JanelaAutenticacao(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Elísio Unlock Master — Login ({VERSAO_ATUAL})")
        self.geometry("450x420")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        ctk.CTkLabel(self, text="⚡ ELÍSIO UNLOCK MASTER", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30, 5))
        ctk.CTkLabel(self, text="Validação centralizada (Render)", font=ctk.CTkFont(size=12), text_color="#aaaaaa").pack(pady=(0, 25))
        
        self.entry_user = ctk.CTkEntry(self, placeholder_text="Nome de Utilizador", width=340, height=45)
        self.entry_user.pack(pady=10)
        
        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Palavra-passe (Senha)", width=340, height=45, show="*")
        self.entry_pass.pack(pady=10)
        
        self.btn_login = ctk.CTkButton(self, text="Validar e Entrar", width=340, height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.processar_login)
        self.btn_login.pack(pady=20)
        
        self.lbl_msg = ctk.CTkLabel(self, text="", text_color="#e74c3c", font=ctk.CTkFont(size=12))
        self.lbl_msg.pack()

    def processar_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        if not username or not password:
            self.lbl_msg.configure(text="Preencha o utilizador e a senha.")
            return
            
        self.btn_login.configure(state="disabled", text="A contactar o servidor...")
        self.lbl_msg.configure(text="")
        
        def request_thread():
            try:
                response = requests.post(SERVER_URL, json={
                    "username": username,
                    "password": password,
                    "hwid": get_hwid()
                }, timeout=12)
                
                data = response.json()
                
                # Regra: Sucesso do servidor OU o Administrador Master (NUNCA bloqueia o admin)
                if data.get("status") == "sucesso" or username.lower() == "admin":
                    guardar_sessao_local(username)
                    self.after(0, lambda: self.sucesso(username))
                else:
                    erro = data.get("mensagem", "Acesso negado.")
                    self.after(0, lambda: self.lbl_msg.configure(text=erro))
                    self.after(0, lambda: self.btn_login.configure(state="normal", text="Validar e Entrar"))
            except Exception as e:
                # Se falhar a rede mas o usuário for admin, permite entrar
                if username.lower() == "admin":
                    guardar_sessao_local(username)
                    self.after(0, lambda: self.sucesso(username))
                else:
                    self.after(0, lambda: self.lbl_msg.configure(text="Erro de ligação ao Render."))
                    self.after(0, lambda: self.btn_login.configure(state="normal", text="Validar e Entrar"))

        threading.Thread(target=request_thread, daemon=True).start()

    def sucesso(self, username):
        self.destroy()
        app = ElisioUnlockMasterApp(username)
        app.mainloop()


# ==========================================
# INÍCIO DO SISTEMA
# ==========================================
def main():
    # 1. Verifica se existe sessão válida de 7 dias (abre direto sem internet)
    valida, username = verificar_sessao_7_dias()
    if valida:
        app = ElisioUnlockMasterApp(username)
        app.mainloop()
    else:
        # 2. Mostra a Janela de Login Moderna para validar com o Render
        login_app = JanelaAutenticacao()
        login_app.mainloop()

if __name__ == "__main__":
    main()
