# src/states/playing.py

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState

if TYPE_CHECKING:
    from core.game import Game


class PlayingState(GameState):
    def __init__(self, game: Game):
        super().__init__(game)

        # Game'den model & input & renderer'ı çek
        self.world = game.world
        self.input_handler = game.input_handler
        self.renderer = game.renderer
        self.debug_font = pygame.font.SysFont("Arial", 24, bold=True)

    def enter(self):
        print("[PlayingState] enter")
        # Oyun müziğini çal
        self.game.sound.stop_music()


    def exit(self):
        print("[PlayingState] exit")
        # Müzik durdurulsun
        self.game.sound.stop_music()

    # ---------------- INPUT ----------------
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # ESC → PausedState
            from states.paused import PausedState
            self.game.set_state(PausedState(self.game, self))
        else:
            # Diğer input'lar dünyaya gitsin
            self.input_handler.handle_event(event, self.world)

    # ---------------- UPDATE ----------------
    def update(self, dt: float):
        self.world.update(dt)

    # ---------------- RENDER ----------------
    def render(self, surface: pygame.Surface):
        # Dünyayı Renderer ile çiz
        self.renderer.draw_world(self.world)

        # Sol üst köşe: ESC – Pause etiketi
        label = "ESC – Pause"
        text_surf = self.debug_font.render(label, True, (255, 255, 255))
        padding = 8

        bg_rect = text_surf.get_rect(topleft=(16, 16))
        bg_rect.inflate_ip(padding * 2, padding * 2)

        hud = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        hud.fill((0, 0, 0, 130))  # yarı şeffaf

        surface.blit(hud, bg_rect.topleft)
        surface.blit(text_surf, (bg_rect.x + padding, bg_rect.y + padding))
