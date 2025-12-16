# src/states/menu.py

from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from ui.widgets import Button
from states.options import OptionsState  # Options menüsüne geçmek için
from utils.paths import asset_path

if TYPE_CHECKING:
    from core.game import Game
    from states.playing import PlayingState  # type: ignore


class MenuState(GameState):
    def __init__(self, game: Game) -> None:
        super().__init__(game)

        cfg = self.game.config

        # Tema rengine göre arka plan seç
        if cfg.THEME == "desert":
            self.background_color = (20, 18, 12)
        elif cfg.THEME == "forest":
            self.background_color = (10, 16, 14)
        elif cfg.THEME == "city":
            self.background_color = (12, 12, 16)
        else:
            self.background_color = cfg.BG_COLOR

        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 20)
        self.button_font = pygame.font.SysFont("Arial", 32)

        self.buttons: list[Button] = []
        self._create_buttons()

    def _create_buttons(self) -> None:
        screen = self.game.screen
        width, height = screen.get_size()

        btn_width = 260
        btn_height = 60
        spacing = 20

        # 4 butonluk yüksekliği hesapla (Play, Options, Exit,leaderboard)
        total_height = 4 * btn_height + 3 * spacing
        start_y = (height // 2) - total_height // 2 + 110  # biraz aşağı kaydır

        center_x = width // 2

        def make_rect(row_index: int) -> pygame.Rect:
            """
            row_index:
              0 -> Play
              1 -> Leaderboard
              2 -> Options
              3 ->Exit
            """
            x = center_x - btn_width // 2
            y = start_y + row_index * (btn_height + spacing)
            return pygame.Rect(x, y, btn_width, btn_height)

        # Play butonu: ThemeSelectState'e geç
        def on_play():
            from states.auth import AuthState
            self.game.set_state(AuthState(self.game))

        def on_leaderboard():
            from states.leaderboard import LeaderboardState
            self.game.set_state(LeaderboardState(self.game))

        # Options butonu: OptionsState'e geç
        def on_options():
            # Burada artık direkt OptionsState'e geçiyoruz
            self.game.set_state(OptionsState(self.game))

        # Exit butonu: oyunu kapat
        def on_exit():
            self.game.running = False

        # 3 butonluk liste
        self.buttons = [
            Button(make_rect(0), "Play", on_play, self.button_font),
            Button(make_rect(1),"Leaderboard",on_leaderboard,self.button_font),
            Button(make_rect(2), "Options", on_options, self.button_font),
            Button(make_rect(3), "Exit", on_exit, self.button_font),
        ]

    def enter(self) -> None:
        print("[MenuState] enter")

        # Menü müziğini çal
        try:
            path = asset_path("music", "menu_theme.mp3")
            print("[Audio] Menü müziği yükleniyor:", path)

            # 1) Müzik dosyasını yükle
            pygame.mixer.music.load(path)
            print("[Audio] Menü müziği yüklendi:", path)

            # 2) Volume'u ayarla config'ten gelsin(PreferencesRepo'dan)
            muted=getattr(self.game.config, "MUSIC_MUTED", False)
            volume=getattr(self.game.config, "MUSIC_VOLUME", 1.0)
            if muted:
                volume=0.0
            print("[Audio] Menü müziği volume ayarlanıyor:", volume)
            pygame.mixer.music.set_volume(volume)
            # 3) Müzik çal
            pygame.mixer.music.play(-1)  # -1 → sonsuz döngü
            print("[Audio] Music playing...")


        except Exception as e:
            print("[Audio] Menü müziği yüklenemedi:", repr(e))
             
    
    def exit(self) -> None:
        print("[MenuState] exit")
        #stop_music çağırmıyoruz. Müzik sadece oyun başlayınca duracak.


    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.game.running = False
            return

        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        for btn in self.buttons:
            btn.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(self.background_color)
        w, h = surface.get_width(), surface.get_height()

       # Başlık üstte kalsın diye paneli biraz aşağı al, boyunu küçült
        panel_w = int(w * 0.62)
        panel_h = int(h * 0.50)
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (w // 2, h // 2 + 70)

        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 110))
        surface.blit(panel_surf, panel_rect.topleft)

        # Başlık
        title_surf = self.title_font.render("Bomberman DP", True, (230, 230, 255))
        title_rect = title_surf.get_rect(center=(w // 2, 120))
        surface.blit(title_surf, title_rect)

        # Alt açıklama
        subtitle_surf = self.subtitle_font.render(
            "Press Play to start, ESC to pause", True, (180, 180, 200)
        )
        subtitle_rect = subtitle_surf.get_rect(center=(w // 2, 165))
        surface.blit(subtitle_surf, subtitle_rect)

        # Butonlar
        for btn in self.buttons:
            btn.render(surface)
