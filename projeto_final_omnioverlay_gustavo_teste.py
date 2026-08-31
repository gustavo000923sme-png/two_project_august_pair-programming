"""
===============================================================================
PROJETO: OmniOverlay - HUD Familiar com Streaming & Modo Cinema
===============================================================================
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw

# Módulo para o Navegador Embutido (pip install tkinterweb)
from tkinterweb import HtmlFrame

from google import genai
from pynput import keyboard

# Configurações Iniciais de Aparência
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class OmniOverlay(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Dimensões Iniciais
        self.title("OmniOverlay HUD - Edição Família & Streaming")
        self.geometry("840x760")

        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.attributes("-alpha", 0.96)

        # Cores Dinâmicas dos Modos
        self.atualizar_cores_tema("dark")

        # Variáveis de Controle
        self._offset_x = 0
        self._offset_y = 0
        self.visivel = True
        self.web_visivel = True
        self.config_visivel = False
        self.modo_cinema_ativo = False
        self.client_gemini = None
        self.imagem_perfil = None

        # Monta a Interface
        self.criar_interface()
        self.iniciar_gemini()

    # -------------------------------------------------------------------------
    # Função para Recortar Imagem em Círculo Perfeito
    # -------------------------------------------------------------------------
    def criar_avatar_circular(self, caminho_imagem, tamanho=(44, 44)):
        try:
            img = Image.open(caminho_imagem).convert("RGBA")
            img = img.resize(tamanho, Image.Resampling.LANCZOS)

            mascara = Image.new("L", tamanho, 0)
            draw = ImageDraw.Draw(mascara)
            draw.ellipse((0, 0, tamanho[0], tamanho[1]), fill=255)

            resultado = Image.new("RGBA", tamanho, (0, 0, 0, 0))
            resultado.paste(img, (0, 0), mask=mascara)
            return ctk.CTkImage(light_image=resultado, dark_image=resultado, size=tamanho)
        except Exception as e:
            print(f"Erro ao processar avatar: {e}")
            return None

    # -------------------------------------------------------------------------
    # Gerenciamento de Tema (Claro / Escuro)
    # -------------------------------------------------------------------------
    def atualizar_cores_tema(self, modo):
        if modo == "dark":
            self.bg_principal = "#0F172A"
            self.bg_card = "#1E293B"
            self.border_card = "#334155"
            self.txt_principal = "#F8FAFC"
            self.txt_secundario = "#94A3B8"
        else:  # light
            self.bg_principal = "#F1F5F9"
            self.bg_card = "#FFFFFF"
            self.border_card = "#E2E8F0"
            self.txt_principal = "#0F172A"
            self.txt_secundario = "#64748B"

        self.configure(fg_color=self.bg_principal)

    def alternar_tema(self, novo_modo):
        ctk.set_appearance_mode(novo_modo)
        modo_str = "dark" if novo_modo.lower() in ["escuro", "dark"] else "light"
        self.atualizar_cores_tema(modo_str)

        cards = [
            self.header_frame, self.frame_spotify, self.frame_streaming,
            self.frame_busca_universal, self.frame_browser_container,
            self.frame_config, self.frame_ia_resposta
        ]
        for card in cards:
            if card and hasattr(card, "configure"):
                card.configure(fg_color=self.bg_card, border_color=self.border_card)

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
    # Interface Gráfica
    # -------------------------------------------------------------------------
    def criar_interface(self):
        # 1. CABEÇALHO DA CENTRAL (HEADER AMIGÁVEL)
        self.header_frame = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16, border_color=self.border_card, border_width=1, height=54
        )
        self.header_frame.pack(fill="x", padx=12, pady=(12, 6))

        self.header_frame.bind("<Button-1>", self.iniciar_arraste)
        self.header_frame.bind("<B1-Motion>", self.arrastar_janela)

        # Avatar Circular do Usuário
        self.lbl_avatar = ctk.CTkLabel(
            self.header_frame,
            text="😊",
            width=44,
            height=44,
            corner_radius=22,
            fg_color="#38BDF8",
            text_color="#FFFFFF",
            font=("Segoe UI", 20)
        )
        self.lbl_avatar.pack(side="left", padx=(10, 8))

        lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="OmniOverlay",
            font=("Segoe UI", 14, "bold"),
            text_color="#38BDF8",
        )
        lbl_titulo.pack(side="left", padx=(2, 10))
        lbl_titulo.bind("<Button-1>", self.iniciar_arraste)
        lbl_titulo.bind("<B1-Motion>", self.arrastar_janela)

        # Botão Toggle Web
        self.btn_toggle_web = ctk.CTkButton(
            self.header_frame,
            text="🖥️ Minimizar Web",
            width=115,
            height=30,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            font=("Segoe UI", 10, "bold"),
            command=self.alternar_web,
        )
        self.btn_toggle_web.pack(side="left", padx=3)

        # Botão Modo Cinema
        self.btn_modo_cinema = ctk.CTkButton(
            self.header_frame,
            text="🍿 Modo Cinema",
            width=110,
            height=30,
            corner_radius=8,
            fg_color="#E50914",
            hover_color="#B20710",
            text_color="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            command=self.alternar_modo_cinema,
        )
        self.btn_modo_cinema.pack(side="left", padx=3)

        # Botão Opções
        self.btn_config = ctk.CTkButton(
            self.header_frame,
            text="⚙️ Opções",
            width=85,
            height=30,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            font=("Segoe UI", 10, "bold"),
            command=self.alternar_painel_config,
        )
        self.btn_config.pack(side="left", padx=3)

        btn_fechar = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=30,
            height=28,
            corner_radius=8,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=("Arial", 12, "bold"),
            command=self.destroy,
        )
        btn_fechar.pack(side="right", padx=10)

        # 2. PAINEL DE CONFIGURAÇÕES (INICIALMENTE OCULTO)
        self.frame_config = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16, border_color="#38BDF8", border_width=1
        )
        self.criar_painel_configuracoes()

        # 3. MINI HUB SPOTIFY / MÚSICA
        self.frame_spotify = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16, border_color="#22C55E", border_width=1
        )
        self.frame_spotify.pack(fill="x", padx=12, pady=4)

        sub_spotify = ctk.CTkFrame(self.frame_spotify, fg_color="transparent")
        sub_spotify.pack(fill="x", padx=12, pady=6)

        self.lbl_capa = ctk.CTkLabel(
            sub_spotify, text="🎵", width=42, height=42, corner_radius=10,
            fg_color="#22C55E", font=("Segoe UI", 18), text_color="#FFFFFF"
        )
        self.lbl_capa.pack(side="left", padx=(0, 10))

        frame_info_musica = ctk.CTkFrame(sub_spotify, fg_color="transparent")
        frame_info_musica.pack(side="left", fill="x", expand=True)

        self.lbl_musica_titulo = ctk.CTkLabel(
            frame_info_musica, text="Tocador de Música", font=("Segoe UI", 11, "bold"), anchor="w"
        )
        self.lbl_musica_titulo.pack(fill="x")

        self.lbl_artista = ctk.CTkLabel(
            frame_info_musica, text="Nenhuma faixa em execução",
            font=("Segoe UI", 9), text_color="#94A3B8", anchor="w"
        )
        self.lbl_artista.pack(fill="x")

        self.slider_progresso = ctk.CTkProgressBar(
            frame_info_musica, height=5, progress_color="#22C55E", fg_color="#334155", corner_radius=3
        )
        self.slider_progresso.pack(fill="x", pady=(3, 0))
        self.slider_progresso.set(0.0)

        frame_controles = ctk.CTkFrame(sub_spotify, fg_color="transparent")
        frame_controles.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            frame_controles, text="⏮", width=32, height=32, corner_radius=16,
            fg_color="#334155", hover_color="#475569", command=self.spotify_anterior
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            frame_controles, text="⏯", width=38, height=32, corner_radius=16,
            fg_color="#22C55E", hover_color="#16A34A", font=("Segoe UI", 11, "bold"),
            command=self.spotify_play_pause
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            frame_controles, text="⏭", width=32, height=32, corner_radius=16,
            fg_color="#334155", hover_color="#475569", command=self.spotify_proxima
        ).pack(side="left", padx=2)

        # 4. ABA DE SERVIÇOS DE STREAMING (ATALHOS RÁPIDOS)
        self.frame_streaming = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16, border_color="#E50914", border_width=1
        )
        self.frame_streaming.pack(fill="x", padx=12, pady=4)

        sub_stream = ctk.CTkFrame(self.frame_streaming, fg_color="transparent")
        sub_stream.pack(fill="x", padx=10, pady=6)

        lbl_stream = ctk.CTkLabel(sub_stream, text="🎬 Streaming:", font=("Segoe UI", 10, "bold"), text_color="#E50914")
        lbl_stream.pack(side="left", padx=(4, 8))

        servicos = [
            ("🔴 Netflix", "https://www.netflix.com", "#E50914"),
            ("▶️ YouTube", "https://www.youtube.com", "#FF0000"),
            ("✨ Disney+", "https://www.disneyplus.com", "#113CCF"),
            ("💜 Twitch", "https://www.twitch.tv", "#9146FF"),
            ("📦 Prime Video", "https://www.primevideo.com", "#00A8E1"),
            ("🟣 Max", "https://www.max.com", "#002BE7")
        ]

        for nome, url, cor in servicos:
            btn = ctk.CTkButton(
                sub_stream, text=nome, height=28, corner_radius=8,
                fg_color="#334155", hover_color=cor, font=("Segoe UI", 9, "bold"),
                command=lambda u=url: self.abrir_site_streaming(u)
            )
            btn.pack(side="left", padx=3)

        # 5. BARRA DE PESQUISA UNIVERSAL
        self.frame_busca_universal = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16, border_color=self.border_card, border_width=1
        )
        self.frame_busca_universal.pack(fill="x", padx=12, pady=4)

        self.seletor_modo = ctk.CTkOptionMenu(
            self.frame_busca_universal,
            values=["🌐 Pesquisar na Web", "🤖 Perguntar para a IA"],
            width=160,
            height=34,
            corner_radius=10,
            fg_color="#334155",
            button_color="#475569",
            button_hover_color="#38BDF8",
            dropdown_fg_color="#1E293B",
            font=("Segoe UI", 10, "bold"),
        )
        self.seletor_modo.pack(side="left", padx=(8, 4), pady=6)

        self.entry_universal = ctk.CTkEntry(
            self.frame_busca_universal,
            placeholder_text="Digite um site, filme, vídeo ou dúvida...",
            height=34,
            corner_radius=10,
            border_color="#334155",
            font=("Segoe UI", 10),
        )
        self.entry_universal.pack(side="left", fill="x", expand=True, padx=4, pady=6)
        self.entry_universal.bind("<Return>", lambda event: self.executar_busca_universal())

        btn_executar = ctk.CTkButton(
            self.frame_busca_universal,
            text="Buscar 🔍",
            width=90,
            height=34,
            corner_radius=10,
            fg_color="#38BDF8",
            hover_color="#0284C7",
            text_color="#0F172A",
            font=("Segoe UI", 10, "bold"),
            command=self.executar_busca_universal,
        )
        btn_executar.pack(side="right", padx=(4, 8), pady=6)

        # 6. PAINEL DA IA (OCULTO POR PADRÃO)
        self.frame_ia_resposta = ctk.CTkFrame(
            self, fg_color=self.bg_card, corner_radius=16, border_color="#38BDF8", border_width=1
        )

        lbl_ia_head = ctk.CTkLabel(
            self.frame_ia_resposta, text="🤖 RESPOSTA DA IA:", font=("Segoe UI", 10, "bold"), text_color="#38BDF8"
        )
        lbl_ia_head.pack(anchor="w", padx=12, pady=(6, 2))

        btn_fechar_ia = ctk.CTkButton(
            self.frame_ia_resposta, text="✕", width=20, height=20, corner_radius=6,
            fg_color="#EF4444", hover_color="#DC2626", command=self.ocultar_painel_ia
        )
        btn_fechar_ia.place(relx=0.96, rely=0.05)

        self.txt_resposta_ia = ctk.CTkTextbox(
            self.frame_ia_resposta, height=90, corner_radius=10, border_color="#334155", font=("Segoe UI", 10)
        )
        self.txt_resposta_ia.pack(fill="x", padx=12, pady=(2, 6))

        # 7. CONTAINER DO NAVEGADOR WEB EMBUTIDO
        self.frame_browser_container = ctk.CTkFrame(
            self, corner_radius=16, fg_color=self.bg_card, border_color=self.border_card, border_width=1
        )
        self.frame_browser_container.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self.browser = HtmlFrame(self.frame_browser_container)
        self.browser.pack(fill="both", expand=True)
        self.browser.load_website("https://www.google.com/safeSearch")

    # -------------------------------------------------------------------------
    # Função para Abrir Streaming
    # -------------------------------------------------------------------------
    def abrir_site_streaming(self, url):
        if not self.web_visivel:
            self.alternar_web()
        self.browser.load_website(url)

    # -------------------------------------------------------------------------
    # Modo Cinema / Tela Cheia
    # -------------------------------------------------------------------------
    def alternar_modo_cinema(self):
        if not self.modo_cinema_ativo:
            # Ativar Modo Cinema
            self.modo_cinema_ativo = True
            if not self.web_visivel:
                self.alternar_web()

            # Ocultar outros módulos para focar no vídeo
            self.frame_spotify.pack_forget()
            self.frame_streaming.pack_forget()
            self.frame_busca_universal.pack_forget()
            if self.config_visivel:
                self.frame_config.pack_forget()

            self.btn_modo_cinema.configure(text="🔙 Sair do Cinema", fg_color="#334155")
            self.geometry("1024x768")
        else:
            # Sair do Modo Cinema
            self.modo_cinema_ativo = False
            self.btn_modo_cinema.configure(text="🍿 Modo Cinema", fg_color="#E50914")

            # Restaurar visibilidade dos módulos
            if self.chk_spotify.get() == 1:
                self.frame_spotify.pack(fill="x", padx=12, pady=4, after=self.header_frame)
            self.frame_streaming.pack(fill="x", padx=12, pady=4, after=self.frame_spotify)
            self.frame_busca_universal.pack(fill="x", padx=12, pady=4, after=self.frame_streaming)
            self.geometry("840x760")

    # -------------------------------------------------------------------------
    # Painel de Configurações & Fotos de Perfil
    # -------------------------------------------------------------------------
    def criar_painel_configuracoes(self):
        lbl_title_cfg = ctk.CTkLabel(
            self.frame_config, text="⚙️ CONFIGURAÇÕES E PERFIL DA FAMÍLIA", font=("Segoe UI", 11, "bold"), text_color="#38BDF8"
        )
        lbl_title_cfg.pack(anchor="w", padx=12, pady=(8, 4))

        content_cfg = ctk.CTkFrame(self.frame_config, fg_color="transparent")
        content_cfg.pack(fill="x", padx=12, pady=4)

        # SEÇÃO 1: PERFIL & FOTO CIRCULAR
        frame_perfil = ctk.CTkFrame(content_cfg, fg_color="#334155", corner_radius=10)
        frame_perfil.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=4)

        lbl_perfil_t = ctk.CTkLabel(frame_perfil, text="🖼️ Foto de Perfil", font=("Segoe UI", 10, "bold"))
        lbl_perfil_t.pack(anchor="w", padx=10, pady=(4, 2))

        btn_carregar_foto = ctk.CTkButton(
            frame_perfil, text="Escolher Foto de Perfil", height=26, fg_color="#38BDF8", text_color="#0F172A",
            hover_color="#0284C7", font=("Segoe UI", 9, "bold"), command=self.selecionar_foto_perfil
        )
        btn_carregar_foto.pack(fill="x", padx=10, pady=4)

        self.entry_nome_usuario = ctk.CTkEntry(frame_perfil, placeholder_text="Seu Nome ou Apelido", height=24, font=("Segoe UI", 9))
        self.entry_nome_usuario.pack(fill="x", padx=10, pady=4)

        # SEÇÃO 2: CHAVE DE IA (GEMINI)
        frame_contas = ctk.CTkFrame(content_cfg, fg_color="#334155", corner_radius=10)
        frame_contas.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        lbl_contas_t = ctk.CTkLabel(frame_contas, text="🔑 Conexão com IA", font=("Segoe UI", 10, "bold"))
        lbl_contas_t.pack(anchor="w", padx=10, pady=(4, 2))

        self.entry_gemini_key = ctk.CTkEntry(frame_contas, placeholder_text="Chave de API do Gemini", height=24, show="*", font=("Segoe UI", 9))
        self.entry_gemini_key.pack(fill="x", padx=10, pady=4)

        btn_salvar_contas = ctk.CTkButton(
            frame_contas, text="Salvar Configurações", height=26, fg_color="#38BDF8", text_color="#0F172A",
            hover_color="#0284C7", font=("Segoe UI", 9, "bold"), command=self.salvar_contas
        )
        btn_salvar_contas.pack(fill="x", padx=10, pady=4)

        # SEÇÃO 3: TEMA & OPÇÕES VISUAIS
        frame_opcoes = ctk.CTkFrame(content_cfg, fg_color="#334155", corner_radius=10)
        frame_opcoes.pack(side="right", fill="both", expand=True, padx=(4, 0), pady=4)

        lbl_opcoes_t = ctk.CTkLabel(frame_opcoes, text="🎨 Visual e Exibição", font=("Segoe UI", 10, "bold"))
        lbl_opcoes_t.pack(anchor="w", padx=10, pady=(4, 2))

        self.switch_tema = ctk.CTkOptionMenu(
            frame_opcoes, values=["Escuro", "Claro"], height=24, fg_color="#1E293B",
            button_color="#475569", font=("Segoe UI", 9), command=self.alternar_tema
        )
        self.switch_tema.pack(fill="x", padx=10, pady=4)

        self.chk_spotify = ctk.CTkCheckBox(
            frame_opcoes, text="Mostrar Tocador", font=("Segoe UI", 9), command=self.atualizar_visibilidade_modulos
        )
        self.chk_spotify.pack(anchor="w", padx=10, pady=2)
        self.chk_spotify.select()

    def selecionar_foto_perfil(self):
        caminho_imagem = filedialog.askopenfilename(
            title="Selecione uma Imagem para seu Perfil",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if caminho_imagem:
            avatar_img = self.criar_avatar_circular(caminho_imagem, tamanho=(44, 44))
            if avatar_img:
                self.lbl_avatar.configure(image=avatar_img, text="")
                self.imagem_perfil = avatar_img

    def salvar_contas(self):
        gemini_k = self.entry_gemini_key.get().strip()
        nome_user = self.entry_nome_usuario.get().strip()

        if gemini_k:
            os.environ["GEMINI_API_KEY"] = gemini_k
            self.iniciar_gemini()

        if nome_user:
            self.lbl_artista.configure(text=f"Usuário ativo: {nome_user}")

    def alternar_painel_config(self):
        if self.config_visivel:
            self.frame_config.pack_forget()
            self.config_visivel = False
        else:
            self.frame_config.pack(fill="x", padx=12, pady=6, after=self.header_frame)
            self.config_visivel = True

    def atualizar_visibilidade_modulos(self):
        if self.chk_spotify.get() == 1:
            self.frame_spotify.pack(fill="x", padx=12, pady=4, after=self.frame_config)
        else:
            self.frame_spotify.pack_forget()

    # -------------------------------------------------------------------------
    # Alternar / Minimizar Web
    # -------------------------------------------------------------------------
    def alternar_web(self):
        if self.web_visivel:
            self.frame_browser_container.pack_forget()
            self.geometry("840x280")
            self.btn_toggle_web.configure(text="🖥️ Expandir Web")
            self.web_visivel = False
        else:
            self.frame_browser_container.pack(fill="both", expand=True, padx=12, pady=(4, 12))
            self.geometry("840x760")
            self.btn_toggle_web.configure(text="🖥️ Minimizar Web")
            self.web_visivel = True

    # -------------------------------------------------------------------------
    # Lógica de Pesquisa Universal
    # -------------------------------------------------------------------------
    def executar_busca_universal(self):
        query = self.entry_universal.get().strip()
        if not query:
            return

        modo = self.seletor_modo.get()

        if "Web" in modo:
            if not self.web_visivel:
                self.alternar_web()

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
        self.frame_ia_resposta.pack(fill="x", padx=12, pady=4, before=self.frame_browser_container)

        self.txt_resposta_ia.delete("1.0", "end")
        self.txt_resposta_ia.insert("1.0", "🤖 Pensando na melhor resposta para você...")

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
                resposta_texto = f"Não foi possível obter a resposta no momento: {e}"
        else:
            resposta_texto = (
                f"[Modo de Demonstração]\n\nVocê perguntou: '{pergunta}'\n\n"
                "Para ativar respostas da IA em tempo real, insira uma Chave de API no painel de Opções."
            )

        self.txt_resposta_ia.delete("1.0", "end")
        self.txt_resposta_ia.insert("1.0", resposta_texto)

    # -------------------------------------------------------------------------
    # Funções Spotify & Sistema
    # -------------------------------------------------------------------------
    def spotify_play_pause(self):
        self.lbl_musica_titulo.configure(text="Tocando / Pausado")

    def spotify_proxima(self):
        self.lbl_musica_titulo.configure(text="Próxima Música")

    def spotify_anterior(self):
        self.lbl_musica_titulo.configure(text="Música Anterior")

    def iniciar_gemini(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                self.client_gemini = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Erro no Gemini: {e}")

    def alternar_visibilidade(self):
        if self.visivel:
            self.withdraw()
            self.visivel = False
        else:
            self.deiconify()
            self.attributes("-topmost", True)
            self.visivel = True


# -----------------------------------------------------------------------------
# Escuta do Teclado (Alt + Z)
# -----------------------------------------------------------------------------
def escutar_teclado(app):
    teclas_pressionadas = set()

    def on_press(key):
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr) or (
            hasattr(key, "char") and key.char and key.char.lower() == "z"
        ):
            teclas_pressionadas.add(key)

        tem_alt = any(k in teclas_pressionadas for k in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr))
        tem_z = any(hasattr(k, "char") and k.char and k.char.lower() == "z" for k in teclas_pressionadas)

        if tem_alt and tem_z:
            app.alternar_visibilidade()

    def on_release(key):
        teclas_pressionadas.discard(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    app = OmniOverlay()
    thread_teclado = threading.Thread(target=escutar_teclado, args=(app,), daemon=True)
    thread_teclado.start()
    app.mainloop()