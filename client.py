import sys
import os
import threading
import time
from datetime import datetime

import customtkinter as ctk
# O cefpython3 ou tkinterweb permite renderizar páginas web dentro de janelas Python, 
# mas para uma compatibilidade máxima e leveza (sem falhas de compilação no PyInstaller), 
# podemos abrir o link de autenticação de forma inteligente ou usar uma WebView nativa.
# Como alternativa robusta e leve para o Windows, usamos o webview ou um navegador integrado limpo,
# ou abrir o fluxo padrão de protocolo customizado / verificação limpa de sessão do app.py.
import webbrowser

from modules.adb_tools import executar_adb
from modules.fastboot_tools import executar_fastboot
from modules.config import WEB_BASE_URL, VERSAO_ATUAL
from modules.logger import registrar_log

class ElisioUnlockMasterApp(ctk.CTk):
    """Ferramenta de Bancada que abre após o login bem-sucedido no app.py"""
    def __init__(self, dados_usuario="Técnico"):
        super().__init__()
        
        self.dados_usuario = dados_usuario
        self.title(f"Elísio Unlock Master — Ferramenta de Bancada ({VERSAO_ATUAL})")
        self.geometry("1100x680")
        self.minsize(980, 600)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Centralizar na tela
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.criar_barra_lateral()
        self.criar_painel_principal()
        
        self.ativo = True
        self.thread_monitor = threading.Thread(target=self.loop_monitoramento_usb, daemon=True)
        self.thread_monitor.start()

    def criar_barra_lateral(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="⚡ ELÍSIO MASTER", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        ctk.CTkLabel(info_frame, text=f"👤 {self.dados_usuario}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="🛡️ Licença: Ativa (Render)", font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(anchor="w")
        ctk.CTkLabel(info_frame, text="🟢 Estado: Conectado", font=ctk.CTkFont(size=11), text_color="#3498db").pack(anchor="w")
        
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#34495e").grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="🌐 Universal & FRP", command=lambda: self.mudar_aba("universal")).grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="📱 Marcas & Modelos", command=lambda: self.mudar_aba("marcas")).grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚡ Flashing & Fastboot", command=lambda: self.mudar_aba("flash")).grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚙️ Informações & Diagnóstico", command=lambda: self.mudar_aba("info")).grid(row=6, column=0, padx=20, pady=8, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="Abrir Portal Web", fg_color="#2980b9", hover_color="#3498db", command=lambda: webbrowser.open(WEB_BASE_URL)).grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Sair / Fechar", fg_color="#c0392b", hover_color="#e74c3c", command=self.fechar_sistema).grid(row=8, column=0, padx=20, pady=20, sticky="ew")

    def criar_painel_principal(self):
        self.main_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_panel.grid(row=0, column=1, sticky="nsew")
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)
        
        self.header_frame = ctk.CTkFrame(self.main_panel, height=60, fg_color="#262626")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        
        self.lbl_status_device = ctk.CTkLabel(self.header_frame, text="🔌 Detetando estado do dispositivo na USB...", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f1c40f")
        self.lbl_status_device.pack(side="left", padx=20, pady=15)
        
        self.content_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.mudar_aba("universal")

    def limpar_conteudo(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def mudar_aba(self, nome):
        self.limpar_conteudo()
        if nome == "universal":
            self.aba_universal()
        elif nome == "marcas":
            self.aba_marcas()
        elif nome == "flash":
            self.aba_flash()
        elif nome == "info":
            self.aba_info()

    def aba_universal(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#222222")
        frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(frame, text="Ferramentas Universais de Manutenção", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=15)
        
        btn_f = ctk.CTkFrame(frame, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_f, text="Listar Portas ADB", width=180, command=lambda: self.escrever_log(executar_adb("devices"))).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Bypass FRP (Pacotes)", width=180, command=self.acao_bypass_frp).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Recovery Mode", width=180, command=lambda: self.escrever_log(executar_adb("reboot recovery"))).pack(side="left", padx=5)
        
        self.criar_caixa_log(frame)

    def aba_marcas(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#222222")
        frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(frame, text="Módulo por Fabricante", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=15)
        
        sel_f = ctk.CTkFrame(frame, fg_color="transparent")
        sel_f.pack(fill="x", padx=20, pady=10)
        
        self.combo_marca = ctk.CTkComboBox(sel_f, values=["Samsung", "Xiaomi", "Motorola", "Tecno / Infinix"], width=220)
        self.combo_marca.pack(side="left", padx=5)
        ctk.CTkButton(sel_f, text="Executar Rotina MTP/Fastboot", command=self.executar_rotina_marca).pack(side="left", padx=10)
        
        self.criar_caixa_log(frame)

    def aba_flash(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#222222")
        frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(frame, text="Flashing & Fastboot Partition Tools", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=15)
        
        btn_f = ctk.CTkFrame(frame, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_f, text="Listar Fastboot Devices", command=lambda: self.escrever_log(executar_fastboot("devices"))).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Wipe Userdata (Fastboot)", fg_color="#c0392b", hover_color="#e74c3c", command=lambda: self.escrever_log(executar_fastboot("erase userdata"))).pack(side="left", padx=5)
        
        self.criar_caixa_log(frame)

    def aba_info(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#222222")
        frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(frame, text="Diagnóstico Completo de Hardware", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkButton(frame, text="Ler Propriedades do Aparelho", command=self.ler_hardware).pack(anchor="w", padx=20, pady=10)
        self.criar_caixa_log(frame)

    def criar_caixa_log(self, parent):
        log_container = ctk.CTkFrame(parent, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.txt_log = ctk.CTkTextbox(log_container, fg_color="#121212", text_color="#2ecc71", font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_log.pack(fill="both", expand=True)
        self.escrever_log(f"[{datetime.now().strftime('%H:%M:%S')}] Ferramenta iniciada com sucesso via autenticação Render.")

    def escrever_log(self, texto):
        if hasattr(self, 'txt_log'):
            self.txt_log.insert("end", texto + "\n")
            self.txt_log.see("end")

    def acao_bypass_frp(self):
        self.escrever_log("[+] Iniciando contorno de FRP...")
        self.escrever_log(executar_adb("shell am start -a android.intent.action.VIEW -d https://www.google.com"))

    def ler_hardware(self):
        self.escrever_log("--- DIAGNÓSTICO DE HARDWARE ---")
        self.escrever_log("Modelo: " + executar_adb("shell getprop ro.product.model"))
        self.escrever_log("Android: " + executar_adb("shell getprop ro.build.version.release"))
        self.escrever_log("Serial: " + executar_adb("get-serialno"))

    def executar_rotina_marca(self):
        marca = self.combo_marca.get()
        self.escrever_log(f"[+] Aplicando rotina para {marca}...")
        if "Samsung" in marca:
            self.escrever_log(executar_adb("shell am start -a android.intent.action.DIAL -d tel:%2A%230%2A%23"))
        else:
            self.escrever_log(executar_adb("devices"))

    def loop_monitoramento_usb(self):
        while self.ativo:
            try:
                res = executar_adb("get-state")
                if "device" in res:
                    modelo = executar_adb("shell getprop ro.product.model")
                    texto = f"🟢 Conectado ADB: {modelo}" if modelo else "🟢 Dispositivo ADB Conectado"
                    self.after(0, lambda: self.lbl_status_device.configure(text=texto, text_color="#2ecc71"))
                else:
                    res_fb = executar_fastboot("devices")
                    if len(res_fb.strip()) > 0:
                        self.after(0, lambda: self.lbl_status_device.configure(text="⚡ Dispositivo em Fastboot", text_color="#f1c40f"))
                    else:
                        self.after(0, lambda: self.lbl_status_device.configure(text="🔌 Nenhum dispositivo detetado na porta USB", text_color="#e74c3c"))
            except Exception:
                pass
            time.sleep(3)

    def fechar_sistema(self):
        self.ativo = False
        self.destroy()
        sys.exit(0)


class JanelaLoginRender(ctk.CTk):
    """Janela inicial elegante que exibe os campos do app.py e aguarda a autenticação web"""
    def __init__(self):
        super().__init__()
        
        self.title(f"Elísio Unlock Master — Login Web ({VERSAO_ATUAL})")
        self.geometry("480x450")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        ctk.CTkLabel(self, text="⚡ ELÍSIO UNLOCK MASTER", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(25, 5))
        ctk.CTkLabel(self, text="Autenticação Centralizada (Render)", font=ctk.CTkFont(size=12), text_color="#aaaaaa").pack(pady=(0, 15))
        
        # Botão para abrir o link do Render diretamente se o utilizador quiser ver no navegador completo
        self.btn_browser = ctk.CTkButton(self, text="🌐 Abrir Página de Login no Navegador", fg_color="#2c3e50", hover_color="#34495e", command=self.abrir_no_navegador)
        self.btn_browser.pack(pady=5, padx=30, fill="x")
        
        ctk.CTkLabel(self, text="— OU INSIRA SUAS CREDENCIAIS AQUI —", font=ctk.CTkFont(size=10), text_color="#666666").pack(pady=10)
        
        self.entry_user = ctk.CTkEntry(self, placeholder_text="Nome de Utilizador", width=380, height=40)
        self.entry_user.pack(pady=5)
        
        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Palavra-passe (Senha)", width=380, height=40, show="*")
        self.entry_pass.pack(pady=5)
        
        self.btn_entrar = ctk.CTkButton(self, text="Validar e Entrar na Ferramenta", width=380, height=40, command=self.validar_credenciais, font=ctk.CTkFont(weight="bold"))
        self.btn_entrar.pack(pady=15)
        
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="#e74c3c", font=ctk.CTkFont(size=11))
        self.lbl_status.pack(pady=5)

    def abrir_no_navegador(self):
        try:
            webbrowser.open(f"{WEB_BASE_URL}/login")
            registrar_log("Página de login do Render aberta no navegador web.")
        except Exception:
            pass

    def validar_credenciais(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        if not username or not password:
            self.lbl_status.configure(text="Preencha o utilizador e a senha.")
            return
            
        self.btn_entrar.configure(state="disabled", text="A aguardar resposta do Render...")
        self.lbl_status.configure(text="")
        
        def processo():
            try:
                import requests
                # Comunica diretamente com o endpoint do seu app.py no Render
                response = requests.post(f"{WEB_BASE_URL}/api/validar_hwid", json={
                    "username": username,
                    "password": password,
                    "hwid": "PC_DESKTOP_" + platform.node()
                }, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # Se for sucesso ou se for o admin (nunca bloqueia admin)
                    if data.get("status") == "sucesso" or username.lower() == "admin":
                        registrar_log(f"Utilizador {username} autenticado com sucesso pelo Render.")
                        self.after(0, lambda: self.sucesso_login(username))
                    else:
                        msg = data.get("mensagem", "Credenciais rejeitadas.")
                        self.after(0, lambda: self.lbl_status.configure(text=str(msg)))
                        self.after(0, lambda: self.btn_entrar.configure(state="normal", text="Validar e Entrar na Ferramenta"))
                else:
                    self.after(0, lambda: self.lbl_status.configure(text="Erro de resposta do servidor no Render."))
                    self.after(0, lambda: self.btn_entrar.configure(state="normal", text="Validar e Entrar na Ferramenta"))
            except Exception as e:
                self.after(0, lambda: self.lbl_status.configure(text=f"Erro de conexão: sem internet?"))
                self.after(0, lambda: self.btn_entrar.configure(state="normal", text="Validar e Entrar na Ferramenta"))

        threading.Thread(target=processo, daemon=True).start()

    def sucesso_login(self, username):
        # A janela de login some/fecha-se aqui
        self.destroy()
        # Abre a ferramenta principal na área de trabalho
        app = ElisioUnlockMasterApp(username)
        app.mainloop()


def main():
    # Abre a janela que interage com o link/sistema do app.py no Render
    app_login = JanelaLoginRender()
    app_login.mainloop()

if __name__ == "__main__":
    main()
