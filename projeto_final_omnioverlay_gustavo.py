"""
===============================================================================
PROJETO: OmniOverlay - Modern SaaS HUD (Família, IA & Streaming)
===============================================================================
"""

import json
import os
import threading
import customtkinter as ctk
from PIL import Image, ImageDraw
from pynput import keyboard
from tkinter import filedialog

# Módulo para o Navegador Embutido
from tkinterweb import HtmlFrame

from google import genai

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("dark")

COLOR_THEMES = {
    "azul": {"primary": "#2563EB", "hover": "#1D4ED8"},
    "vermelho": {"primary": "#DC2626", "hover": "#B91C1C"},
    "verde": {"primary": "#16A34A", "hover": "#15803D"},
    "roxo": {"primary": "#9333EA", "hover": "#7E22CE"},
}

CONFIG_FILE = "app_config.json"


class OmniOverlay(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("OmniOverlay Dashboard")
        self.geometry("900x780")
        self.minsize(800, 600)

        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.attributes("-alpha", 0.98)

        # Estados e Variáveis
        self._offset_x = 0
        self._offset_y = 0
        self.visivel = True
        self.modo_cinema_ativo = False
        self.client_gemini = None

        self.modo_tema = "dark"
        self.cor_acento = "azul"
        self.accounts = {"google": True, "microsoft": False, "github": False}
        self.api_keys = {"gemini": ""}

        self.carregar_configuracoes()

        # Dicionários de elementos atualizáveis
        self.componentes_tema = []
        self.dynamic_accent_buttons = []
        self.btn_accounts = {}

        # Ajusta paleta inicial
        self.definir_paleta_cores(self.modo_tema)

        # Construção da Interface
        self.criar_interface()
        self.iniciar_gemini()
        self.aplicar_cor_acento(self.cor_acento)

    # -------------------------------------------------------------------------
    # Sistema de Cores e Temas
    # -------------------------------------------------------------------------
    def definir_paleta_cores(self, modo):
        self.modo_tema = modo
        if modo == "dark":
            self.bg_principal = "#0F172A"  # Slate 900
            self.bg_card = "#1E293B"  # Slate 800
            self.bg_input = "#334155"  # Slate 700
            self.border_card = "#334155"
            self.txt_principal = "#F8FAFC"  # Slate 50
            self.txt_secundario = "#94A3B8"  # Slate 400
        else:  # Modo Claro Corrigido (Alto Contraste)
            self.bg_principal = "#F8FAFC"  # Slate 50
            self.bg_card = "#FFFFFF"  # Branco puro
            self.bg_input = "#F1F5F9"  # Slate 100
            self.border_card = "#E2E8F0"  # Slate 200
            self.txt_principal = "#0F172A"  # Slate 900 (Contraste forte)
            self.txt_secundario = "#475569"  # Slate 600

        self.configure(fg_color=self.bg_principal)

    def alternar_tema(self, novo_modo):
        modo_str = "dark" if novo_modo.lower() in ["escuro", "dark"] else "light"
        ctk.set_appearance_mode(modo_str)
        self.definir_paleta_cores(modo_str)

        # Atualiza a cor de fundo de todos os containers registrados
        for comp in self.componentes_tema:
            if hasattr(comp, "configure"):
                comp.configure(
                    fg_color=self.bg_card, border_color=self.border_card
                )

        # Atualiza labels e entradas textuais
        self.lbl_titulo.configure(text_color=self.txt_principal)
        self.entry_universal.configure(
            fg_color=self.bg_input,
            text_color=self.txt_principal,
            border_color=self.border_card,
        )
        self.txt_resposta_ia.configure(
            fg_color=self.bg_input, text_color=self.txt_principal
        )

        self.salvar_configuracoes()

    def aplicar_cor_acento(self, nome_cor):
        self.cor_acento = nome_cor
        cor = COLOR_THEMES.get(nome_cor, COLOR_THEMES["azul"])

        for btn in self.dynamic_accent_buttons:
            btn.configure(fg_color=cor["primary"], hover_color=cor["hover"])

        for chave in self.accounts:
            self.atualizar_botao_conta(chave)

        self.salvar_configuracoes()

    # -------------------------------------------------------------------------
    # Movimentação do HUD
    # -------------------------------------------------------------------------
    def iniciar_arraste(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def arrastar_janela(self, event):
        if not self.modo_cinema_ativo:
            x = self.winfo_x() + (event.x - self._offset_x)
            y = self.winfo_y() + (event.y - self._offset_y)
            self.geometry(f"+{x}+{y}")

    # -------------------------------------------------------------------------
    # Interface Gráfica Principal
    # -------------------------------------------------------------------------
    def criar_interface(self):
        # 1. BARRA SUPERIOR (HEADER)
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=self.bg_card,
            corner_radius=12,
            border_color=self.border_card,
            border_width=1,
            height=60,
        )
        self.header_frame.pack(fill="x", padx=16, pady=(16, 8))
        self.componentes_tema.append(self.header_frame)

        self.header_frame.bind("<Button-1>", self.iniciar_arraste)
        self.header_frame.bind("<B1-Motion>", self.arrastar_janela)

        # Avatar
        self.lbl_avatar = ctk.CTkLabel(
            self.header_frame,
            text="😊",
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
            font=("Segoe UI", 16, "bold"),
            text_color=self.txt_principal,
        )
        self.lbl_titulo.pack(side="left", padx=2)

        # Botão Fechar HUD
        btn_fechar = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Segoe UI", 14, "bold"),
            command=self.destroy,
        )
        btn_fechar.pack(side="right", padx=12)

        # Botão Modo Cinema
        self.btn_modo_cinema = ctk.CTkButton(
            self.header_frame,
            text="🍿 Modo Cinema",
            height=36,
            corner_radius=8,
            fg_color="#E50914",
            hover_color="#B20710",
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.alternar_modo_cinema,
        )
        self.btn_modo_cinema.pack(side="right", padx=6)

        # 2. BARRA DE PESQUISA UNIVERSAL FIXA
        self.frame_busca = ctk.CTkFrame(
            self,
            fg_color=self.bg_card,
            corner_radius=12,
            border_color=self.border_card,
            border_width=1,
        )
        self.frame_busca.pack(fill="x", padx=16, pady=4)
        self.componentes_tema.append(self.frame_busca)

        self.seletor_modo = ctk.CTkOptionMenu(
            self.frame_busca,
            values=["🌐 Pesquisar na Web", "🤖 Perguntar para a IA"],
            width=170,
            height=38,
            corner_radius=8,
            fg_color=self.bg_input,
            button_color="#475569",
            font=("Segoe UI", 11, "bold"),
        )
        self.seletor_modo.pack(side="left", padx=8, pady=8)

        self.entry_universal = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Digite um endereço web ou pergunta...",
            height=38,
            corner_radius=8,
            fg_color=self.bg_input,
            text_color=self.txt_principal,
            border_color=self.border_card,
            font=("Segoe UI", 11),
        )
        self.entry_universal.pack(
            side="left", fill="x", expand=True, padx=4, pady=8
        )
        self.entry_universal.bind(
            "<Return>", lambda e: self.executar_busca_universal()
        )

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

        # Resposta da IA (Oculta por padrão)
        self.frame_ia_resposta = ctk.CTkFrame(
            self,
            fg_color=self.bg_card,
            corner_radius=12,
            border_color="#38BDF8",
            border_width=1,
        )
        self.componentes_tema.append(self.frame_ia_resposta)

        lbl_ia_head = ctk.CTkLabel(
            self.frame_ia_resposta,
            text="🤖 RESPOSTA DA IA",
            font=("Segoe UI", 11, "bold"),
            text_color="#38BDF8",
        )
        lbl_ia_head.pack(anchor="w", padx=12, pady=(6, 2))

        btn_fechar_ia = ctk.CTkButton(
            self.frame_ia_resposta,
            text="✕",
            width=24,
            height=24,
            corner_radius=6,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self.ocultar_painel_ia,
        )
        btn_fechar_ia.place(relx=0.96, rely=0.05)

        self.txt_resposta_ia = ctk.CTkTextbox(
            self.frame_ia_resposta,
            height=100,
            corner_radius=8,
            fg_color=self.bg_input,
            text_color=self.txt_principal,
            font=("Segoe UI", 11),
        )
        self.txt_resposta_ia.pack(fill="x", padx=12, pady=(2, 8))

        # 3. NAVEGAÇÃO POR ABAS (HUB MODERNO)
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            fg_color=self.bg_card,
            border_color=self.border_card,
            border_width=1,
        )
        self.tabview.pack(
            fill="both", expand=True, padx=16, pady=(8, 16)
        )
        self.componentes_tema.append(self.tabview)

        # Criando as abas
        self.tab_web = self.tabview.add("🌐 Navegador")
        self.tab_streaming = self.tabview.add("🎬 Streaming")
        self.tab_midia = self.tabview.add("🎵 Tocador")
        self.tab_config = self.tabview.add("⚙️ Opções & Contas")

        # Configurar conteúdo de cada aba
        self.montar_aba_navegador()
        self.montar_aba_streaming()
        self.montar_aba_midia()
        self.montar_aba_configuracoes()

    # -------------------------------------------------------------------------
    # Conteúdo das Abas
    # -------------------------------------------------------------------------
    def montar_aba_navegador(self):
        self.browser = HtmlFrame(self.tab_web)
        self.browser.pack(fill="both", expand=True)
        self.browser.load_website("https://www.google.com/safeSearch")

    def montar_aba_streaming(self):
        lbl = ctk.CTkLabel(
            self.tab_streaming,
            text="Plataformas de Streaming",
            font=("Segoe UI", 14, "bold"),
            text_color=self.txt_principal,
        )
        lbl.pack(anchor="w", padx=16, pady=(12, 16))

        grid_frame = ctk.CTkFrame(self.tab_streaming, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=16)

        servicos = [
            ("🔴 Netflix", "https://www.netflix.com", "#E50914"),
            ("▶️ YouTube", "https://www.youtube.com", "#FF0000"),
            ("✨ Disney+", "https://www.disneyplus.com", "#113CCF"),
            ("💜 Twitch", "https://www.twitch.tv", "#9146FF"),
            ("📦 Prime Video", "https://www.primevideo.com", "#00A8E1"),
            ("🟣 Max", "https://www.max.com", "#002BE7"),
        ]

        # Botões organizados em Grade (Grid)
        col, row = 0, 0
        for nome, url, cor in servicos:
            btn = ctk.CTkButton(
                grid_frame,
                text=nome,
                height=50,
                corner_radius=10,
                fg_color=self.bg_input,
                hover_color=cor,
                text_color=self.txt_principal,
                font=("Segoe UI", 12, "bold"),
                command=lambda u=url: self.abrir_streaming_e_navegar(u),
            )
            btn.grid(
                row=row, column=col, padx=8, pady=8, sticky="nsew"
            )

            col += 1
            if col > 2:
                col = 0
                row += 1

        for i in range(3):
            grid_frame.grid_columnconfigure(i, weight=1)

    def montar_aba_midia(self):
        frame_player = ctk.CTkFrame(
            self.tab_midia, fg_color=self.bg_input, corner_radius=12
        )
        frame_player.pack(fill="x", padx=16, pady=20)

        self.lbl_musica_titulo = ctk.CTkLabel(
            frame_player,
            text="Tocador de Mídia",
            font=("Segoe UI", 14, "bold"),
            text_color=self.txt_principal,
        )
        self.lbl_musica_titulo.pack(pady=(16, 2))

        self.lbl_artista = ctk.CTkLabel(
            frame_player,
            text="Nenhuma faixa em execução",
            font=("Segoe UI", 11),
            text_color=self.txt_secundario,
        )
        self.lbl_artista.pack(pady=(0, 12))

        self.slider_progresso = ctk.CTkProgressBar(
            frame_player,
            height=6,
            progress_color="#22C55E",
            fg_color="#475569",
            corner_radius=3,
        )
        self.slider_progresso.pack(fill="x", padx=30, pady=8)
        self.slider_progresso.set(0.0)

        frame_ctrl = ctk.CTkFrame(frame_player, fg_color="transparent")
        frame_ctrl.pack(pady=16)

        ctk.CTkButton(
            frame_ctrl,
            text="⏮",
            width=50,
            height=40,
            corner_radius=20,
            fg_color="#475569",
            command=lambda: self.lbl_musica_titulo.configure(
                text="Faixa Anterior"
            ),
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            frame_ctrl,
            text="⏯",
            width=60,
            height=40,
            corner_radius=20,
            fg_color="#22C55E",
            hover_color="#16A34A",
            font=("Segoe UI", 14, "bold"),
            command=lambda: self.lbl_musica_titulo.configure(
                text="Tocando / Pausado"
            ),
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            frame_ctrl,
            text="⏭",
            width=50,
            height=40,
            corner_radius=20,
            fg_color="#475569",
            command=lambda: self.lbl_musica_titulo.configure(
                text="Próxima Faixa"
            ),
        ).pack(side="left", padx=6)

    def montar_aba_configuracoes(self):
        container = ctk.CTkScrollableFrame(
            self.tab_config, fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # CARD 1: PERFIL
        card_perfil = ctk.CTkFrame(
            container, fg_color=self.bg_input, corner_radius=10
        )
        card_perfil.pack(fill="x", pady=6, ipady=6)

        ctk.CTkLabel(
            card_perfil,
            text="Perfil do Usuário",
            font=("Segoe UI", 12, "bold"),
            text_color=self.txt_principal,
        ).pack(anchor="w", padx=12, pady=(6, 2))

        btn_foto = ctk.CTkButton(
            card_perfil,
            text="Alterar Foto de Perfil",
            height=34,
            font=("Segoe UI", 10, "bold"),
            command=self.selecionar_foto_perfil,
        )
        btn_foto.pack(anchor="w", padx=12, pady=4)
        self.dynamic_accent_buttons.append(btn_foto)

        self.entry_nome_usuario = ctk.CTkEntry(
            card_perfil,
            placeholder_text="Nome do Usuário",
            height=34,
            font=("Segoe UI", 10),
        )
        self.entry_nome_usuario.pack(fill="x", padx=12, pady=4)

        # CARD 2: APARÊNCIA & CORES
        card_visual = ctk.CTkFrame(
            container, fg_color=self.bg_input, corner_radius=10
        )
        card_visual.pack(fill="x", pady=6, ipady=6)

        ctk.CTkLabel(
            card_visual,
            text="Aparência e Cores",
            font=("Segoe UI", 12, "bold"),
            text_color=self.txt_principal,
        ).pack(anchor="w", padx=12, pady=(6, 2))

        self.switch_tema = ctk.CTkOptionMenu(
            card_visual,
            values=["Escuro", "Claro"],
            height=32,
            font=("Segoe UI", 10),
            command=self.alternar_tema,
        )
        self.switch_tema.pack(anchor="w", padx=12, pady=4)
        if self.modo_tema == "light":
            self.switch_tema.set("Claro")

        ctk.CTkLabel(
            card_visual,
            text="Cor de Acento do App:",
            font=("Segoe UI", 10),
            text_color=self.txt_secundario,
        ).pack(anchor="w", padx=12, pady=(4, 0))

        frame_cores = ctk.CTkFrame(card_visual, fg_color="transparent")
        frame_cores.pack(anchor="w", padx=12, pady=4)

        for nome_c, chave_c in [
            ("Azul", "azul"),
            ("Vermelho", "vermelho"),
            ("Verde", "verde"),
            ("Roxo", "roxo"),
        ]:
            ctk.CTkButton(
                frame_cores,
                text=nome_c,
                width=75,
                height=30,
                corner_radius=6,
                fg_color=COLOR_THEMES[chave_c]["primary"],
                hover_color=COLOR_THEMES[chave_c]["hover"],
                font=("Segoe UI", 10, "bold"),
                command=lambda k=chave_c: self.aplicar_cor_acento(k),
            ).pack(side="left", padx=2)

        # CARD 3: CONTAS & CHAVE IA
        card_contas = ctk.CTkFrame(
            container, fg_color=self.bg_input, corner_radius=10
        )
        card_contas.pack(fill="x", pady=6, ipady=6)

        ctk.CTkLabel(
            card_contas,
            text="Contas & Chave IA",
            font=("Segoe UI", 12, "bold"),
            text_color=self.txt_principal,
        ).pack(anchor="w", padx=12, pady=(6, 2))

        for chave, nome in [
            ("google", "Google"),
            ("microsoft", "Microsoft"),
            ("github", "GitHub"),
        ]:
            row_c = ctk.CTkFrame(card_contas, fg_color="transparent")
            row_c.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(
                row_c,
                text=nome,
                font=("Segoe UI", 10),
                text_color=self.txt_principal,
            ).pack(side="left")

            btn_acc = ctk.CTkButton(
                row_c,
                text="",
                width=100,
                height=28,
                font=("Segoe UI", 9, "bold"),
                command=lambda k=chave: self.toggle_conta(k),
            )
            btn_acc.pack(side="right")
            self.btn_accounts[chave] = btn_acc

        self.entry_gemini_key = ctk.CTkEntry(
            card_contas,
            placeholder_text="Chave de API do Gemini",
            height=34,
            show="*",
            font=("Segoe UI", 10),
        )
        self.entry_gemini_key.pack(fill="x", padx=12, pady=(8, 4))
        self.entry_gemini_key.insert(
            0, self.api_keys.get("gemini", os.environ.get("GEMINI_API_KEY", ""))
        )

        btn_salvar = ctk.CTkButton(
            card_contas,
            text="Salvar Alterações",
            height=36,
            font=("Segoe UI", 10, "bold"),
            command=self.salvar_contas,
        )
        btn_salvar.pack(fill="x", padx=12, pady=8)
        self.dynamic_accent_buttons.append(btn_salvar)

    # -------------------------------------------------------------------------
    # Operações de Negócio
    # -------------------------------------------------------------------------
    def abrir_streaming_e_navegar(self, url):
        self.tabview.set("🌐 Navegador")
        self.browser.load_website(url)

    def alternar_modo_cinema(self):
        if not self.modo_cinema_ativo:
            self.modo_cinema_ativo = True
            self.frame_busca.pack_forget()
            self.btn_modo_cinema.configure(text="🔙 Sair do Cinema")
            self.tabview.set("🌐 Navegador")
            self.geometry("1024x768")
        else:
            self.modo_cinema_ativo = False
            self.frame_busca.pack(
                fill="x", padx=16, pady=4, after=self.header_frame
            )
            self.btn_modo_cinema.configure(text="🍿 Modo Cinema")
            self.geometry("900x780")

    def executar_busca_universal(self):
        query = self.entry_universal.get().strip()
        if not query:
            return

        modo = self.seletor_modo.get()

        if "Web" in modo:
            self.tabview.set("🌐 Navegador")
            if query.startswith("http://") or query.startswith("https://"):
                url = query
            elif "." in query and " " not in query:
                url = f"https://{query}"
            else:
                url = f"https://www.google.com/search?q={query}&safe=active"

            self.browser.load_website(url)

        elif "IA" in modo:
            self.exibir_painel_ia(query)

    def exibir_painel_ia(self, pergunta):
        self.frame_ia_resposta.pack(
            fill="x", padx=16, pady=4, after=self.frame_busca
        )
        self.txt_resposta_ia.delete("1.0", "end")
        self.txt_resposta_ia.insert(
            "1.0", "🤖 Processando sua pergunta..."
        )

        threading.Thread(
            target=self._processar_pergunta_ia, args=(pergunta,), daemon=True
        ).start()

    def ocultar_painel_ia(self):
        self.frame_ia_resposta.pack_forget()

    def _processar_pergunta_ia(self, pergunta):
        if self.client_gemini:
            try:
                response = self.client_gemini.models.generate_content(
                    model="gemini-2.5-flash", contents=pergunta
                )
                resposta_texto = response.text
            except Exception as e:
                resposta_texto = f"Erro na requisição: {e}"
        else:
            resposta_texto = (
                f"[Modo de Demonstração]\n\nPergunta: '{pergunta}'\n\n"
                "Para respostas reais, adicione sua Chave de API na aba de Opções."
            )

        self.txt_resposta_ia.delete("1.0", "end")
        self.txt_resposta_ia.insert("1.0", resposta_texto)

    def selecionar_foto_perfil(self):
        caminho = filedialog.askopenfilename(
            title="Escolha uma Foto",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")],
        )
        if caminho:
            try:
                img = Image.open(caminho).convert("RGBA").resize((42, 42))
                mascara = Image.new("L", (42, 42), 0)
                ImageDraw.Draw(mascara).ellipse((0, 0, 42, 42), fill=255)
                res = Image.new("RGBA", (42, 42), (0, 0, 0, 0))
                res.paste(img, (0, 0), mask=mascara)

                avatar = ctk.CTkImage(
                    light_image=res, dark_image=res, size=(42, 42)
                )
                self.lbl_avatar.configure(image=avatar, text="")
            except Exception as e:
                print(f"Erro ao carregar avatar: {e}")

    def toggle_conta(self, chave):
        self.accounts[chave] = not self.accounts[chave]
        self.atualizar_botao_conta(chave)
        self.salvar_configuracoes()

    def atualizar_botao_conta(self, chave):
        if chave not in self.btn_accounts:
            return
        btn = self.btn_accounts[chave]
        conectado = self.accounts.get(chave, False)
        cor_tema = COLOR_THEMES.get(self.cor_acento, COLOR_THEMES["azul"])

        if conectado:
            btn.configure(
                text="Conectado",
                fg_color="#FEE2E2",
                hover_color="#FCA5A5",
                text_color="#991B1B",
            )
        else:
            btn.configure(
                text="Conectar",
                fg_color=cor_tema["primary"],
                hover_color=cor_tema["hover"],
                text_color="#FFFFFF",
            )

    def salvar_contas(self):
        gemini_k = self.entry_gemini_key.get().strip()
        nome_user = self.entry_nome_usuario.get().strip()

        if gemini_k:
            self.api_keys["gemini"] = gemini_k
            os.environ["GEMINI_API_KEY"] = gemini_k
            self.iniciar_gemini()

        if nome_user:
            self.lbl_artista.configure(text=f"Usuário: {nome_user}")

        self.salvar_configuracoes()

    def iniciar_gemini(self):
        api_key = self.api_keys.get(
            "gemini", os.environ.get("GEMINI_API_KEY", "")
        )
        if api_key:
            try:
                self.client_gemini = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Erro ao inicializar Gemini: {e}")

    # -------------------------------------------------------------------------
    # Persistência JSON e Atalhos
    # -------------------------------------------------------------------------
    def salvar_configuracoes(self):
        dados = {
            "modo_tema": self.modo_tema,
            "cor_acento": self.cor_acento,
            "accounts": self.accounts,
            "api_keys": self.api_keys,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar JSON: {e}")

    def carregar_configuracoes(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.modo_tema = dados.get("modo_tema", "dark")
                    self.cor_acento = dados.get("cor_acento", "azul")
                    self.accounts = dados.get("accounts", self.accounts)
                    self.api_keys = dados.get("api_keys", self.api_keys)
            except Exception as e:
                print(f"Erro ao ler JSON: {e}")

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

    with keyboard.Listener(
        on_press=on_press, on_release=on_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    app = OmniOverlay()
    thread_teclado = threading.Thread(
        target=escutar_teclado, args=(app,), daemon=True
    )
    thread_teclado.start()
    app.mainloop()