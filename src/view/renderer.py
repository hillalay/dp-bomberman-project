# src/view/renderer.py

from __future__ import annotations
import pygame
from core.config import GameConfig


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.config = GameConfig.get_instance()

    def draw_world(self, world):
        # 1) Zemin
        self._draw_grass_background()

        # 2) Duvarlar
        for wall in world.walls:
            wall.draw(self.screen)

        # 3) Bombalar
        for bomb in world.bombs:
            bomb.draw(self.screen)

        for pu in getattr(world, "powerups", []):
            pu.draw(self.screen)

        
        # 4) Enemies
        for e in getattr(world, "enemies", []):
            e.draw(self.screen)

        # 5) Oyuncu
        if world.player is not None:
            world.player.draw(self.screen)

        # 6) Patlamalar 
        for fx in world.explosions_fx:
            fx.draw(self.screen)


    def _draw_grass_background(self):
        """
        Tek renk çim zemini — hiçbir desen yok.
        Renk: theme["bg"]
        """
        theme = self.config.THEMES[self.config.THEME]
        base = theme["bg"]  # örn: (46, 126, 2)

        tile = self.config.TILE_SIZE
        cols = self.config.GRID_WIDTH
        rows = self.config.GRID_HEIGHT

        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * tile, y * tile, tile, tile)
                pygame.draw.rect(self.screen, base, rect)
