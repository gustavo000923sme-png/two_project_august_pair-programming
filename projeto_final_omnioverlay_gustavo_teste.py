"""
===============================================================================
PROJETO: OmniOverlay - Premium Theme Engine, AI Assistant, Hub & CPU Monitor
===============================================================================
"""

import json
import os
import subprocess
import time
import urllib.parse
import webbrowser
import threading
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from tkVideoPlayer import TkinterVideo

# Bibliotecas adicionais para monitoramento e atalhos de teclado
import psutil
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
        super().__init__(parent, fg_color=COLOR_BG_SURFACE, corner_radius=12)
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

        frame_criar = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
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
                fg_color=("#CBD5E1", "#334155"),
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
    """Painel Principal Dashboard Overlay com Player, IA e Monitor de Recursos."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG_SURFACE, corner_radius=12)
        self.controller = controller

        self._offset_x = 0
        self._offset_y = 0
        self.modo_cinema_ativo = False
        self.dynamic_accent_buttons = []
        self.icone_foto_temp = ""

        self.criar_interface()
        self.atualizar_monitor_sistema()

    def criar_interface(self):
        # Header Organizado
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

        # Lado Esquerdo - Perfil & Título
        self.btn_avatar = ctk.CTkButton(
            self.header_frame,
            text="👤",
            width=40,
            height=40,
            corner_radius=20,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="#FFFFFF",
            font=("Segoe UI", 15),
            command=self.trocar_foto_perfil,
        )
        self.btn_avatar.pack(side="left", padx=(12, 8))

        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="OmniOverlay",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.lbl_titulo.pack(side="left", padx=2)

        # Centro - Monitor de CPU e RAM Compacto
        self.frame_hardware = ctk.CTkFrame(
            self.header_frame,
            fg_color=COLOR_BG_CARD,
            corner_radius=8,
            height=36
        )
        self.frame_hardware.pack(side="left", padx=16, pady=10)

        self.lbl_cpu = ctk.CTkLabel(
            self.frame_hardware,
            text="⚡ CPU: 0%",
            font=("Segoe UI", 10, "bold"),
            text_color=("#1D4ED8", "#60A5FA")
        )
        self.lbl_cpu.pack(side="left", padx=8)

        self.lbl_ram = ctk.CTkLabel(
            self.frame_hardware,
            text="💾 RAM: 0%",
            font=("Segoe UI", 10, "bold"),
            text_color=("#15803D", "#4ADE80")
        )
        self.lbl_ram.pack(side="left", padx=(0, 8))

        # Lado Direito - Controles e Ações
        btn_fechar = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=32,
            height=32,
            corner_radius=8,
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            command=self.controller.destroy,
        )
        btn_fechar.pack(side="right", padx=(4, 12))

        self.btn_tema = ctk.CTkButton(
            self.header_frame,
            text="☀️" if self.controller.modo_tema_atual == "dark" else "🌙",
            width=32,
            height=32,
            corner_radius=8,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=COLOR_TEXT_PRIMARY,
            font=("Segoe UI", 12),
            command=self.controller.alternar_tema_global,
        )
        self.btn_tema.pack(side="right", padx=4)

        self.btn_modo_cinema = ctk.CTkButton(
            self.header_frame,
            text="🎬 Cinema",
            width=85,
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
            width=85,
            height=32,
            corner_radius=8,
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            text_color=COLOR_TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            command=self.controller.abrir_seletor_perfis,
        )
        btn_trocar_conta.pack(side="right", padx=4)

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
        self.tab_ia = self.tabview.add("🤖 Assistente IA")
        self.tab_video = self.tabview.add("🎬 Player de Vídeo")
        self.tab_config = self.tabview.add("⚙️ Configurações")

        self.montar_aba_hub()
        self.montar_aba_ia()
        self.montar_aba_player_video()
        self.montar_aba_config()

    def atualizar_monitor_sistema(self):
        """Atualiza o uso de CPU, RAM e Hardware em tempo real."""
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()

            self.lbl_cpu.configure(text=f"⚡ CPU: {cpu_usage:.0f}%")
            self.lbl_ram.configure(text=f"💾 RAM: {ram.percent:.0f}%")

            if hasattr(self, 'bar_cpu_detalhada'):
                self.bar_cpu_detalhada.set(cpu_usage / 100.0)
                self.lbl_cpu_valor_detalhado.configure(text=f"{cpu_usage:.1f}%")

                self.bar_ram_detalhada.set(ram.percent / 100.0)
                ram_usada_gb = ram.used / (1024**3)
                ram_total_gb = ram.total / (1024**3)
                self.lbl_ram_valor_detalhado.configure(
                    text=f"{ram.percent:.1f}% ({ram_usada_gb:.1f} GB / {ram_total_gb:.1f} GB)"
                )

                cor_cpu = "#16A34A" if cpu_usage < 60 else ("#EAB308" if cpu_usage < 85 else "#EF4444")
                self.bar_cpu_detalhada.configure(progress_color=cor_cpu)

                cor_ram = "#16A34A" if ram.percent < 70 else ("#EAB308" if ram.percent < 88 else "#EF4444")
                self.bar_ram_detalhada.configure(progress_color=cor_ram)

        except Exception as e:
            print(f"[MONITOR] Erro ao obter dados do sistema: {e}")

        self.after(1500, self.atualizar_monitor_sistema)

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

    # =========================================================================
    # ABA 1: HUB DE ATALHOS (CORRIGIDO PARA O MODO CLARO)
    # =========================================================================
    def montar_aba_hub(self):
        frame_adicionar = ctk.CTkFrame(self.tab_hub, fg_color=COLOR_BG_CARD, corner_radius=10)
        frame_adicionar.pack(fill="x", pady=(8, 8), padx=8, ipady=4)

        ctk.CTkLabel(
            frame_adicionar,
            text="➕ Adicionar Novo Atalho ao Seu Perfil",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0284C7", "#38BDF8")
        ).pack(anchor="w", padx=12, pady=(6, 2))

        form_top = ctk.CTkFrame(frame_adicionar, fg_color="transparent")
        form_top.pack(fill="x", padx=8, pady=2)

        self.entry_nome_atalho = ctk.CTkEntry(
            form_top,
            placeholder_text="Nome do Atalho...",
            height=32,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER
        )
        self.entry_nome_atalho.pack(side="left", fill="x", expand=True, padx=4)

        self.entry_url_atalho = ctk.CTkEntry(
            form_top,
            placeholder_text="Link Web ou Caminho (.exe)...",
            height=32,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER
        )
        self.entry_url_atalho.pack(side="left", fill="x", expand=True, padx=4)

        btn_browse_app = ctk.CTkButton(
            form_top,
            text="💻 Buscar App",
            width=100,
            height=32,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.procurar_app_para_atalho,
        )
        btn_browse_app.pack(side="left", padx=4)

        form_bot = ctk.CTkFrame(frame_adicionar, fg_color="transparent")
        form_bot.pack(fill="x", padx=8, pady=(4, 6))

        ctk.CTkLabel(form_bot, text="Ícone:", font=("Segoe UI", 10, "bold"), text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=4)

        self.combo_icone = ctk.CTkComboBox(
            form_bot,
            values=["🎮", "💻", "🚀", "🌐", "🎵", "⚡", "📂", "🛠️"],
            width=70,
            height=30,
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
            height=30,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.escolher_foto_icone_atalho,
        )
        self.btn_foto_atalho.pack(side="left", padx=4)

        btn_add_atalho = ctk.CTkButton(
            form_bot,
            text="+ Salvar Atalho",
            width=120,
            height=30,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.adicionar_atalho_customizado,
        )
        btn_add_atalho.pack(side="right", padx=4)

        self.tabview_hub = ctk.CTkTabview(
            self.tab_hub,
            corner_radius=10,
            fg_color="transparent",
            text_color=COLOR_TEXT_PRIMARY
        )
        self.tabview_hub.pack(fill="both", expand=True, padx=4, pady=0)

        self.cat_custom = self.tabview_hub.add("⭐ Meus Atalhos")
        self.cat_media = self.tabview_hub.add("🎵 Mídia & Streaming")
        self.cat_games = self.tabview_hub.add("🎮 Jogos & Plataformas")
        self.cat_tools = self.tabview_hub.add("⚙️ Sistema & Ferramentas")

        self.scroll_custom = ctk.CTkScrollableFrame(self.cat_custom, fg_color="transparent")
        self.scroll_custom.pack(fill="both", expand=True)

        self.grid_custom = ctk.CTkFrame(self.scroll_custom, fg_color="transparent")
        self.grid_custom.pack(fill="x", pady=4)

        self.montar_categoria_estatica(self.cat_media, [
            ("🟢 Spotify", "https://open.spotify.com", "#1DB954"),
            ("▶️ YouTube", "https://www.youtube.com", "#FF0000"),
            ("🔴 Netflix", "https://www.netflix.com", "#E50914"),
            ("💜 Twitch", "https://www.twitch.tv", "#9146FF"),
            ("📦 Prime Video", "https://www.primevideo.com", "#00A8E1"),
            ("💬 WhatsApp Web", "https://web.whatsapp.com", "#25D366"),
            ("🎵 Soundcloud", "https://soundcloud.com", "#FF5500"),
            ("📺 Disney+", "https://www.disneyplus.com", "#113CCF"),
        ])

        self.montar_categoria_estatica(self.cat_games, [
            ("🚀 Steam", "steam://open/main", "#171A21"),
            ("🛡️ Epic Games", "epicgames://", "#2A2A2A"),
            ("💬 Discord", "https://discord.com/app", "#5865F2"),
            ("🎮 Roblox", "https://www.roblox.com", "#000000"),
            ("🔴 Roblox App", "roblox://", "#E22B26"),
            ("🌐 Poki Jogos", "https://poki.com", "#0099FF"),
        ])

        self.montar_categoria_estatica(self.cat_tools, [
            ("📁 Gerenciador de Arquivos", "explorer.exe", "#0078D4"),
            ("⚙️ Configurações do Windows", "ms-settings:", "#0078D4"),
            ("📝 Bloco de Notas", "notepad.exe", "#475569"),
            ("🌐 Google Chrome", "https://www.google.com", "#4285F4"),
            ("💻 Prompt de Comando", "cmd.exe", "#1E293B"),
            ("⚡ Gerenciador de Tarefas", "taskmgr.exe", "#16A34A"),
        ])

    def montar_categoria_estatica(self, container, lista_atalhos):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self.criar_cards_grid(scroll, lista_atalhos)

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
                text="Nenhum atalho personalizado criado ainda. Adicione no campo acima!",
                text_color=COLOR_TEXT_SECONDARY,
                font=("Segoe UI", 11)
            )
            lbl_vazio.pack(anchor="w", padx=8, pady=12)
            return

        for idx, item in enumerate(lista):
            card_frame = ctk.CTkFrame(
                self.grid_custom,
                fg_color=COLOR_BG_CARD,
                border_color=COLOR_BORDER,
                border_width=1,
                corner_radius=8
            )
            card_frame.pack(fill="x", pady=3, padx=4)

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
                height=38,
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
                width=26,
                height=26,
                fg_color=("#CBD5E1", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                command=lambda i=idx: self.mover_atalho_posicao(i, -1)
            )
            btn_up.pack(side="right", padx=2)

            btn_down = ctk.CTkButton(
                card_frame,
                text="⬇️",
                width=26,
                height=26,
                fg_color=("#CBD5E1", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                command=lambda i=idx: self.mover_atalho_posicao(i, 1)
            )
            btn_down.pack(side="right", padx=2)

            btn_del = ctk.CTkButton(
                card_frame,
                text="🗑️",
                width=30,
                height=26,
                fg_color="#EF4444",
                hover_color="#DC2626",
                text_color="#FFFFFF",
                command=lambda i=idx: self.remover_atalho_customizado(i),
            )
            btn_del.pack(side="right", padx=6)

    # =========================================================================
    # ABA 2: INTEGRAÇÃO DA INTELIGÊNCIA ARTIFICIAL (CHAT)
    # =========================================================================
    def montar_aba_ia(self):
        container_ia = ctk.CTkFrame(self.tab_ia, fg_color="transparent")
        container_ia.pack(fill="both", expand=True, padx=8, pady=8)

        header_ia = ctk.CTkFrame(container_ia, fg_color=COLOR_BG_CARD, corner_radius=8)
        header_ia.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            header_ia,
            text="🤖 OmniAI - Assistente Virtual Integrado",
            font=("Segoe UI", 12, "bold"),
            text_color=("#1D4ED8", "#60A5FA")
        ).pack(side="left", padx=12, pady=8)

        self.chat_history = ctk.CTkTextbox(
            container_ia,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=8,
            wrap="word",
            font=("Segoe UI", 11)
        )
        self.chat_history.pack(fill="both", expand=True, pady=(0, 8))
        self.chat_history.configure(state="disabled")

        self.adicionar_mensagem_chat("OmniAI", "Olá! Como posso ajudar você hoje?")

        frame_input_ia = ctk.CTkFrame(container_ia, fg_color="transparent")
        frame_input_ia.pack(fill="x")

        self.entry_ia_prompt = ctk.CTkEntry(
            frame_input_ia,
            placeholder_text="Digite sua pergunta ou mensagem...",
            height=40,
            fg_color=COLOR_INPUT_BG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            font=("Segoe UI", 11)
        )
        self.entry_ia_prompt.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_ia_prompt.bind("<Return>", lambda e: self.enviar_mensagem_ia())

        btn_enviar_ia = ctk.CTkButton(
            frame_input_ia,
            text="Enviar 🚀",
            width=90,
            height=40,
            corner_radius=8,
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.enviar_mensagem_ia
        )
        btn_enviar_ia.pack(side="right")
        self.dynamic_accent_buttons.append(btn_enviar_ia)

    def adicionar_mensagem_chat(self, remetente, texto):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"[{remetente}]: {texto}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def enviar_mensagem_ia(self):
        mensagem = self.entry_ia_prompt.get().strip()
        if not mensagem:
            return

        self.entry_ia_prompt.delete(0, "end")
        self.adicionar_mensagem_chat("Você", mensagem)

        threading.Thread(target=self._processar_resposta_ia, args=(mensagem,), daemon=True).start()

    def _processar_resposta_ia(self, mensagem):
        time.sleep(0.5)
        resposta = f"Recebi sua mensagem: '{mensagem}'. Integração com IA pronta para ser expandida!"
        self.after(0, lambda: self.adicionar_mensagem_chat("OmniAI", resposta))

    # =========================================================================
    # ABA 3: PLAYER DE VÍDEO INTEGRADO
    # =========================================================================
    def montar_aba_player_video(self):
        container_video = ctk.CTkFrame(self.tab_video, fg_color="transparent")
        container_video.pack(fill="both", expand=True, padx=8, pady=8)

        self.video_player = TkinterVideo(master=container_video, scaled=True)
        self.video_player.pack(fill="both", expand=True, pady=(0, 8))

        frame_controles = ctk.CTkFrame(container_video, fg_color=COLOR_BG_CARD, corner_radius=8)
        frame_controles.pack(fill="x")

        btn_carregar = ctk.CTkButton(
            frame_controles,
            text="📁 Abrir Vídeo",
            width=100,
            height=32,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=self.carregar_arquivo_video
        )
        btn_carregar.pack(side="left", padx=8, pady=8)

        btn_play = ctk.CTkButton(
            frame_controles,
            text="▶️ Play",
            width=70,
            height=32,
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="#FFFFFF",
            command=lambda: self.video_player.play()
        )
        btn_play.pack(side="left", padx=4, pady=8)

        btn_pause = ctk.CTkButton(
            frame_controles,
            text="⏸️ Pause",
            width=70,
            height=32,
            fg_color=("#CBD5E1", "#334155"),
            text_color=COLOR_TEXT_PRIMARY,
            command=lambda: self.video_player.pause()
        )
        btn_pause.pack(side="left", padx=4, pady=8)

        btn_stop = ctk.CTkButton(
            frame_controles,
            text="⏹️ Stop",
            width=70,
            height=32,
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            command=lambda: self.video_player.stop()
        )
        btn_stop.pack(side="left", padx=4, pady=8)

    def carregar_arquivo_video(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um Arquivo de Vídeo",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.avi *.mkv *.mov *.wmv"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.video_player.load(caminho)
            self.video_player.play()

    # =========================================================================
    # ABA 4: CONFIGURAÇÕES E MONITOR DE RECURSOS DETALHADO
    # =========================================================================
    def montar_aba_config(self):
        scroll_config = ctk.CTkScrollableFrame(self.tab_config, fg_color="transparent")
        scroll_config.pack(fill="both", expand=True, padx=4, pady=4)

        frame_hw_detalhado = ctk.CTkFrame(scroll_config, fg_color=COLOR_BG_CARD, corner_radius=10)
        frame_hw_detalhado.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(
            frame_hw_detalhado,
            text="📊 Monitor de Hardware em Tempo Real",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 6))

        lbl_cpu_txt = ctk.CTkLabel(frame_hw_detalhado, text="Uso do Processador (CPU):", font=("Segoe UI", 11), text_color=COLOR_TEXT_PRIMARY)
        lbl_cpu_txt.pack(anchor="w", padx=12, pady=(4, 0))

        frame_bar_cpu = ctk.CTkFrame(frame_hw_detalhado, fg_color="transparent")
        frame_bar_cpu.pack(fill="x", padx=12, pady=(2, 8))

        self.bar_cpu_detalhada = ctk.CTkProgressBar(frame_bar_cpu, height=14, corner_radius=7)
        self.bar_cpu_detalhada.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.bar_cpu_detalhada.set(0)

        self.lbl_cpu_valor_detalhado = ctk.CTkLabel(frame_bar_cpu, text="0%", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_PRIMARY, width=50)
        self.lbl_cpu_valor_detalhado.pack(side="right")

        lbl_ram_txt = ctk.CTkLabel(frame_hw_detalhado, text="Memória RAM Usada:", font=("Segoe UI", 11), text_color=COLOR_TEXT_PRIMARY)
        lbl_ram_txt.pack(anchor="w", padx=12, pady=(4, 0))

        frame_bar_ram = ctk.CTkFrame(frame_hw_detalhado, fg_color="transparent")
        frame_bar_ram.pack(fill="x", padx=12, pady=(2, 12))

        self.bar_ram_detalhada = ctk.CTkProgressBar(frame_bar_ram, height=14, corner_radius=7)
        self.bar_ram_detalhada.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.bar_ram_detalhada.set(0)

        self.lbl_ram_valor_detalhado = ctk.CTkLabel(frame_bar_ram, text="0%", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT_PRIMARY, width=150)
        self.lbl_ram_valor_detalhado.pack(side="right")

        frame_cores = ctk.CTkFrame(scroll_config, fg_color=COLOR_BG_CARD, corner_radius=10)
        frame_cores.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(
            frame_cores,
            text="🎨 Personalização do Tema e Cores",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(10, 6))

        frame_botoes_cor = ctk.CTkFrame(frame_cores, fg_color="transparent")
        frame_botoes_cor.pack(fill="x", padx=12, pady=(4, 12))

        for nome_cor, dados in COLOR_ACCENTS.items():
            btn_c = ctk.CTkButton(
                frame_botoes_cor,
                text=nome_cor.capitalize(),
                width=80,
                height=32,
                corner_radius=6,
                fg_color=dados["primary"],
                hover_color=dados["hover"],
                text_color="#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                command=lambda c=nome_cor: self.aplicar_cor_acento(c)
            )
            btn_c.pack(side="left", padx=4)

    # =========================================================================
    # FUNÇÕES AUXILIARES DE EXECUÇÃO E GRID
    # =========================================================================
    def criar_cards_grid(self, parent_scroll, lista_items):
        frame_grid = ctk.CTkFrame(parent_scroll, fg_color="transparent")
        frame_grid.pack(fill="x", pady=4)

        for nome, alvo, cor in lista_items:
            btn = ctk.CTkButton(
                frame_grid,
                text=nome,
                height=40,
                corner_radius=8,
                fg_color=COLOR_BG_CARD,
                hover_color=("#CBD5E1", "#334155"),
                text_color=COLOR_TEXT_PRIMARY,
                border_color=COLOR_BORDER,
                border_width=1,
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                command=lambda a=alvo: self.abrir_inteligente(a)
            )
            btn.pack(fill="x", pady=3, padx=4)

    def selecionar_executavel_direto(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um Executável",
            filetypes=[("Executáveis e Atalhos", "*.exe *.lnk *.bat *.cmd"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.entry_universal.delete(0, "end")
            self.entry_universal.insert(0, caminho)

    def executar_busca_universal(self):
        alvo = self.entry_universal.get().strip()
        if alvo:
            self.abrir_inteligente(alvo)

    def abrir_inteligente(self, alvo):
        if not alvo:
            return

        try:
            if alvo.startswith(("http://", "https://")):
                webbrowser.open(alvo)
            elif ":" in alvo and not os.path.exists(alvo) and not alvo.endswith(".exe"):
                os.startfile(alvo)
            elif os.path.exists(alvo) or alvo.endswith(".exe"):
                subprocess.Popen(alvo)
            else:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(alvo)}")
        except Exception as e:
            print(f"[ERRO] Falha ao abrir '{alvo}': {e}")


class OmniOverlayApp(ctk.CTk):
    """Classe principal da Aplicação Gerenciadora de Telas e Estado Global."""

    def __init__(self):
        super().__init__()

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.98)
        self.title("OmniOverlay Engine")

        self.dados_config = AccountManager.carregar_dados()
        self.modo_tema_atual = self.dados_config.get("modo_tema", "dark")
        ctk.set_appearance_mode(self.modo_tema_atual)

        self.perfil_ativo = None
        self.centralizar_janela(920, 800)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frame_seletor = ProfileSelectorFrame(self.container, self)
        self.frame_dashboard = DashboardFrame(self.container, self)

        self.frame_seletor.grid(row=0, column=0, sticky="nsew")
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew")

        ultimo_id = self.dados_config.get("ultimo_perfil", "")
        perfil_encontrado = None

        for p in self.dados_config.get("perfis", []):
            if p["id"] == ultimo_id:
                perfil_encontrado = p
                break

        if perfil_encontrado:
            self.entrar_no_perfil(perfil_encontrado)
        else:
            self.abrir_seletor_perfis()

        # Inicia o ouvinte de atalho global para Alt + Z
        self.iniciar_hotkey_listener()

    def iniciar_hotkey_listener(self):
        """Registra o atalho global Alt + Z em segundo plano."""
        def on_activate():
            self.after(0, self.toggle_visibilidade)

        try:
            self.listener = keyboard.GlobalHotKeys({'<alt>+z': on_activate})
            self.listener.start()
        except Exception as e:
            print(f"[HOTKEY] Erro ao registrar o atalho Alt + Z: {e}")

    def toggle_visibilidade(self):
        """Exibe ou oculta a janela do aplicativo ao pressionar a tecla de atalho."""
        if self.winfo_viewable():
            self.withdraw()
        else:
            self.deiconify()
            self.attributes("-topmost", True)

    def centralizar_janela(self, largura, altura):
        self.update_idletasks()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (largura // 2)
        y = (hs // 2) - (altura // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def abrir_seletor_perfis(self):
        self.frame_seletor.atualizar_lista()
        self.frame_seletor.tkraise()

    def entrar_no_perfil(self, perfil):
        self.perfil_ativo = perfil
        self.dados_config["ultimo_perfil"] = perfil["id"]
        AccountManager.salvar_dados(self.dados_config)

        self.frame_dashboard.carregar_perfil(perfil)
        self.frame_dashboard.tkraise()

    def alternar_tema_global(self):
        if self.modo_tema_atual == "dark":
            self.modo_tema_atual = "light"
            self.frame_dashboard.btn_tema.configure(text="🌙")
        else:
            self.modo_tema_atual = "dark"
            self.frame_dashboard.btn_tema.configure(text="☀️")

        ctk.set_appearance_mode(self.modo_tema_atual)
        self.dados_config["modo_tema"] = self.modo_tema_atual
        AccountManager.salvar_dados(self.dados_config)


if __name__ == "__main__":
    app = OmniOverlayApp()
    app.mainloop()