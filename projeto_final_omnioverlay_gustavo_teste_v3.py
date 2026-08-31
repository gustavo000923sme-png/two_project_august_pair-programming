"""
===============================================================================
PROJETO: OmniOverlay - Multi-Account HUD (IA, Navegador & Spotify Corrigidos)
===============================================================================
"""

import json
import os
import threading
import time
import urllib.parse
import tkinter as tk
import customtkinter as ctk
from pynput import keyboard
from tkinterweb import HtmlFrame
from google import genai

# Configuração visual global
ctk.set_appearance_mode("dark")

COLOR_THEMES = {
    "azul": {"primary": "#2563EB", "hover": "#1D4ED8"},
    "vermelho": {"primary": "#DC2626", "hover": "#B91C1C"},
    "verde": {"primary": "#16A34A", "hover": "#15803D"},
    "roxo": {"primary": "#9333EA", "hover": "#7E22CE"},
}

CONFIG_FILE = "app_config.json"


class AccountManager:
    """Gerencia a leitura e escrita das contas no disco."""

    @staticmethod
    def carregar_dados():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    if "perfis" in dados and len(dados["perfis"]) > 0:
                        return dados
            except Exception as e:
                print(f"[ERRO] Falha ao ler {CONFIG_FILE}: {e}")

        dados_padrao = {
            "perfis": [
                {
                    "id": "p1",
                    "nome": "Jogador Principal",
                    "cor_acento": "azul",
                    "gemini_key": ""
                }
            ],
            "ultimo_perfil": "p1",
            "modo_tema": "dark"
        }
        AccountManager.salvar_dados(dados_padrao)
        return dados_padrao

    @staticmethod
    def salvar_dados(dados):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERRO] Falha ao salvar em {CONFIG_FILE}: {e}")


class ProfileSelectorFrame(ctk.CTkFrame):
    """Tela de Seleção e Criação de Perfis."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=12)
        self.controller = controller
        self.criar_interface()

    def criar_interface(self):
        header = ctk.CTkFrame(self, fg_color="#1E293B", height=50, corner_radius=0)
        header.pack(fill="x")

        lbl_titulo = ctk.CTkLabel(
            header,
            text="🎮 Escolha sua Conta",
            font=("Segoe UI", 14, "bold"),
            text_color="#F8FAFC",
        )
        lbl_titulo.pack(side="left", padx=16, pady=12)

        btn_fechar = ctk.CTkButton(
            header,
            text="✕",
            width=30,
            height=30,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self.controller.destroy,
        )
        btn_fechar.pack(side="right", padx=12)

        self.scroll_perfis = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_perfis.pack(fill="both", expand=True, padx=20, pady=15)

        frame_criar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        frame_criar.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            frame_criar,
            text="Criar Nova Conta",
            font=("Segoe UI", 11, "bold"),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.entry_novo_nome = ctk.CTkEntry(
            frame_criar,
            placeholder_text="Nome da conta...",
            height=36,
            fg_color="#0F172A",
            border_color="#334155"
        )
        self.entry_novo_nome.pack(fill="x", padx=12, pady=4)
        self.entry_novo_nome.bind("<Return>", lambda e: self.acao_criar_perfil())

        btn_novo = ctk.CTkButton(
            frame_criar,
            text="+ Criar e Entrar",
            height=36,
            corner_radius=8,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=("Segoe UI", 11, "bold"),
            command=self.acao_criar_perfil,
        )
        btn_novo.pack(fill="x", padx=12, pady=(4, 12))

    def atualizar_lista(self):
        for widget in self.scroll_perfis.winfo_children():
            widget.destroy()

        perfis = self.controller.dados_config.get("perfis", [])

        for perfil in perfis:
            card = ctk.CTkFrame(self.scroll_perfis, fg_color="#1E293B", corner_radius=12)
            card.pack(fill="x", pady=6, ipady=4)

            lbl_avatar = ctk.CTkLabel(
                card,
                text="👤",
                width=42,
                height=42,
                corner_radius=21,
                fg_color="#334155",
                text_color="#FFFFFF",
                font=("Segoe UI", 16),
            )
            lbl_avatar.pack(side="left", padx=12)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True)

            lbl_nome = ctk.CTkLabel(
                info_frame,
                text=perfil["nome"],
                font=("Segoe UI", 12, "bold"),
                text_color="#F8FAFC",
                anchor="w",
            )
            lbl_nome.pack(fill="x", pady=(12, 0))

            btn_entrar = ctk.CTkButton(
                card,
                text="Entrar",
                width=80,
                height=32,
                corner_radius=6,
                fg_color="#16A34A",
                hover_color="#15803D",
                font=("Segoe UI", 11, "bold"),
                command=lambda p=perfil: self.controller.entrar_no_perfil(p),
            )
            btn_entrar.pack(side="right", padx=12)

    def acao_criar_perfil(self):
        nome = self.entry_novo_nome.get().strip()
        if not nome:
            return

        novo_id = f"p_{int(time.time())}"
        novo_perfil = {
            "id": novo_id,
            "nome": nome,
            "cor_acento": "azul",
            "gemini_key": ""
        }

        self.controller.dados_config["perfis"].append(novo_perfil)
        AccountManager.salvar_dados(self.controller.dados_config)

        self.entry_novo_nome.delete(0, "end")
        self.controller.entrar_no_perfil(novo_perfil)


class DashboardFrame(ctk.CTkFrame):
    """Tela Principal do Dashboard / Overlay."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#0F172A", corner_radius=12)
        self.controller = controller

        self._offset_x = 0
        self._offset_y = 0
        self.modo_cinema_ativo = False
        self.dynamic_accent_buttons = []

        self.criar_interface()

    def criar_interface(self):
        # Header Superior
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color="#1E293B",
            corner_radius=12,
            border_color="#334155",
            border_width=1,
            height=60,
        )
        self.header_frame.pack(fill="x", padx=16, pady=(16, 8))

        self.header_frame.bind("<Button-1>", self.iniciar_arraste)
        self.header_frame.bind("<B1-Motion>", self.arrastar_janela)

        self.lbl_avatar = ctk.CTkLabel(
            self.header_frame,
            text="👤",
            width=42,
            height=42,
            corner_radius=21,
            fg_color="#3B82F6",
            text_color="#FFFFFF",
            font=("Segoe UI", 18),
        )
        self.lbl_avatar.pack(side="left", padx=(12, 10))

        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="OmniOverlay",
            font=("Segoe UI", 14, "bold"),
            text_color="#F8FAFC",
        )
        self.lbl_titulo.pack(side="left", padx=2)

        # Botão Modo Cinema
        self.btn_modo_cinema = ctk.CTkButton(
            self.header_frame,
            text="🎬 Modo Cinema",
            width=110,
            height=32,
            corner_radius=8,
            fg_color="#9333EA",
            hover_color="#7E22CE",
            font=("Segoe UI", 10, "bold"),
            command=self.toggle_modo_cinema,
        )
        self.btn_modo_cinema.pack(side="right", padx=(4, 8))

        btn_trocar_conta = ctk.CTkButton(
            self.header_frame,
            text="🔄 Trocar Conta",
            width=110,
            height=32,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            font=("Segoe UI", 10, "bold"),
            command=self.controller.abrir_seletor_perfis,
        )
        btn_trocar_conta.pack(side="right", padx=4)

        btn_fechar = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self.controller.destroy,
        )
        btn_fechar.pack(side="right", padx=4)

        # Barra de Pesquisa Universal (Otimizada para HTML leve)
        self.frame_busca = ctk.CTkFrame(
            self,
            fg_color="#1E293B",
            corner_radius=12,
            border_color="#334155",
            border_width=1,
        )
        self.frame_busca.pack(fill="x", padx=16, pady=4)

        self.entry_universal = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Pesquise na web ou digite um link (ex: wikipedia.org)...",
            height=38,
            corner_radius=8,
            fg_color="#334155",
            text_color="#F8FAFC",
            border_color="#334155",
            font=("Segoe UI", 11),
        )
        self.entry_universal.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self.entry_universal.bind("<Return>", lambda e: self.executar_busca_universal())

        btn_executar = ctk.CTkButton(
            self.frame_busca,
            text="Buscar 🔍",
            width=100,
            height=38,
            corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            command=self.executar_busca_universal,
        )
        btn_executar.pack(side="right", padx=8, pady=8)
        self.dynamic_accent_buttons.append(btn_executar)

        # Abas Principais
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            fg_color="#1E293B",
            border_color="#334155",
            border_width=1,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.tab_web = self.tabview.add("🌐 Navegador")
        self.tab_spotify = self.tabview.add("🎵 Spotify Player")
        self.tab_streaming = self.tabview.add("🎬 Streaming")
        self.tab_ai = self.tabview.add("🤖 Assistente IA")
        self.tab_config = self.tabview.add("⚙️ Configurações")

        self.montar_aba_navegador()
        self.montar_aba_spotify()
        self.montar_aba_streaming()
        self.montar_aba_ai()
        self.montar_aba_config()

    def carregar_perfil(self, perfil):
        self.lbl_titulo.configure(text=f"OmniOverlay - {perfil['nome']}")
        self.entry_api_key.delete(0, "end")
        self.entry_api_key.insert(0, perfil.get("gemini_key", ""))
        self.aplicar_cor_acento(perfil.get("cor_acento", "azul"))

    def aplicar_cor_acento(self, nome_cor):
        cor = COLOR_THEMES.get(nome_cor, COLOR_THEMES["azul"])
        for btn in self.dynamic_accent_buttons:
            btn.configure(fg_color=cor["primary"], hover_color=cor["hover"])

        if self.controller.perfil_ativo:
            self.controller.perfil_ativo["cor_acento"] = nome_cor
            AccountManager.salvar_dados(self.controller.dados_config)

    def iniciar_arraste(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def arrastar_janela(self, event):
        if not self.modo_cinema_ativo:
            x = self.controller.winfo_x() + (event.x - self._offset_x)
            y = self.controller.winfo_y() + (event.y - self._offset_y)
            self.controller.geometry(f"+{x}+{y}")

    def toggle_modo_cinema(self):
        self.modo_cinema_ativo = not self.modo_cinema_ativo

        if self.modo_cinema_ativo:
            self.controller.attributes("-alpha", 0.85)
            self.frame_busca.pack_forget()
            self.btn_modo_cinema.configure(text="❌ Sair Cinema", fg_color="#DC2626", hover_color="#B91C1C")
            
            ws = self.controller.winfo_screenwidth()
            hs = self.controller.winfo_screenheight()
            self.controller.geometry(f"{ws}x{hs}+0+0")
        else:
            self.controller.attributes("-alpha", 0.98)
            self.frame_busca.pack(fill="x", padx=16, pady=4, after=self.header_frame)
            self.btn_modo_cinema.configure(text="🎬 Modo Cinema", fg_color="#9333EA", hover_color="#7E22CE")
            self.controller.centralizar_janela(920, 800)

    def montar_aba_navegador(self):
        nav_bar = ctk.CTkFrame(self.tab_web, fg_color="transparent")
        nav_bar.pack(fill="x", pady=(0, 6))

        btn_voltar = ctk.CTkButton(
            nav_bar,
            text="◄ Voltar",
            width=70,
            height=30,
            fg_color="#334155",
            text_color="#F8FAFC",
            command=lambda: self.browser.go_back(),
        )
        btn_voltar.pack(side="left", padx=2)

        btn_avancar = ctk.CTkButton(
            nav_bar,
            text="Avançar ►",
            width=70,
            height=30,
            fg_color="#334155",
            text_color="#F8FAFC",
            command=lambda: self.browser.go_forward(),
        )
        btn_avancar.pack(side="left", padx=2)

        self.browser = HtmlFrame(self.tab_web)
        self.browser.pack(fill="both", expand=True)
        # DuckDuckGo Lite para carregamento ultra-rápido e compatível com Tkinter
        self.browser.load_website("https://lite.duckduckgo.com/lite/")

    def montar_aba_spotify(self):
        """Player do Spotify Embutido Ultraleve e Integrado."""
        frame_controles = ctk.CTkFrame(self.tab_spotify, fg_color="transparent")
        frame_controles.pack(fill="x", pady=6)

        ctk.CTkLabel(
            frame_controles,
            text="Cole o Link de uma Música/Playlist do Spotify:",
            font=("Segoe UI", 11, "bold"),
            text_color="#1DB954"
        ).pack(side="left", padx=8)

        self.entry_spotify_url = ctk.CTkEntry(
            frame_controles,
            placeholder_text="https://open.spotify.com/track/...",
            height=32,
            fg_color="#334155",
            text_color="#F8FAFC"
        )
        self.entry_spotify_url.pack(side="left", fill="x", expand=True, padx=8)

        btn_carregar_spot = ctk.CTkButton(
            frame_controles,
            text="Tocar 🎵",
            width=80,
            height=32,
            fg_color="#1DB954",
            hover_color="#1AA34A",
            command=self.carregar_embed_spotify
        )
        btn_carregar_spot.pack(side="right", padx=8)

        self.spotify_browser = HtmlFrame(self.tab_spotify)
        self.spotify_browser.pack(fill="both", expand=True, pady=6)
        
        # Player Padrão do Spotify Embutido (Playlist Top Hits Brasil)
        self.carregar_embed_spotify("https://open.spotify.com/playlist/37i9dQZF1DX0FO21A2R1ch")

    def carregar_embed_spotify(self, url_custom=None):
        url = url_custom or self.entry_spotify_url.get().strip()
        if not url:
            return

        # Converte links padrão do Spotify para versão Embed compacta
        embed_url = url.replace("open.spotify.com/", "open.spotify.com/embed/")
        
        html_code = f"""
        <html>
        <body style="background-color:#0F172A; margin:0; padding:10px; display:flex; justify-content:center; align-items:center;">
            <iframe src="{embed_url}" width="100%" height="450" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
        </body>
        </html>
        """
        self.spotify_browser.load_html(html_code)

    def montar_aba_streaming(self):
        grid_frame = ctk.CTkFrame(self.tab_streaming, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=16, pady=16)

        servicos = [
            ("🔴 Netflix", "https://www.netflix.com", "#E50914"),
            ("▶️ YouTube", "https://m.youtube.com", "#FF0000"),
            ("✨ Disney+", "https://www.disneyplus.com", "#113CCF"),
            ("💜 Twitch", "https://m.twitch.tv", "#9146FF"),
            ("📦 Prime Video", "https://www.primevideo.com", "#00A8E1"),
            ("🟣 Max", "https://www.max.com", "#002BE7"),
        ]

        col, row = 0, 0
        for nome, url, cor in servicos:
            btn = ctk.CTkButton(
                grid_frame,
                text=nome,
                height=60,
                corner_radius=10,
                fg_color="#334155",
                hover_color=cor,
                text_color="#F8FAFC",
                font=("Segoe UI", 12, "bold"),
                command=lambda u=url: self.navegar_para(u),
            )
            btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            col += 1
            if col > 2:
                col = 0
                row += 1

        for i in range(3):
            grid_frame.grid_columnconfigure(i, weight=1)

    def montar_aba_ai(self):
        self.chat_history = ctk.CTkTextbox(
            self.tab_ai,
            fg_color="#334155",
            text_color="#F8FAFC",
            font=("Segoe UI", 11),
            corner_radius=8,
        )
        self.chat_history.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        input_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        input_frame.pack(fill="x", padx=8, pady=4)

        self.entry_chat = ctk.CTkEntry(
            input_frame,
            placeholder_text="Pergunte algo ao Gemini...",
            height=38,
            fg_color="#334155",
            text_color="#F8FAFC",
            border_color="#334155",
        )
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_chat.bind("<Return>", lambda e: self.enviar_mensagem_ai())

        btn_enviar = ctk.CTkButton(
            input_frame,
            text="Enviar",
            width=80,
            height=38,
            command=self.enviar_mensagem_ai,
        )
        btn_enviar.pack(side="right")
        self.dynamic_accent_buttons.append(btn_enviar)

    def montar_aba_config(self):
        container = ctk.CTkScrollableFrame(self.tab_config, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            container,
            text="Configurações da IA (Gemini)",
            font=("Segoe UI", 13, "bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w", pady=(0, 4))

        self.entry_api_key = ctk.CTkEntry(
            container,
            placeholder_text="Insira sua Chave de API do Gemini...",
            height=36,
            fg_color="#334155",
            border_color="#334155",
        )
        self.entry_api_key.pack(fill="x", pady=4)

        btn_salvar_key = ctk.CTkButton(
            container,
            text="Salvar Chave API",
            height=32,
            command=self.salvar_chave_gemini,
        )
        btn_salvar_key.pack(anchor="e", pady=6)
        self.dynamic_accent_buttons.append(btn_salvar_key)

        ctk.CTkLabel(
            container,
            text="Personalização de Cores",
            font=("Segoe UI", 13, "bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w", pady=(16, 4))

        frame_cores = ctk.CTkFrame(container, fg_color="transparent")
        frame_cores.pack(fill="x", pady=4)

        for nome, dados in COLOR_THEMES.items():
            btn_c = ctk.CTkButton(
                frame_cores,
                text=nome.capitalize(),
                fg_color=dados["primary"],
                hover_color=dados["hover"],
                width=80,
                height=32,
                command=lambda c=nome: self.aplicar_cor_acento(c),
            )
            btn_c.pack(side="left", padx=4)

    def salvar_chave_gemini(self):
        nova_key = self.entry_api_key.get().strip()
        if self.controller.perfil_ativo:
            self.controller.perfil_ativo["gemini_key"] = nova_key
            AccountManager.salvar_dados(self.controller.dados_config)
            self.controller.atualizar_gemini_client(nova_key)
            self.chat_history.insert("end", "Sistema: Chave de API atualizada com sucesso!\n\n")

    def enviar_mensagem_ai(self):
        msg = self.entry_chat.get().strip()
        if not msg:
            return

        self.chat_history.insert("end", f"Você: {msg}\n")
        self.entry_chat.delete(0, "end")

        if not self.controller.gemini_client:
            self.chat_history.insert(
                "end",
                "Sistema: Adicione uma Chave API do Gemini válida nas Configurações.\n\n",
            )
            return

        def processar():
            try:
                resposta = self.controller.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=msg,
                )
                texto_resposta = resposta.text
            except Exception as e:
                texto_resposta = f"Erro na requisição: {e}"

            # Atualização segura na Thread principal
            self.after(0, lambda: self._atualizar_chat_resposta(texto_resposta))

        threading.Thread(target=processar, daemon=True).start()

    def _atualizar_chat_resposta(self, texto):
        self.chat_history.insert("end", f"Gemini: {texto}\n\n")
        self.chat_history.see("end")

    def navegar_para(self, url):
        self.tabview.set("🌐 Navegador")
        self.browser.load_website(url)

    def executar_busca_universal(self):
        query = self.entry_universal.get().strip()
        if not query:
            return

        self.tabview.set("🌐 Navegador")
        if query.startswith("http://") or query.startswith("https://"):
            url = query
        elif "." in query and " " not in query:
            url = f"https://{query}"
        else:
            query_encoded = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={query_encoded}"

        self.browser.load_website(url)


class OmniOverlay(ctk.CTk):
    """Janela Principal que Gerencia os Frames de Navegação."""

    def __init__(self):
        super().__init__()

        self.title("OmniOverlay")
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.attributes("-alpha", 0.98)

        self.dados_config = AccountManager.carregar_dados()
        self.perfil_ativo = None
        self.gemini_client = None
        self.visivel = True

        self.frame_seletor = ProfileSelectorFrame(self, self)
        self.frame_dashboard = DashboardFrame(self, self)

        self.abrir_seletor_perfis()

    def centralizar_janela(self, largura, altura):
        self.geometry(f"{largura}x{altura}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.winfo_screenheight() // 2) - (altura // 2)
        self.geometry(f"+{x}+{y}")

    def abrir_seletor_perfis(self):
        self.frame_dashboard.pack_forget()
        self.centralizar_janela(450, 580)
        self.frame_seletor.pack(fill="both", expand=True)
        self.frame_seletor.atualizar_lista()

    def entrar_no_perfil(self, perfil):
        self.perfil_ativo = perfil
        self.dados_config["ultimo_perfil"] = perfil["id"]
        AccountManager.salvar_dados(self.dados_config)

        self.atualizar_gemini_client(perfil.get("gemini_key", ""))

        self.frame_seletor.pack_forget()
        self.centralizar_janela(920, 800)
        self.frame_dashboard.pack(fill="both", expand=True)
        self.frame_dashboard.carregar_perfil(perfil)

    def atualizar_gemini_client(self, api_key):
        if api_key:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"[ERRO] Falha ao inicializar Gemini: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None

    def alternar_visibilidade(self):
        if self.visivel:
            self.withdraw()
            self.visivel = False
        else:
            self.deiconify()
            self.attributes("-topmost", True)
            self.visivel = True


def escutar_teclado(app):
    teclas = set()

    def on_press(key):
        if key in (
            keyboard.Key.alt_l,
            keyboard.Key.alt_r,
            keyboard.Key.alt_gr,
        ) or (hasattr(key, "char") and key.char and key.char.lower() == "z"):
            teclas.add(key)

        tem_alt = any(
            k in teclas
            for k in (
                keyboard.Key.alt_l,
                keyboard.Key.alt_r,
                keyboard.Key.alt_gr,
            )
        )
        tem_z = any(
            hasattr(k, "char") and k.char and k.char.lower() == "z" for k in teclas
        )

        if tem_alt and tem_z:
            app.alternar_visibilidade()

    def on_release(key):
        teclas.discard(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    app = OmniOverlay()

    thread_teclado = threading.Thread(
        target=escutar_teclado, args=(app,), daemon=True
    )
    thread_teclado.start()

    app.mainloop()