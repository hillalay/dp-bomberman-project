from __future__ import annotations
import pygame
from typing import Optional

from model.ai.move_strategies import IMoveStrategy, RandomMoveStrategy


class Enemy:
    def __init__(self, x: int, y: int, tile_size: int, speed: float = 7.0, strategy: Optional[IMoveStrategy] = None):
        # speed = tile / second gibi düşün (7 iyi)
        self.ts = tile_size
        self.rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)

        self.speed_tiles = speed
        self.strategy: IMoveStrategy = strategy or RandomMoveStrategy()

        self._moving = False
        self._dir = (0, 0)
        self._target_px = self.rect.topleft  # hedef pixel (tile köşesi)

        self._rethink_timer = 0.0
        self._rethink_interval = 0.2

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (220, 70, 70), self.rect)


    def grid_pos(self) -> tuple[int, int]:
        return (self.rect.x // self.ts, self.rect.y // self.ts)

    def _tile_rect(self, gx: int, gy: int) -> pygame.Rect:
        return pygame.Rect(gx * self.ts, gy * self.ts, self.ts, self.ts)

    def _snap_to_tile(self):
        gx, gy = self.grid_pos()
        self.rect.topleft = (gx * self.ts, gy * self.ts)

    def _can_step(self, world, dx: int, dy: int) -> bool:
        gx, gy = self.grid_pos()
        nxt = self._tile_rect(gx + dx, gy + dy)
        return not world.collides_with_solid(nxt)

    def _start_step(self, world, dx: int, dy: int) -> bool:
        if dx == 0 and dy == 0:
            return False
        if not self._can_step(world, dx, dy):
            return False

        gx, gy = self.grid_pos()
        self._dir = (dx, dy)
        self._target_px = ((gx + dx) * self.ts, (gy + dy) * self.ts)
        self._moving = True
        return True

    def update(self, dt: float, world) -> None:
        # Tile merkezine/kenarına oturt
        if not self._moving:
            self._snap_to_tile()

        # Hareket halindeyken hedefe ilerle
        if self._moving:
            speed_px = self.speed_tiles * self.ts * dt
            cx, cy = self.rect.topleft
            tx, ty = self._target_px

            # X yaklaş
            if cx < tx: cx = min(tx, cx + speed_px)
            if cx > tx: cx = max(tx, cx - speed_px)

            # Y yaklaş
            if cy < ty: cy = min(ty, cy + speed_px)
            if cy > ty: cy = max(ty, cy - speed_px)

            self.rect.topleft = (int(cx), int(cy))

            if self.rect.topleft == self._target_px:
                self._moving = False
            return

        # Yeni karar verme (tile üstündeyken)
        self._rethink_timer += dt
        if self._rethink_timer < self._rethink_interval:
            return
        self._rethink_timer = 0.0

        dx, dy = self.strategy.choose_dir(self, world)

        # Seçilen yön olmazsa: alternatif dene (takılma kesilir)
        if not self._start_step(world, dx, dy):
            for adx, ady in [(1,0), (-1,0), (0,1), (0,-1)]:
                if self._start_step(world, adx, ady):
                    break
