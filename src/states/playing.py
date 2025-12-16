from __future__ import annotations
import pygame
from typing import TYPE_CHECKING
from states.base import GameState

from controller.command_mapper import CommandMapper
from controller.command_invoker import CommandInvoker

if TYPE_CHECKING:
    from core.game import Game

class PlayingState(GameState):
    def __init__(self, game: Game):
        super().__init__(game)

        self.world = game.world
        self.renderer = game.renderer
        self.debug_font = pygame.font.SysFont("Arial", 24, bold=True)

        # Command Pattern
        self.command_mapper = CommandMapper()
        self.command_invoker = CommandInvoker()

        self.debug_font = pygame.font.SysFont("Arial", 24, bold=True)

    def enter(self):
        print("[PlayingState] enter")
        self.world=self.game.world
        self.renderer=self.game.renderer
        self.game.sound.stop_music()

    def exit(self):
        print("[PlayingState] exit")
        self.game.sound.stop_music()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from states.paused import PausedState
            self.game.set_state(PausedState(self.game, self))
            return

        cmd = self.command_mapper.map_event(event, self.world)
        if cmd is not None:
            self.command_invoker.execute(cmd)

    def update(self, dt: float):
        self.world.update(dt)

        #player öldüyse oyunu bitir
        if hasattr(self.world.player,"alive") and not self.world.player.alive:
            from states.game_over import GameOverState
            self.game.set_state(GameOverState(self.game))

    def render(self, surface: pygame.Surface):
        self.renderer.draw_world(self.world)
        label = "ESC – Pause"
        text_surf = self.debug_font.render(label, True, (255, 255, 255))
        padding = 8

        bg_rect = text_surf.get_rect(topleft=(16, 16))
        bg_rect.inflate_ip(padding * 2, padding * 2)

        hud = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        hud.fill((0, 0, 0, 130))

        surface.blit(hud, bg_rect.topleft)
        surface.blit(text_surf, (bg_rect.x + padding, bg_rect.y + padding))
