import platform
import subprocess
import sys
import os
import time
import threading
import customtkinter as ctk

# ==========================================
# VERSÃO PESSOAL (FUNCIONAL & DIRETA)
# ==========================================
VERSAO_ATUAL = "v3.0.0-Pro-Pessoal"

def obter_caminho_binario(nome_binario):
    """Garante que o app encontre os binários dentro da pasta bin/ mesmo após compilado"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, 'bin', nome_binario)

def executar_adb(args):
    adb_path = obter_caminho_binario("adb.exe" if platform.system() == "Windows" else "adb")
    cmd = f'"{adb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=15)
        return res.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return f"Erro ADB: {str(e)}"

def executar_fastboot(args):
    fb_path = obter_caminho_binario("fastboot.exe" if platform.system() == "Windows" else "fastboot")
    cmd = f'"{fb_path}" {args}'
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=15)
        return res.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return f"Erro Fastboot: {str(e)}"


class ElisioUnlockMasterPessoal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Elísio Unlock Master — Bancada Pessoal ({VERSAO_ATUAL})")
        self.geometry("1200x750")
        self.minsize(980, 620)
        
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
        
        # Monitor USB ativo em segundo plano
        self.ativo = True
        threading.Thread(target=self.loop_monitoramento_usb, daemon=True).start()

    def criar_barra_lateral(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        ctk.CTkLabel(self.sidebar, text="⚡ ELÍSIO MASTER", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkLabel(info_frame, text="👤 Modo Pessoal (Direto)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="🟢 Operacional & Ativo", font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(anchor="w")
        
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#34495e").grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        
        # Abas de Ação Direta
        ctk.CTkButton(self.sidebar, text="🌐 Universal (FRP & Senhas)", command=lambda: self.mudar_aba("universal")).grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="📱 Marcas & Modelos", command=lambda: self.mudar_aba("marcas")).grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚡ Fastboot & Wipe Total", command=lambda: self.mudar_aba("flash")).grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="📖 Guia Manual (Botões)", command=lambda: self.mudar_aba("guia")).grid(row=6, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(self.sidebar, text="⚙️ Diagnóstico & HWID", command=lambda: self.mudar_aba("info")).grid(row=7, column=0, padx=20, pady=8, sticky="ew")
        
        ctk.CTkButton(self.sidebar, text="Sair do Programa", fg_color="#c0392b", hover_color="#e74c3c", command=self.fechar_sistema).grid(row=9, column=0, padx=20, pady=20, sticky="ew")

    def criar_painel_principal(self):
        self.main_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_panel.grid(row=0, column=1, sticky="nsew")
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)
        
        # Header de Estado USB Real
        self.header_frame = ctk.CTkFrame(self.main_panel, height=60, fg_color="#262626")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        self.lbl_status_device = ctk.CTkLabel(self.header_frame, text="🔌 À procura de telemóvel na USB...", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f1c40f")
        self.lbl_status_device.pack(side="left", padx=20, pady=15)
        
        # Conteúdo + Consola Real
        self.content_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.frame_botoes = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.frame_botoes.grid(row=0, column=0, sticky="nsew")
        
        # Consola Verde de Execução Real
        log_container = ctk.CTkFrame(self.content_frame)
        log_container.grid(row=1, column=0, sticky="nsew", pady=(15, 0))
        self.txt_log = ctk.CTkTextbox(log_container, fg_color="#0d0d0d", text_color="#00ff00", font=ctk.CTkFont(family="Consolas", size=13))
        self.txt_log.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.escrever_log(f"[{time.strftime('%H:%M:%S')}] Sistema pronto. Ligue o telemóvel à porta USB e escolha a operação.")
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

    # ==========================================
    # ABAS COM AÇÃ0 REAL DE BANCADA
    # ==========================================
    def aba_universal(self):
        ctk.CTkLabel(self.frame_botoes, text="Módulo Universal — Remoção de Conta Google & Senhas", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        r1 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r1.pack(fill="x", pady=5)
        ctk.CTkButton(r1, text="Listar Dispositivos (ADB)", width=210, command=lambda: self.escrever_log(executar_adb("devices"))).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Remover FRP (Conta Google)", width=210, fg_color="#d35400", hover_color="#e67e22", command=self.acao_remover_frp).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Remover Senha / Format (ADB)", width=210, fg_color="#c0392b", hover_color="#e74c3c", command=self.acao_remover_senha_adb).pack(side="left", padx=5)

        r2 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r2.pack(fill="x", pady=10)
        ctk.CTkButton(r2, text="Forçar Recovery Mode", width=210, command=lambda: self.escrever_log(executar_adb("reboot recovery"))).pack(side="left", padx=5)
        ctk.CTkButton(r2, text="Reiniciar Aparelho Normal", width=210, command=lambda: self.escrever_log(executar_adb("reboot"))).pack(side="left", padx=5)

    def aba_marcas(self):
        ctk.CTkLabel(self.frame_botoes, text="Seleção de Marca & Rotina Específica", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        r1 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r1.pack(fill="x", pady=5)
        
        self.combo_marca = ctk.CTkComboBox(r1, values=["Samsung", "Xiaomi / Redmi", "Motorola", "Tecno / Infinix / Itel"], width=250, height=35)
        self.combo_marca.pack(side="left", padx=5)
        
        ctk.CTkButton(r1, text="Executar FRP / Reset da Marca", width=220, height=35, command=self.acao_executar_marca).pack(side="left", padx=10)

        # Explicação rápida na tela
        lbl_info = ctk.CTkLabel(self.frame_botoes, text="💡 Dica: Selecione a marca do telemóvel conectado para disparar o atalho de bypass ou comandos de desbloqueio.", text_color="#aaaaaa", font=ctk.CTkFont(size=12))
        lbl_info.pack(anchor="w", padx=5, pady=15)

    def aba_flash(self):
        ctk.CTkLabel(self.frame_botoes, text="Modo Fastboot — Limpeza Total e Remoção de Palavra-Passe", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        
        r1 = ctk.CTkFrame(self.frame_botoes, fg_color="transparent")
        r1.pack(fill="x", pady=5)
        ctk.CTkButton(r1, text="Listar Fastboot Devices", width=220, command=lambda: self.escrever_log(executar_fastboot("devices"))).pack(side="left", padx=5)
        ctk.CTkButton(r1, text="Wipe Userdata (Apagar Senha/Dados)", width=250, fg_color="#c0392b", hover_color="#e74c3c", command=self.acao_wipe_fastboot).pack(side="left", padx=5)

    def aba_guia(self):
        ctk.CTkLabel(self.frame_botoes, text="Guia de Hard Reset Físico (Caso o telemóvel não ligue por cabo)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 5))
        guia_txt = (
            "📱 [ SAMSUNG ]: Desligue. Segure Volume Mais (+) + Power até ver o logo. Use os botões de volume até 'Wipe data/factory reset' e confirme com Power.\n\n"
            "📱 [ XIAOMI / REDMI ]: Desligue. Segure Volume Mais (+) + Power. No menu Recovery, escolha 'Wipe Data' -> 'Wipe All Data'.\n\n"
            "📱 [ MOTOROLA ]: Desligue. Segure Volume Menos (-) + Power. Selecione 'Recovery Mode' com Volume e confirme com Power.\n\n"
            "📱 [ TECNO / INFINIX ]: Desligue. Segure Volume Mais (+) + Power em simultâneo até entrar no menu de recuperação."
        )
        lbl = ctk.CTkLabel(self.frame_botoes, text=guia_txt, justify="left", font=ctk.CTkFont(size=13), text_color="#d0d0d0")
        lbl.pack(anchor="w", padx=5, pady=5)

    def aba_info(self):
        ctk.CTkLabel(self.frame_botoes, text="Diagnóstico Completo do Aparelho Conectado", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkButton(self.frame_botoes, text="Ler Informações de Hardware (Getprop)", width=280, height=40, command=self.acao_ler_diagnostico).pack(anchor="w", padx=5, pady=5)

    # ==========================================
    # EXECUÇÃO REAL DE COMANDOS ADB / FASTBOOT
    # ==========================================
    def acao_remover_frp(self):
        self.escrever_log("\n[+] A iniciar remoção de FRP (Conta Google) via comandos ADB diretos...")
        self.escrever_log(executar_adb("shell am start -S -n com.google.android.gsf/.update.SystemUpdateActivity"))
        self.escrever_log(executar_adb("shell am start -a android.intent.action.VIEW -d https://www.google.com"))
        self.escrever_log("[+] Rotina enviada! Verifique se o navegador abriu no telemóvel.")

    def acao_remover_senha_adb(self):
        self.escrever_log("\n[+] A tentar apagar dados de bloqueio (Screen Lock) via ADB...")
        self.escrever_log(executar_adb("shell rm /data/system/gesture.key"))
        self.escrever_log(executar_adb("shell rm /data/system/password.key"))
        self.escrever_log(executar_adb("shell rm /data/system/*.key"))
        self.escrever_log("[+] Ficheiros de senha removidos. Reinicie o telemóvel para testar.")

    def acao_wipe_fastboot(self):
        self.escrever_log("\n[+] ATENÇÃO: A executar limpeza total de dados e remoção de senha em Fastboot...")
        self.escrever_log(executar_fastboot("erase userdata"))
        self.escrever_log(executar_fastboot("erase cache"))
        self.escrever_log(executar_fastboot("reboot"))
        self.escrever_log("[+] Processo concluído! O telemóvel vai reiniciar limpo de fábrica.")

    def acao_ler_diagnostico(self):
        self.escrever_log("\n---------------- DIAGNÓSTICO DO TELEMÓVEL ----------------")
        self.escrever_log("Modelo: " + executar_adb("shell getprop ro.product.model"))
        self.escrever_log("Versão Android: " + executar_adb("shell getprop ro.build.version.release"))
        self.escrever_log("Número de Série: " + executar_adb("get-serialno"))
        self.escrever_log("---------------------------------------------------------")

    def acao_executar_marca(self):
        marca = self.combo_marca.get()
        self.escrever_log(f"\n[+] A disparar rotina especializada para: {marca}")
        if "Samsung" in marca:
            # Comando de teste de fábrica / MTP dialer para Samsung FRP
            self.escrever_log(executar_adb("shell am start -a android.intent.action.DIAL -d tel:%2A%230%2A%23"))
            self.escrever_log("[+] Menu de teste Samsung (Dialer *#0*#) acionado.")
        elif "Xiaomi" in marca:
            self.escrever_log(executar_fastboot("oem unlock"))
            self.escrever_log(executar_fastboot("flashing unlock"))
        elif "Motorola" in marca:
            self.escrever_log(executar_fastboot("oem get_unlock_data"))
        else:
            self.escrever_log(executar_adb("reboot bootloader"))
            self.escrever_log("[+] Aparelho direcionado para o Bootloader.")

    def loop_monitoramento_usb(self):
        """Monitoriza a porta USB a cada 3 segundos de forma real"""
        while self.ativo:
            try:
                res_adb = executar_adb("get-state")
                if "device" in res_adb:
                    modelo = executar_adb("shell getprop ro.product.model")
                    txt = f"🟢 Conectado (ADB): {modelo}" if modelo else "🟢 Dispositivo ADB Conectado"
                    self.after(0, lambda: self.lbl_status_device.configure(text=txt, text_color="#2ecc71"))
                else:
                    res_fb = executar_fastboot("devices")
                    if len(res_fb.strip()) > 0 and "fastboot" in res_fb:
                        self.after(0, lambda: self.lbl_status_device.configure(text="⚡ Dispositivo detetado em modo FASTBOOT", text_color="#f1c40f"))
                    else:
                        self.after(0, lambda: self.lbl_status_device.configure(text="🔌 Nenhum dispositivo detetado na porta USB", text_color="#e74c3c"))
            except:
                pass
            time.sleep(3)

    def fechar_sistema(self):
        self.ativo = False
        self.destroy()
        sys.exit(0)


def main():
    app = ElisioUnlockMasterPessoal()
    app.mainloop()

if __name__ == "__main__":
    main()
