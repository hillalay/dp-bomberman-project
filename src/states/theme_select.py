# src/states/theme_select.py

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from ui.widgets import Button

if TYPE_CHECKING:
    from core.game import Game


class ThemeSelectState(GameState):
    """
    Play'e basınca açılan arena/tema seçimi ekranı.
    Desert / Forest / City butonları burada.
    """

    def __init__(self, game: Game):
        super().__init__(game)

        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 22)
        self.button_font = pygame.font.SysFont("Arial", 28)

        self.buttons: list[Button] = []
        self._create_buttons()

    def _create_buttons(self):
        surface = self.game.screen
        w, h = surface.get_size()

        btn_w, btn_h = 220, 60
        spacing = 20
        total_h = 3 * btn_h + 2 * spacing
        start_y = h // 2 - total_h // 2 + 40
        center_x = w // 2

        def make_rect(row_index: int) -> pygame.Rect:
            x = center_x - btn_w // 2
            y = start_y + row_index * (btn_h + spacing)
            return pygame.Rect(x, y, btn_w, btn_h)

        def choose_theme(theme: str):
            # Config'e temayı yaz ve Playing'e geç
            self.game.config.set_theme(theme)

            #DB tema tercihini kalıcı yap
            prefs = self.game.preferences_repo.get_or_create_for_user(self.game.active_user_id)

            self.game.preferences_repo.update_preferences(
                user_id=self.game.active_user_id,
                theme=theme,
                music_volume=prefs.music_volume,
                sfx_volume=prefs.sfx_volume,
                music_muted=prefs.music_muted,
                sfx_muted=prefs.sfx_muted,
            )
            #yeni oyunu başlat
            self.game.start_new_game()

            #Playing'e geç
            from states.playing import PlayingState
            self.game.set_state(PlayingState(self.game))

        self.buttons = [
            Button(make_rect(0), "Desert", lambda: choose_theme("desert"), self.button_font),
            Button(make_rect(1), "Forest", lambda: choose_theme("forest"), self.button_font),
            Button(make_rect(2), "City",   lambda: choose_theme("city"),   self.button_font),
        ]

    def enter(self):
        print("[ThemeSelectState] enter")

    def exit(self):
        print("[ThemeSelectState] exit")

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # ESC ile tekrar menüye dön
            from states.menu import MenuState
            self.game.set_state(MenuState(self.game))
            return

        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float):
        for btn in self.buttons:
            btn.update(dt)

    def render(self, surface: pygame.Surface):
        surface.fill((10, 10, 14))

        title_surf = self.title_font.render("Choose Arena", True, (230, 230, 255))
        title_rect = title_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(title_surf, title_rect)

        subtitle_surf = self.subtitle_font.render(
            "Where do you want to play?", True, (190, 190, 210)
        )
        subtitle_rect = subtitle_surf.get_rect(center=(surface.get_width() // 2, title_rect.bottom + 24))
        surface.blit(subtitle_surf, subtitle_rect)

        for btn in self.buttons:
            btn.render(surface)
