import sys
import os
import webbrowser
import threading
import time
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from modules.auth import validar_token_servidor
from modules.adb_tools import executar_adb
from modules.fastboot_tools import executar_fastboot
from modules.config import carregar_configuracao
from modules.logger import registrar_log, registrar_log as log_sistema

config = carregar_configuracao()

class ElisioUnlockMasterApp(ctk.CTk):
    def __init__(self, dados_sessao):
        super().__init__()
        
        self.dados_sessao = dados_sessao
        self.title(f"Elísio Unlock Master — {config.get('versao_atual', 'v2.5.0')}")
        self.geometry("1100x680")
        self.minsize(980, 600)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.criar_barra_lateral()
        self.criar_painel_principal()
        
        # Thread de monitoramento USB segura com after()
        self.ativo = True
        self.thread_monitor = threading.Thread(target=self.loop_monitoramento_usb, daemon=True)
        self.thread_monitor.start()

    def criar_barra_lateral(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="⚡ ELÍSIO MASTER", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        usuario = self.dados_sessao.get("usuario", "Técnico")
        validade = self.dados_sessao.get("validade", "Ativa")
        
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        ctk.CTkLabel(info_frame, text=f"👤 {usuario}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"🛡️ Licença: {validade}", font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(anchor="w")
        ctk.CTkLabel(info_frame, text="🟢 Servidor: Online", font=ctk.CTkFont(size=11), text_color="#3498db").pack(anchor="w")
        
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#34495e").grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="🌐 Universal & FRP", command=lambda: self.mudar_aba("universal")).grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="📱 Marcas & Modelos", command=lambda: self.mudar_aba("marcas")).grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚡ Flashing & Fastboot", command=lambda: self.mudar_aba("flash")).grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚙️ Informações & Diagnóstico", command=lambda: self.mudar_aba("info")).grid(row=6, column=0, padx=20, pady=8, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="Sair / Encerrar", fg_color="#c0392b", hover_color="#e74c3c", command=self.fechar_sistema).grid(row=8, column=0, padx=20, pady=20, sticky="ew")

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
        self.escrever_log(f"[{datetime.now().strftime('%H:%M:%S')}] Módulo gráfico iniciado com sucesso.")

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

def main():
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
        valido, dados = validar_token_servidor(token)
        if valido:
            app = ElisioUnlockMasterApp(dados)
            app.mainloop()
        else:
            sys.exit(1)
    else:
        try:
            webbrowser.open(config.get("web_base_url"))
        except Exception:
            pass
        sys.exit(0)

if __name__ == "__main__":
    main()
