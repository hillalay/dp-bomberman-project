# src/states/menu.py

from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from ui.widgets import Button

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

        total_height = 3 * btn_height + 2 * spacing
        start_y = (height // 2) - total_height // 2 + 40  # biraz aşağı kaydır

        center_x = width // 2

        def make_rect(row_index: int) -> pygame.Rect:
            x = center_x - btn_width // 2
            y = start_y + row_index * (btn_height + spacing)
            return pygame.Rect(x, y, btn_width, btn_height)

        def on_play():
            from states.theme_select import ThemeSelectState
            self.game.set_state(ThemeSelectState(self.game))

        def on_options():
            print("[MenuState] Options clicked (TODO: OptionsState)")

        def on_exit():
            self.game.running = False

        self.buttons = [
            Button(make_rect(0), "Play", on_play, self.button_font),
            Button(make_rect(1), "Options", on_options, self.button_font),
            Button(make_rect(2), "Exit", on_exit, self.button_font),
        ]

    def enter(self) -> None:
        print("[MenuState] enter")

    def exit(self) -> None:
        print("[MenuState] exit")

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

        # Hafif ortadaki panel
        panel_rect = pygame.Rect(0, 0, surface.get_width() * 0.6, surface.get_height() * 0.6)
        panel_rect.center = (surface.get_width() // 2, surface.get_height() // 2 + 20)
        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 80))
        surface.blit(panel_surf, panel_rect.topleft)

        # Başlık
        title_surf = self.title_font.render("Bomberman DP", True, (230, 230, 255))
        title_rect = title_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(title_surf, title_rect)

        # Alt açıklama
        subtitle_surf = self.subtitle_font.render(
            "Press Play to start, ESC to pause", True, (180, 180, 200)
        )
        subtitle_rect = subtitle_surf.get_rect(center=(surface.get_width() // 2, title_rect.bottom + 24))
        surface.blit(subtitle_surf, subtitle_rect)

        # Butonlar
        for btn in self.buttons:
            btn.render(surface)
