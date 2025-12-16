# src/states/leaderboard.py
from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from ui.widgets import Button
from data.scores_repo import ScoresRepo

if TYPE_CHECKING:
    from core.game import Game


class LeaderboardState(GameState):
    """
    Leaderboard ekranı.
    - ScoresRepo.get_leaderboard() ile TOP skorları çeker
    - Listeler
    - ESC veya Back ile MenuState'e döner
    """

    def __init__(self, game: Game) -> None:
        super().__init__(game)

        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.row_font = pygame.font.SysFont("Arial", 22)
        self.button_font = pygame.font.SysFont("Arial", 24)

        # Repo
        self.scores_repo = ScoresRepo()

        # Data
        self.entries = []

        # UI
        self.buttons: list[Button] = []
        self._create_buttons()

    def _create_buttons(self) -> None:
        screen = self.game.screen
        w, h = screen.get_size()

        btn_w, btn_h = 220, 56
        rect = pygame.Rect(0, 0, btn_w, btn_h)
        rect.center = (w // 2, h - 90)

        def on_back():
            from states.menu import MenuState
            self.game.set_state(MenuState(self.game))

        self.buttons = [
            Button(rect, "Back to Menu", on_back, self.button_font)
        ]

    def enter(self) -> None:
        print("[LeaderboardState] enter")
        # DB'den çek
        try:
            self.entries = self.scores_repo.get_leaderboard(limit=10)
        except Exception as e:
            print("[LeaderboardState] leaderboard yüklenemedi:", repr(e))
            self.entries = []

    def exit(self) -> None:
        print("[LeaderboardState] exit")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.game.running = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from states.menu import MenuState
            self.game.set_state(MenuState(self.game))
            return

        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        for btn in self.buttons:
            btn.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((10, 12, 18))
        w, h = surface.get_size()

        # Title
        title = self.title_font.render("Leaderboard", True, (230, 230, 255))
        surface.blit(title, title.get_rect(center=(w // 2, 90)))

        # Table headers
        left_x = w // 2 - 260
        top_y = 150

        hdr_rank = self.header_font.render("#", True, (180, 180, 200))
        hdr_user = self.header_font.render("Username", True, (180, 180, 200))
        hdr_score = self.header_font.render("Score", True, (180, 180, 200))
        hdr_won = self.header_font.render("Won", True, (180, 180, 200))

        surface.blit(hdr_rank, (left_x, top_y))
        surface.blit(hdr_user, (left_x + 50, top_y))
        surface.blit(hdr_score, (left_x + 260, top_y))
        surface.blit(hdr_won, (left_x + 360, top_y))

        # Divider
        pygame.draw.line(surface, (80, 90, 120), (left_x, top_y + 34), (left_x + 420, top_y + 34), 2)

        # Rows
        row_y = top_y + 50
        row_h = 30

        if not self.entries:
            empty = self.row_font.render("No scores yet.", True, (200, 120, 120))
            surface.blit(empty, empty.get_rect(center=(w // 2, row_y + 40)))
        else:
            for i, e in enumerate(self.entries, start=1):
                rank_s = self.row_font.render(str(i), True, (230, 230, 230))
                user_s = self.row_font.render(e.username, True, (230, 230, 230))
                score_s = self.row_font.render(str(e.score), True, (230, 230, 230))
                won_s = self.row_font.render("Yes" if e.won else "No", True, (230, 230, 230))

                y = row_y + (i - 1) * row_h
                surface.blit(rank_s, (left_x, y))
                surface.blit(user_s, (left_x + 50, y))
                surface.blit(score_s, (left_x + 260, y))
                surface.blit(won_s, (left_x + 360, y))

        # Buttons
        for btn in self.buttons:
            btn.render(surface)

        # Hint
        hint = self.row_font.render("ESC: Back", True, (160, 160, 180))
        surface.blit(hint, (20, h - 40))
