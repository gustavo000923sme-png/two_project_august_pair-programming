"""
===============================================================================
PROJETO: OmniOverlay - Premium Theme Engine, Shortcut Manager & Media Player
===============================================================================
"""

import json
import os
import subprocess
import threading
import time
import urllib.parse
import webbrowser
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
from pynput import keyboard

CONFIG_FILE = "app_config.json"

COLOR_TEXT_PRIMARY = ("#0F172A", "#F8FAFC")
COLOR_TEXT_SECONDARY = ("#475569", "#94A3B8")
COLOR_BG_SURFACE = ("#FFFFFF", "#151C28")
COLOR_BG_CARD = ("#E2E8F0", "#1E293B")
COLOR_INPUT_BG = ("#FFFFFF", "#0F172A")
COLOR_BORDER = ("#CBD5E1", "#334155")

COLOR_ACCENTS = {
    "azul": {"primary": "#2563EB", "hover": "#1D4ED8"},
    "vermelho": {"primary": "#DC2626", "hover": "#B91C1C"},
    "verde": {"primary": "#16A34A", "hover": "#15803D"},
    "roxo": {"primary": "#9333EA", "hover": "#7E22CE"},
}


class AccountManager:
    """Gerencia leitura e gravação dos perfis e atalhos."""

    @staticmethod
    def carregar_dados():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    if "perfis" in dados and len(dados["perfis"]) > 0:
                        for p in dados["perfis"]:
                            if "atalhos_custom" not in p:
                                p["atalhos_custom"] = []
                            if "foto_perfil" not in p:
                                p["foto_perfil"] = ""
                        return dados
            except Exception as e:
                print(f"[ERRO] Falha ao ler arquivo de configuração: {e}")

        dados_padrao = {
            "perfis": [
                {
                    "id": "p1",
                    "nome": "Jogador Principal",
                    "cor_acento": "azul",
                    "foto_perfil": "",
                    "atalhos_custom": []
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
            print(f"[ERRO] Falha ao salvar arquivo de configuração: {e}")


class ProfileSelectorFrame(ctk.CTkFrame):
    """Tela de Seleção de Perfis."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=("#F1F5F9", "#0B0F17"), corner_radius=12)
        self.controller = controller
        self.criar_interface()

    def criar_interface(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_BG_SURFACE, height=50, corner_radius=0)
        header.pack(fill="x")

        lbl_titulo = ctk.CTkLabel(
            header,
            text="🎮 Escolha sua Conta",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        lbl_titulo.pack(side="left", padx=16, pady=12)

        btn_fechar = ctk.CTkButton(
            header,
            text="✕",
            width=30,
            height=30,
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            command=self.controller.destroy,
        )
        btn_fechar.pack(side="right", padx=12)

        self.scroll_perfis = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_perfis.pack(fill="both", expand=True, padx=20, pady=15)

        frame_criar = ctk.CTkFrame(self, fg_color=COLOR_BG_SURFACE, corner_radius=12)
        frame_criar.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            frame_criar,
            text="Criar Nova Conta",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.entry_novo_nome = ctk.CTkEntry(
            frame_criar,
            placeholder_text="Nome da conta...",
            height=36,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER
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
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.acao_criar_perfil,
        )
        btn_novo.pack(fill="x", padx=12, pady=(4, 12))

    def atualizar_lista(self):
        for widget in self.scroll_perfis.winfo_children():
            widget.destroy()

        perfis = self.controller.dados_config.get("perfis", [])

        for perfil in perfis:
            card = ctk.CTkFrame(self.scroll_perfis, fg_color=COLOR_BG_CARD, corner_radius=12)
            card.pack(fill="x", pady=6, ipady=4)

            foto_path = perfil.get("foto_perfil", "")
            img_avatar = None
            if foto_path and os.path.exists(foto_path):
                try:
                    pil_img = Image.open(foto_path)
                    img_avatar = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(36, 36))
                except Exception:
                    img_avatar = None

            lbl_avatar = ctk.CTkLabel(
                card,
                text="" if img_avatar else "👤",
                image=img_avatar,
                width=42,
                height=42,
                corner_radius=21,
                fg_color=("#E2E8F0", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                font=("Segoe UI", 16),
            )
            lbl_avatar.pack(side="left", padx=12)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True)

            lbl_nome = ctk.CTkLabel(
                info_frame,
                text=perfil["nome"],
                font=("Segoe UI", 12, "bold"),
                text_color=COLOR_TEXT_PRIMARY,
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
                text_color="#FFFFFF",
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
            "foto_perfil": "",
            "atalhos_custom": []
        }

        self.controller.dados_config["perfis"].append(novo_perfil)
        AccountManager.salvar_dados(self.controller.dados_config)

        self.entry_novo_nome.delete(0, "end")
        self.controller.entrar_no_perfil(novo_perfil)


class DashboardFrame(ctk.CTkFrame):
    """Painel Principal Dashboard Overlay com Player de Vídeo."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=("#F1F5F9", "#0B0F17"), corner_radius=12)
        self.controller = controller

        self._offset_x = 0
        self._offset_y = 0
        self.modo_cinema_ativo = False
        self.dynamic_accent_buttons = []
        self.icone_foto_temp = ""

        self.criar_interface()

    def criar_interface(self):
        # Header
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_SURFACE,
            corner_radius=12,
            border_color=COLOR_BORDER,
            border_width=1,
            height=60,
        )
        self.header_frame.pack(fill="x", padx=16, pady=(16, 8))

        self.header_frame.bind("<Button-1>", self.iniciar_arraste)
        self.header_frame.bind("<B1-Motion>", self.arrastar_janela)

        self.btn_avatar = ctk.CTkButton(
            self.header_frame,
            text="👤",
            width=42,
            height=42,
            corner_radius=21,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="#FFFFFF",
            font=("Segoe UI", 16),
            command=self.trocar_foto_perfil,
        )
        self.btn_avatar.pack(side="left", padx=(12, 10))

        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="OmniOverlay",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_titulo.pack(side="left", padx=2)

        self.btn_tema = ctk.CTkButton(
            self.header_frame,
            text="☀️ Modo Claro" if self.controller.modo_tema_atual == "dark" else "🌙 Modo Escuro",
            width=110,
            height=32,
            corner_radius=8,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=COLOR_TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            command=self.controller.alternar_tema_global,
        )
        self.btn_tema.pack(side="right", padx=(4, 8))

        self.btn_modo_cinema = ctk.CTkButton(
            self.header_frame,
            text="🎬 Cinema",
            width=90,
            height=32,
            corner_radius=8,
            fg_color="#9333EA",
            hover_color="#7E22CE",
            text_color="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            command=self.toggle_modo_cinema,
        )
        self.btn_modo_cinema.pack(side="right", padx=4)

        btn_trocar_conta = ctk.CTkButton(
            self.header_frame,
            text="🔄 Contas",
            width=90,
            height=32,
            corner_radius=8,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=COLOR_TEXT_PRIMARY,
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
            text_color="#FFFFFF",
            command=self.controller.destroy,
        )
        btn_fechar.pack(side="right", padx=4)

        # Barra de Pesquisa / Lançador Universal
        self.frame_busca = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_SURFACE,
            corner_radius=12,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.frame_busca.pack(fill="x", padx=16, pady=4)

        self.entry_universal = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Cole um Link Web ou o caminho de um Programa (.exe) para abrir...",
            height=38,
            corner_radius=8,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            font=("Segoe UI", 11),
        )
        self.entry_universal.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self.entry_universal.bind("<Return>", lambda e: self.executar_busca_universal())

        btn_procurar_arquivo = ctk.CTkButton(
            self.frame_busca,
            text="📁 Buscar App",
            width=100,
            height=38,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.selecionar_executavel_direto,
        )
        btn_procurar_arquivo.pack(side="right", padx=(0, 4), pady=8)

        btn_executar = ctk.CTkButton(
            self.frame_busca,
            text="Abrir 🚀",
            width=90,
            height=38,
            corner_radius=8,
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.executar_busca_universal,
        )
        btn_executar.pack(side="right", padx=8, pady=8)
        self.dynamic_accent_buttons.append(btn_executar)

        # Abas Principais
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            fg_color=COLOR_BG_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.tab_hub = self.tabview.add("🚀 Central de Atalhos")
        self.tab_video = self.tabview.add("🎬 Player de Vídeo")
        self.tab_config = self.tabview.add("⚙️ Configurações")

        self.montar_aba_hub()
        self.montar_aba_player_video()
        self.montar_aba_config()

    def carregar_perfil(self, perfil):
        self.lbl_titulo.configure(text=f"OmniOverlay - {perfil['nome']}")
        self.aplicar_cor_acento(perfil.get("cor_acento", "azul"))
        self.atualizar_foto_avatar(perfil.get("foto_perfil", ""))
        self.atualizar_atalhos_customizados()

    def atualizar_foto_avatar(self, foto_path):
        if foto_path and os.path.exists(foto_path):
            try:
                pil_img = Image.open(foto_path)
                img_avatar = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                self.btn_avatar.configure(image=img_avatar, text="")
                return
            except Exception as e:
                print(f"[ERRO] Falha ao carregar avatar: {e}")

        self.btn_avatar.configure(image="", text="👤")

    def trocar_foto_perfil(self):
        caminho = filedialog.askopenfilename(
            title="Escolha sua Foto de Perfil",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.ico *.bmp")]
        )
        if caminho and self.controller.perfil_ativo:
            self.controller.perfil_ativo["foto_perfil"] = caminho
            AccountManager.salvar_dados(self.controller.dados_config)
            self.atualizar_foto_avatar(caminho)

    def aplicar_cor_acento(self, nome_cor):
        cor = COLOR_ACCENTS.get(nome_cor, COLOR_ACCENTS["azul"])
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
            self.controller.attributes("-alpha", 1.0)
            self.frame_busca.pack_forget()
            self.btn_modo_cinema.configure(text="❌ Sair Cinema", fg_color="#DC2626", hover_color="#B91C1C")
            
            ws = self.controller.winfo_screenwidth()
            hs = self.controller.winfo_screenheight()
            self.controller.geometry(f"{ws}x{hs}+0+0")
        else:
            self.controller.attributes("-alpha", 0.98)
            self.frame_busca.pack(fill="x", padx=16, pady=4, after=self.header_frame)
            self.btn_modo_cinema.configure(text="🎬 Cinema", fg_color="#9333EA", hover_color="#7E22CE")
            self.controller.centralizar_janela(920, 800)

    def montar_aba_hub(self):
        self.scroll_hub = ctk.CTkScrollableFrame(self.tab_hub, fg_color="transparent")
        self.scroll_hub.pack(fill="both", expand=True, padx=8, pady=8)

        frame_adicionar = ctk.CTkFrame(self.scroll_hub, fg_color=COLOR_BG_CARD, corner_radius=10)
        frame_adicionar.pack(fill="x", pady=(0, 16), padx=4, ipady=8)

        ctk.CTkLabel(
            frame_adicionar,
            text="➕ Criar e Personalizar Novo Atalho / App",
            font=("Segoe UI", 12, "bold"),
            text_color=("#0284C7", "#38BDF8")
        ).pack(anchor="w", padx=12, pady=(8, 4))

        form_top = ctk.CTkFrame(frame_adicionar, fg_color="transparent")
        form_top.pack(fill="x", padx=8, pady=2)

        self.entry_nome_atalho = ctk.CTkEntry(
            form_top,
            placeholder_text="Nome do Atalho...",
            height=34,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER
        )
        self.entry_nome_atalho.pack(side="left", fill="x", expand=True, padx=4)

        self.entry_url_atalho = ctk.CTkEntry(
            form_top,
            placeholder_text="Link Web ou Caminho do App (.exe)...",
            height=34,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER
        )
        self.entry_url_atalho.pack(side="left", fill="x", expand=True, padx=4)

        btn_browse_app = ctk.CTkButton(
            form_top,
            text="💻 Localizar App",
            width=110,
            height=34,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.procurar_app_para_atalho,
        )
        btn_browse_app.pack(side="left", padx=4)

        form_bot = ctk.CTkFrame(frame_adicionar, fg_color="transparent")
        form_bot.pack(fill="x", padx=8, pady=(4, 4))

        ctk.CTkLabel(form_bot, text="Ícone do Lado:", font=("Segoe UI", 10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=4)

        self.combo_icone = ctk.CTkComboBox(
            form_bot,
            values=["🎮", "💻", "🚀", "🌐", "🎵", "⚡", "📂", "🛠️"],
            width=80,
            height=32,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_text_color=COLOR_TEXT_PRIMARY
        )
        self.combo_icone.pack(side="left", padx=4)
        self.combo_icone.set("🎮")

        self.btn_foto_atalho = ctk.CTkButton(
            form_bot,
            text="🖼️ Foto Custom",
            width=110,
            height=32,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.escolher_foto_icone_atalho,
        )
        self.btn_foto_atalho.pack(side="left", padx=4)

        btn_add_atalho = ctk.CTkButton(
            form_bot,
            text="+ Criar Atalho",
            width=120,
            height=32,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.adicionar_atalho_customizado,
        )
        btn_add_atalho.pack(side="right", padx=4)

        ctk.CTkLabel(
            self.scroll_hub, text="⭐ Seus Atalhos Personalizados", font=("Segoe UI", 13, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", pady=(4, 8))

        self.grid_custom = ctk.CTkFrame(self.scroll_hub, fg_color="transparent")
        self.grid_custom.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            self.scroll_hub, text="🎵 Mídia & Streaming (Padrão)", font=("Segoe UI", 13, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", pady=(4, 8))

        grid_media = ctk.CTkFrame(self.scroll_hub, fg_color="transparent")
        grid_media.pack(fill="x", pady=(0, 16))

        atalhos_padrao = [
            ("🟢 Spotify", "https://open.spotify.com", "#1DB954"),
            ("▶️ YouTube", "https://www.youtube.com", "#FF0000"),
            ("🔴 Netflix", "https://www.netflix.com", "#E50914"),
            ("💜 Twitch", "https://www.twitch.tv", "#9146FF"),
            ("📦 Prime Video", "https://www.primevideo.com", "#00A8E1"),
            ("💬 WhatsApp Web", "https://web.whatsapp.com", "#25D366"),
        ]
        self.criar_cards_grid(grid_media, atalhos_padrao)

    def procurar_app_para_atalho(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o Executável ou Atalho do Programa",
            filetypes=[("Executáveis e Atalhos", "*.exe *.lnk *.bat *.cmd"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.entry_url_atalho.delete(0, "end")
            self.entry_url_atalho.insert(0, caminho)
            if not self.entry_nome_atalho.get():
                nome_sugerido = os.path.splitext(os.path.basename(caminho))[0].capitalize()
                self.entry_nome_atalho.insert(0, nome_sugerido)

    def escolher_foto_icone_atalho(self):
        caminho = filedialog.askopenfilename(
            title="Escolha uma imagem para o ícone do atalho",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.ico *.bmp")]
        )
        if caminho:
            self.icone_foto_temp = caminho
            self.btn_foto_atalho.configure(text="✅ Foto OK")

    def adicionar_atalho_customizado(self):
        nome = self.entry_nome_atalho.get().strip()
        alvo = self.entry_url_atalho.get().strip()
        icone = self.combo_icone.get()

        if not nome or not alvo:
            return

        perfil = self.controller.perfil_ativo
        if perfil:
            novo_item = {
                "nome": nome,
                "alvo": alvo,
                "icone": icone,
                "foto_icone": self.icone_foto_temp
            }
            perfil["atalhos_custom"].append(novo_item)
            AccountManager.salvar_dados(self.controller.dados_config)

            self.entry_nome_atalho.delete(0, "end")
            self.entry_url_atalho.delete(0, "end")
            self.icone_foto_temp = ""
            self.btn_foto_atalho.configure(text="🖼️ Foto Custom")
            self.atualizar_atalhos_customizados()

    def remover_atalho_customizado(self, index):
        perfil = self.controller.perfil_ativo
        if perfil and 0 <= index < len(perfil["atalhos_custom"]):
            perfil["atalhos_custom"].pop(index)
            AccountManager.salvar_dados(self.controller.dados_config)
            self.atualizar_atalhos_customizados()

    def mover_atalho_posicao(self, index, direcao):
        perfil = self.controller.perfil_ativo
        if not perfil:
            return
        
        lista = perfil.get("atalhos_custom", [])
        novo_index = index + direcao

        if 0 <= novo_index < len(lista):
            lista[index], lista[novo_index] = lista[novo_index], lista[index]
            AccountManager.salvar_dados(self.controller.dados_config)
            self.atualizar_atalhos_customizados()

    def atualizar_atalhos_customizados(self):
        for widget in self.grid_custom.winfo_children():
            widget.destroy()

        perfil = self.controller.perfil_ativo
        if not perfil:
            return

        lista = perfil.get("atalhos_custom", [])

        if not lista:
            lbl_vazio = ctk.CTkLabel(
                self.grid_custom,
                text="Nenhum atalho criado ainda. Adicione um no painel acima!",
                text_color=COLOR_TEXT_SECONDARY
            )
            lbl_vazio.pack(anchor="w", padx=4, pady=4)
            return

        for idx, item in enumerate(lista):
            card_frame = ctk.CTkFrame(
                self.grid_custom,
                fg_color=COLOR_BG_CARD,
                border_color=COLOR_BORDER,
                border_width=1,
                corner_radius=8
            )
            card_frame.pack(fill="x", pady=4, padx=4)

            foto_icon = item.get("foto_icone", "")
            img_obj = None
            if foto_icon and os.path.exists(foto_icon):
                try:
                    pil_img = Image.open(foto_icon)
                    img_obj = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(20, 20))
                except Exception:
                    img_obj = None

            prefixo_icone = item.get("icone", "🎮")
            texto_exibicao = f"{prefixo_icone} {item['nome']}" if not img_obj else f" {item['nome']}"

            btn_exec = ctk.CTkButton(
                card_frame,
                text=texto_exibicao,
                image=img_obj,
                compound="left",
                height=42,
                fg_color="transparent",
                hover_color=("#CBD5E1", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                command=lambda a=item['alvo']: self.abrir_inteligente(a),
            )
            btn_exec.pack(side="left", fill="both", expand=True, padx=(8, 0))

            btn_up = ctk.CTkButton(
                card_frame,
                text="⬆️",
                width=28,
                height=28,
                fg_color=("#CBD5E1", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                command=lambda i=idx: self.mover_atalho_posicao(i, -1)
            )
            btn_up.pack(side="right", padx=2)

            btn_down = ctk.CTkButton(
                card_frame,
                text="⬇️",
                width=28,
                height=28,
                fg_color=("#CBD5E1", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                command=lambda i=idx: self.mover_atalho_posicao(i, 1)
            )
            btn_down.pack(side="right", padx=2)

            btn_del = ctk.CTkButton(
                card_frame,
                text="🗑️",
                width=32,
                height=28,
                fg_color="#EF4444",
                hover_color="#DC2626",
                text_color="#FFFFFF",
                command=lambda i=idx: self.remover_atalho_customizado(i),
            )
            btn_del.pack(side="right", padx=6)

    def selecionar_executavel_direto(self):
        caminho = filedialog.askopenfilename(
            title="Escolha um Executável ou Arquivo",
            filetypes=[("Executáveis", "*.exe *.lnk *.bat"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.entry_universal.delete(0, "end")
            self.entry_universal.insert(0, caminho)

    def abrir_inteligente(self, alvo):
        alvo_limpo = alvo.strip()

        if os.path.exists(alvo_limpo):
            try:
                os.startfile(alvo_limpo)
                return
            except Exception:
                try:
                    subprocess.Popen([alvo_limpo], shell=True)
                    return
                except Exception as e:
                    print(f"[ERRO] Erro ao abrir executável: {e}")

        if alvo_limpo.startswith("http://") or alvo_limpo.startswith("https://"):
            webbrowser.open(alvo_limpo)
        elif "." in alvo_limpo and " " not in alvo_limpo:
            webbrowser.open(f"https://{alvo_limpo}")
        else:
            try:
                os.startfile(alvo_limpo)
            except Exception:
                query_encoded = urllib.parse.quote_plus(alvo_limpo)
                webbrowser.open(f"https://www.google.com/search?q={query_encoded}")

    def criar_cards_grid(self, frame_pai, lista_atalhos):
        col, row = 0, 0
        for nome, url, cor in lista_atalhos:
            btn = ctk.CTkButton(
                frame_pai,
                text=nome,
                height=52,
                corner_radius=10,
                fg_color=COLOR_BG_CARD,
                hover_color=cor,
                text_color=COLOR_TEXT_PRIMARY,
                font=("Segoe UI", 12, "bold"),
                command=lambda u=url: self.abrir_inteligente(u),
            )
            btn.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            col += 1
            if col > 2:
                col = 0
                row += 1

        for i in range(3):
            frame_pai.grid_columnconfigure(i, weight=1)

    def montar_aba_player_video(self):
        """Nova aba com Reprodutor de Mídia / Player de Vídeos."""
        frame_top_video = ctk.CTkFrame(self.tab_video, fg_color="transparent")
        frame_top_video.pack(fill="x", padx=12, pady=10)

        self.entry_video_url = ctk.CTkEntry(
            frame_top_video,
            placeholder_text="Cole o Link do Vídeo (YouTube, Twitch, MP4) ou selecione um arquivo...",
            height=38,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            font=("Segoe UI", 11),
        )
        self.entry_video_url.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_arquivo_local = ctk.CTkButton(
            frame_top_video,
            text="📁 Abrir Vídeo",
            width=110,
            height=38,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.selecionar_video_local,
        )
        btn_arquivo_local.pack(side="right", padx=(0, 6))

        btn_play = ctk.CTkButton(
            frame_top_video,
            text="▶️ Assistir Vídeo",
            width=130,
            height=38,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.reproduzir_video,
        )
        btn_play.pack(side="right")

        # Tela principal de exibição do Player
        self.frame_screen = ctk.CTkFrame(
            self.tab_video,
            fg_color=("#1E293B", "#0F172A"),
            corner_radius=12,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.frame_screen.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.lbl_video_display = ctk.CTkLabel(
            self.frame_screen,
            text="📺 Player de Vídeo do Overlay\n\nCole o link de um vídeo do YouTube ou escolha um arquivo de vídeo do computador para reproduzir.",
            font=("Segoe UI", 13),
            text_color=("#94A3B8", "#64748B"),
        )
        self.lbl_video_display.pack(fill="both", expand=True, padx=20, pady=20)

    def selecionar_video_local(self):
        caminho = filedialog.askopenfilename(
            title="Escolha um arquivo de Vídeo",
            filetypes=[("Vídeos", "*.mp4 *.mkv *.avi *.mov *.webm"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.entry_video_url.delete(0, "end")
            self.entry_video_url.insert(0, caminho)

    def reproduzir_video(self):
        url = self.entry_video_url.get().strip()
        if not url:
            return

        if os.path.exists(url):
            try:
                os.startfile(url)
                self.lbl_video_display.configure(text=f"▶️ Reproduzindo arquivo local:\n{os.path.basename(url)}")
            except Exception as e:
                self.lbl_video_display.configure(text=f"Erro ao abrir vídeo local: {e}")
        else:
            webbrowser.open(url)
            self.lbl_video_display.configure(text=f"🌐 Abrindo vídeo no navegador:\n{url}")

    def montar_aba_config(self):
        container = ctk.CTkScrollableFrame(self.tab_config, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            container,
            text="Foto de Perfil & Conta",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))

        btn_alterar_foto = ctk.CTkButton(
            container,
            text="🖼️ Alterar Foto de Perfil",
            height=36,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            hover_color=("#94A3B8", "#475569"),
            command=self.trocar_foto_perfil,
        )
        btn_alterar_foto.pack(anchor="w", pady=4)

        ctk.CTkLabel(
            container,
            text="Personalização de Cores Destaque",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(16, 4))

        frame_cores = ctk.CTkFrame(container, fg_color="transparent")
        frame_cores.pack(fill="x", pady=4)

        for nome, dados in COLOR_ACCENTS.items():
            btn_c = ctk.CTkButton(
                frame_cores,
                text=nome.capitalize(),
                fg_color=dados["primary"],
                hover_color=dados["hover"],
                text_color="#FFFFFF",
                width=80,
                height=32,
                command=lambda c=nome: self.aplicar_cor_acento(c),
            )
            btn_c.pack(side="left", padx=4)

    def executar_busca_universal(self):
        query = self.entry_universal.get().strip()
        if not query:
            return

        self.abrir_inteligente(query)


class OmniOverlay(ctk.CTk):
    """Aplicação Principal."""

    def __init__(self):
        super().__init__()

        self.title("OmniOverlay")
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.attributes("-alpha", 0.98)

        self.dados_config = AccountManager.carregar_dados()
        self.perfil_ativo = None
        self.visivel = True

        self.modo_tema_atual = self.dados_config.get("modo_tema", "dark")
        ctk.set_appearance_mode(self.modo_tema_atual)

        self.frame_seletor = ProfileSelectorFrame(self, self)
        self.frame_dashboard = DashboardFrame(self, self)

        self.abrir_seletor_perfis()

    def alternar_tema_global(self):
        if self.modo_tema_atual == "dark":
            self.modo_tema_atual = "light"
        else:
            self.modo_tema_atual = "dark"

        ctk.set_appearance_mode(self.modo_tema_atual)

        self.dados_config["modo_tema"] = self.modo_tema_atual
        AccountManager.salvar_dados(self.dados_config)

        perfil_temp = self.perfil_ativo
        self.frame_dashboard.destroy()
        self.frame_dashboard = DashboardFrame(self, self)

        if perfil_temp:
            self.frame_dashboard.pack(fill="both", expand=True)
            self.frame_dashboard.carregar_perfil(perfil_temp)
        else:
            self.frame_seletor.destroy()
            self.frame_seletor = ProfileSelectorFrame(self, self)
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

        self.frame_seletor.pack_forget()
        self.centralizar_janela(920, 800)
        self.frame_dashboard.pack(fill="both", expand=True)
        self.frame_dashboard.carregar_perfil(perfil)

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