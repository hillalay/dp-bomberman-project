# src/core/game.py

from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

from core.config import GameConfig
from model.world import World
from controller.input_handler import InputHandler
from view.renderer import Renderer

if TYPE_CHECKING:
    from states.base import GameState


class Game:
    def __init__(self):
        pygame.init()

        # CONFIG & SCREEN
        self.config = GameConfig.get_instance()
        self.screen = pygame.display.set_mode(
            (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("DP Bomberman")

        self.clock = pygame.time.Clock()
        self.running = True

        # Model & View (PlayingState kullanacak)
        self.world = World(self.config)
        self.input_handler = InputHandler()
        self.renderer = Renderer(self.screen)

        # İlk state: Menü
        from states.menu import MenuState
        self.current_state: GameState = MenuState(self)
        self.current_state.enter()

    # STATE DEĞİŞTİRME
    def set_state(self, new_state: "GameState"):
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()

    # ANA LOOP
    def run(self):
        while self.running:
            dt = self.clock.tick(self.config.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_state.handle_event(event)

            if not self.running:
                break

            self.current_state.update(dt)
            self.current_state.render(self.screen)

            pygame.display.flip()

        pygame.quit()
