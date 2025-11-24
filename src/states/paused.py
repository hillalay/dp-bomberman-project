# src/states/paused.py

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from ui.widgets import Button

if TYPE_CHECKING:
    from core.game import Game
    from states.base import GameState as BaseState


class PausedState(GameState):
    """
    Oyunu yarı saydam overlay ile donduran pause ekranı.
    Resume ve Exit to Menu butonları var.
    """

    def __init__(self, game: Game, underlying_state: BaseState):
        super().__init__(game)
        self.underlying_state = underlying_state

        self.title_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 28)

        self.buttons: list[Button] = []
        self._create_buttons()

    # ------------- Button setup ----------------
    def _create_buttons(self):
        surface = self.game.screen
        w, h = surface.get_size()

        btn_w, btn_h = 220, 60
        spacing = 20
        total_h = 2 * btn_h + spacing
        start_y = h // 2

        center_x = w // 2

        def make_rect(row_index: int) -> pygame.Rect:
            x = center_x - btn_w // 2
            y = start_y + row_index * (btn_h + spacing)
            return pygame.Rect(x, y, btn_w, btn_h)

        def on_resume():
            self.game.set_state(self.underlying_state)

        def on_exit_menu():
            from states.menu import MenuState
            self.game.set_state(MenuState(self.game))

        self.buttons = [
            Button(make_rect(0), "Resume", on_resume, self.button_font),
            Button(make_rect(1), "Exit to Menu", on_exit_menu, self.button_font),
        ]

    # ------------- Lifecycle -------------------
    def enter(self):
        print("[PausedState] enter")

    def exit(self):
        print("[PausedState] exit")

    # ------------- Input -----------------------
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # ESC de resume yapsın
            self.game.set_state(self.underlying_state)
            return

        for btn in self.buttons:
            btn.handle_event(event)

    # ------------- Update ----------------------
    def update(self, dt: float):
        # Oyun dondurulmuş, world.update yok
        for btn in self.buttons:
            btn.update(dt)

    # ------------- Render ----------------------
    def render(self, surface: pygame.Surface):
        # Önce alttaki state'i çiz (oyun dondurulmuş hal)
        self.underlying_state.render(surface)

        # Yarı saydam overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # alpha = 160
        surface.blit(overlay, (0, 0))

        # "Paused" yazısı
        title_surf = self.title_font.render("Paused", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(title_surf, title_rect)

        # Butonlar
        for btn in self.buttons:
            btn.render(surface)
