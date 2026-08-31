"""
===============================================================================
PROJETO: OmniOverlay - Central Flutuante Multitarefas In-Game
===============================================================================
"""

import os
import threading

import customtkinter as ctk
from PIL import Image, ImageTk

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
from pynput import keyboard

# Configurações do customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class OmniOverlay(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Configurações básicas da janela flutuante
        self.title("OmniOverlay")
        self.geometry("680x540")

        # Configurações de estilo overlay in-game
        self.attributes("-topmost", True)  # Mantém por cima
        self.overrideredirect(True)  # Remove as bordas padrão do sistema
        self.attributes("-alpha", 0.94)  # Transparência elegante

        # Variáveis para controlar o movimento da janela pelo mouse
        self._offset_x = 0
        self._offset_y = 0

        self.visivel = True

        # Variáveis das APIs
        self.spotify_cliente = None
        self.client_gemini = None

        # Monta a interface gráfica
        self.criar_interface()

        # Tenta conectar a IA
        self.iniciar_gemini()

    # -------------------------------------------------------------------------
    # Lógica para Arrastar a Janela sem Bordas
    # -------------------------------------------------------------------------
    def iniciar_arraste(self, event):
        """Capta a posição inicial do clique do mouse."""
        self._offset_x = event.x
        self._offset_y = event.y

    def arrastar_janela(self, event):
        """Atualiza a posição da janela conforme o mouse se move."""
        x = self.winfo_x() + (event.x - self._offset_x)
        y = self.winfo_y() + (event.y - self._offset_y)
        self.geometry(f"+{x}+{y}")

    # -------------------------------------------------------------------------
    # Construção da Interface Visual
    # -------------------------------------------------------------------------
    def criar_interface(self):
        # --- Barra de Título Customizada (Permite arrastar a janela) ---
        self.header_frame = ctk.CTkFrame(
            self, fg_color="#1E1E24", corner_radius=10, height=40
        )
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Vincula os eventos do mouse à barra de topo
        self.header_frame.bind("<Button-1>", self.iniciar_arraste)
        self.header_frame.bind("<B1-Motion>", self.arrastar_janela)

        lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="⚡ OMNIOVERLAY",
            font=("Segoe UI", 14, "bold"),
            text_color="#00E5FF",
        )
        lbl_titulo.pack(side="left", padx=15, pady=8)
        lbl_titulo.bind("<Button-1>", self.iniciar_arraste)
        lbl_titulo.bind("<B1-Motion>", self.arrastar_janela)

        lbl_dica = ctk.CTkLabel(
            self.header_frame,
            text="[ Clique e arraste aqui | Alt + Z para ocultar ]",
            font=("Segoe UI", 10),
            text_color="#888888",
        )
        lbl_dica.pack(side="left", padx=10)
        lbl_dica.bind("<Button-1>", self.iniciar_arraste)
        lbl_dica.bind("<B1-Motion>", self.arrastar_janela)

        # Botão Fechar compacto no cabeçalho
        btn_fechar_topo = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=28,
            height=24,
            corner_radius=6,
            fg_color="#FF5252",
            hover_color="#FF1744",
            font=("Arial", 12, "bold"),
            command=self.destroy,
        )
        btn_fechar_topo.pack(side="right", padx=8, pady=6)

        # --- Seção 1: Player do Spotify ---
        frame_spotify = ctk.CTkFrame(self, corner_radius=12, fg_color="#18181C")
        frame_spotify.pack(fill="x", padx=15, pady=8)

        lbl_sec_spotify = ctk.CTkLabel(
            frame_spotify,
            text="🎵 SPOTIFY PLAYER",
            font=("Segoe UI", 12, "bold"),
            text_color="#1DB954",
        )
        lbl_sec_spotify.pack(anchor="w", padx=15, pady=(10, 2))

        self.lbl_musica = ctk.CTkLabel(
            frame_spotify,
            text="Nenhuma música tocando no momento...",
            font=("Segoe UI", 13),
            text_color="#E0E0E0",
        )
        self.lbl_musica.pack(pady=5)

        # Controles de Mídia
        frame_botoes = ctk.CTkFrame(frame_spotify, fg_color="transparent")
        frame_botoes.pack(pady=(5, 12))

        btn_anterior = ctk.CTkButton(
            frame_botoes,
            text="⏮ Anterior",
            width=100,
            height=32,
            corner_radius=8,
            fg_color="#2A2A32",
            hover_color="#3A3A46",
            command=self.spotify_anterior,
        )
        btn_anterior.pack(side="left", padx=6)

        btn_play = ctk.CTkButton(
            frame_botoes,
            text="⏯ Play / Pause",
            width=110,
            height=32,
            corner_radius=8,
            fg_color="#1DB954",
            hover_color="#1AA34A",
            font=("Segoe UI", 12, "bold"),
            command=self.spotify_play_pause,
        )
        btn_play.pack(side="left", padx=6)

        btn_proxima = ctk.CTkButton(
            frame_botoes,
            text="⏭ Próxima",
            width=100,
            height=32,
            corner_radius=8,
            fg_color="#2A2A32",
            hover_color="#3A3A46",
            command=self.spotify_proxima,
        )
        btn_proxima.pack(side="left", padx=6)

        # --- Seção 2: Assistente de IA (Gemini) ---
        frame_ia = ctk.CTkFrame(self, corner_radius=12, fg_color="#18181C")
        frame_ia.pack(fill="both", expand=True, padx=15, pady=8)

        lbl_sec_ia = ctk.CTkLabel(
            frame_ia,
            text="🤖 ASSISTENTE DE IA & PESQUISA",
            font=("Segoe UI", 12, "bold"),
            text_color="#00E5FF",
        )
        lbl_sec_ia.pack(anchor="w", padx=15, pady=(10, 2))

        # Campo de entrada e botão lado a lado
        frame_busca = ctk.CTkFrame(frame_ia, fg_color="transparent")
        frame_busca.pack(fill="x", padx=15, pady=5)

        self.entry_pesquisa = ctk.CTkEntry(
            frame_busca,
            placeholder_text="Digite sua pergunta ou dica de jogo...",
            height=35,
            corner_radius=8,
            border_color="#2A2A32",
        )
        self.entry_pesquisa.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_perguntar = ctk.CTkButton(
            frame_busca,
            text="Consultar",
            width=100,
            height=35,
            corner_radius=8,
            fg_color="#00E5FF",
            hover_color="#00B0FF",
            text_color="#000000",
            font=("Segoe UI", 12, "bold"),
            command=self.consultar_ia,
        )
        btn_perguntar.pack(side="right")

        # Caixa de resposta
        self.txt_resposta = ctk.CTkTextbox(
            frame_ia,
            height=120,
            corner_radius=8,
            fg_color="#101014",
            border_color="#2A2A32",
            border_width=1,
            font=("Segoe UI", 12),
        )
        self.txt_resposta.pack(fill="both", expand=True, padx=15, pady=(5, 12))
        self.txt_resposta.insert(
            "1.0", "As respostas da IA vão aparecer aqui..."
        )

    # -------------------------------------------------------------------------
    # Métodos de Funcionamento
    # -------------------------------------------------------------------------
    def alternar_visibilidade(self):
        if self.visivel:
            self.withdraw()
            self.visivel = False
        else:
            self.deiconify()
            self.attributes("-topmost", True)
            self.visivel = True

    def iniciar_gemini(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                self.client_gemini = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Erro ao conectar com a IA: {e}")

    def consultar_ia(self):
        pergunta = self.entry_pesquisa.get()
        if not pergunta:
            return

        self.txt_resposta.delete("1.0", "end")
        self.txt_resposta.insert("1.0", "Pensando...")

        threading.Thread(
            target=self._processar_pergunta_ia, args=(pergunta,), daemon=True
        ).start()

    def _processar_pergunta_ia(self, pergunta):
        if self.client_gemini:
            try:
                response = self.client_gemini.models.generate_content(
                    model="gemini-2.5-flash", contents=pergunta
                )
                resposta_texto = response.text
            except Exception as e:
                resposta_texto = f"Erro na consulta à IA: {e}"
        else:
            resposta_texto = (
                f"[Modo Demonstração] Pergunta: '{pergunta}'\n\n"
                "Para ativar respostas reais da IA, configure a variável GEMINI_API_KEY no sistema."
            )

        self.txt_resposta.delete("1.0", "end")
        self.txt_resposta.insert("1.0", resposta_texto)

    def spotify_play_pause(self):
        self.lbl_musica.configure(
            text="🎵 Comando Play/Pause enviado ao Spotify"
        )

    def spotify_proxima(self):
        self.lbl_musica.configure(text="⏭ Avançando para a próxima música...")

    def spotify_anterior(self):
        self.lbl_musica.configure(text="⏮ Voltando para a música anterior...")


# -----------------------------------------------------------------------------
# Escuta do Teclado (Alt + Z)
# -----------------------------------------------------------------------------
def escutar_teclado(app):
    teclas_pressionadas = set()

    def on_press(key):
        if (
            key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr)
            or (hasattr(key, "char") and key.char and key.char.lower() == "z")
        ):
            teclas_pressionadas.add(key)

        tem_alt = any(
            k in teclas_pressionadas
            for k in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr)
        )
        tem_z = any(
            hasattr(k, "char") and k.char and k.char.lower() == "z"
            for k in teclas_pressionadas
        )

        if tem_alt and tem_z:
            app.alternar_visibilidade()

    def on_release(key):
        teclas_pressionadas.discard(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# -----------------------------------------------------------------------------
# Execução do Programa
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = OmniOverlay()

    thread_teclado = threading.Thread(
        target=escutar_teclado, args=(app,), daemon=True
    )
    thread_teclado.start()

    app.mainloop()