from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from data.scores_repo import ScoresRepo

if TYPE_CHECKING:
    from core.game import Game


class WinState(GameState):
    def __init__(self, game: Game):
        super().__init__(game)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 26)

    def enter(self):
        print("[WinState] enter")

        user_id = getattr(self.game, "current_user_id", None) or getattr(self.game, "active_user_id", None)
        score = getattr(self.game, "score", 0)

        if user_id is not None:
            ScoresRepo().add_game_result(user_id=user_id, score=int(score), won=True)
            print("[WinState] ✅ win score saved")

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.game.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.start_new_game()
                from states.playing import PlayingState
                self.game.set_state(PlayingState(self.game))
                return

            if event.key in (pygame.K_m, pygame.K_ESCAPE):
                from states.menu import MenuState
                self.game.set_state(MenuState(self.game))
                return

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill((10, 10, 14))
        w, h = surface.get_size()

        title = self.title_font.render("YOU WIN!", True, (90, 220, 120))
        surface.blit(title, title.get_rect(center=(w // 2, h // 3)))

        lines = [
            f"Final Score: {getattr(self.game, 'score', 0)}",
            "",
            "Press R to Restart",
            "Press M or ESC to return to Menu",
        ]

        y = h // 2
        for line in lines:
            txt = self.text_font.render(line, True, (220, 220, 220))
            surface.blit(txt, txt.get_rect(center=(w // 2, y)))
            y += 36
