# src/view/renderer.py
from __future__ import annotations

import pygame
from core.config import GameConfig


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.config = GameConfig.get_instance()

    def draw_world(self, world) -> None:
        # 1) Zemin
        self._draw_grass_background()

        ts = self.config.TILE_SIZE

        # 2) Duvarlar
        # Client tarafında: world.walls zaten PlayingState._apply_snapshot ile gerçek Wall objelerine çevriliyor.
        # Eğer world.walls yoksa fallback olarak _net_walls çiz.
        if getattr(world, "walls", None):
            for wall in world.walls:
                wall.draw(self.screen)
        elif hasattr(world, "_net_walls"):
            for w in world._net_walls:
                r = pygame.Rect(int(w["gx"]) * ts, int(w["gy"]) * ts, ts, ts)
                pygame.draw.rect(self.screen, (120, 120, 120), r)

        # 3) Bombalar
        # Local/Server: world.bombs objeleri
        if getattr(world, "bombs", None):
            for bomb in world.bombs:
                bomb.draw(self.screen)
        # Client: _net_bombs ham liste
        elif hasattr(world, "_net_bombs"):
            for b in world._net_bombs:
                r = pygame.Rect(int(b["x"]), int(b["y"]), ts, ts)
                pygame.draw.rect(self.screen, (200, 0, 0), r)

        # 4) PowerUps
        # Local/Server: world.powerups objeleri
        if getattr(world, "powerups", None):
            for pu in world.powerups:
                pu.draw(self.screen)
        # Client: _net_powerups ham liste (şimdilik basit kutu)
        elif hasattr(world, "_net_powerups"):
            for pu in world._net_powerups:
                r = pygame.Rect(int(pu["x"]), int(pu["y"]), ts, ts)
                pygame.draw.rect(self.screen, (80, 200, 80), r)

        # 5) Enemies
        if getattr(world, "enemies", None):
            for e in world.enemies:
                e.draw(self.screen)
        elif hasattr(world, "_net_enemies"):
            for e in world._net_enemies:
                r = pygame.Rect(int(e["x"]), int(e["y"]), ts, ts)
                pygame.draw.rect(self.screen, (255, 80, 80), r)

        # 6) Players
        if hasattr(world, "players") and world.players:
            for p in world.players.values():
                if p is not None and getattr(p, "alive", True):
                    p.draw(self.screen)
        elif getattr(world, "player", None) is not None:
            world.player.draw(self.screen)

        # 7) Patlama FX
        for fx in getattr(world, "explosions_fx", []):
            fx.draw(self.screen)

    def _draw_grass_background(self) -> None:
        """
        Tek renk zemin. Renk: theme["bg"]
        """
        theme = self.config.THEMES[self.config.THEME]
        base = theme["bg"]

        tile = self.config.TILE_SIZE
        cols = self.config.GRID_WIDTH
        rows = self.config.GRID_HEIGHT

        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * tile, y * tile, tile, tile)
                pygame.draw.rect(self.screen, base, rect)
