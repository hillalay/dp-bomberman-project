# src/view/renderer.py

from __future__ import annotations
import pygame
from core.config import GameConfig


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.config = GameConfig.get_instance()

    def draw_world(self, world):
        # 1) Zemin (checker pattern çim)
        self._draw_grass_background()

        # 2) Duvarlar
        for wall in world.walls:
            wall.draw(self.screen)

        # 3) Bombalar
        for bomb in world.bombs:
            bomb.draw(self.screen)

        # 4) Oyuncu
        if world.player is not None:
            world.player.draw(self.screen)

        # 5) Patlamalar (ileride)
        explosions = getattr(world, "explosions", [])
        for exp in explosions:
            exp.draw(self.screen)

    def _draw_grass_background(self):
        """
        Bomberman'deki gibi hafif desenli çim zemini.
        Tema paletindeki bg / bg_alt renklerini kullanıyoruz.
        """
        theme = self.config.THEMES[self.config.THEME]
        base = theme["bg"]
        alt = theme["bg_alt"]

        tile = self.config.TILE_SIZE
        cols = self.config.GRID_WIDTH
        rows = self.config.GRID_HEIGHT

        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * tile, y * tile, tile, tile)
                color = base if (x + y) % 2 == 0 else alt
                pygame.draw.rect(self.screen, color, rect)
