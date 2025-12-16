from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState

if TYPE_CHECKING:
    from core.game import Game


class GameOverState(GameState):
    def __init__(self, game: Game):
        super().__init__(game)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 26)

    def enter(self):
        print("[GameOverState] enter")
        # İstersen burada müziği durdurabilir veya game over jingle çalabilirsin:
        # self.game.sound.stop_music()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.game.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Restart: ThemeSelect -> Playing akışın nasıl ise ona dön
                self.game.start_new_game()
                from states.playing import PlayingState
                self.game.set_state(PlayingState(self.game))
                return

            if event.key in (pygame.K_m, pygame.K_ESCAPE):
                from states.menu import MenuState
                self.game.set_state(MenuState(self.game))
                return

    def update(self, dt: float):
        # GameOver ekranında dünya güncellenmez
        pass

    def render(self, surface: pygame.Surface):
        surface.fill((10, 10, 14))
        w, h = surface.get_size()

        title = self.title_font.render("GAME OVER", True, (220, 80, 80))
        surface.blit(title, title.get_rect(center=(w // 2, h // 3)))

        lines = [
            "You were killed by an explosion!",
            "",
            "Press R to Restart",
            "Press M or ESC to return to Menu",
        ]

        y = h // 2
        for line in lines:
            txt = self.text_font.render(line, True, (220, 220, 220))
            surface.blit(txt, txt.get_rect(center=(w // 2, y)))
            y += 36
