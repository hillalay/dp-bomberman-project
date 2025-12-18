from __future__ import annotations
import pygame
import random
from typing import Optional

from model.ai.move_strategies import IMoveStrategy, RandomMoveStrategy


class Enemy:
    def __init__(self, x: int, y: int, tile_size: int, speed: float = 7.0, strategy: Optional[IMoveStrategy] = None):
        # speed = tile / second gibi düşün (7 iyi)
        self.ts = tile_size
        self.rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)

        self._last_dir = (0, 0)

        self.speed_tiles = speed
        self.strategy: IMoveStrategy = strategy or RandomMoveStrategy()

        self._moving = False
        self._dir = (0, 0)
        self._target_px = self.rect.topleft  # hedef pixel (tile köşesi)

        self._rethink_timer = 0.0
        self._rethink_interval = 1.0 / max(1e-6, self.speed_tiles)


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
        return not world.is_solid_cell(gx + dx, gy + dy)


        
    def _reverse_of(self, d: tuple[int,int]) -> tuple[int,int]:
        return (-d[0], -d[1])

    def valid_dirs(self, world, avoid_reverse: bool = True) -> list[tuple[int,int]]:
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        out = []
        rev = self._reverse_of(self._last_dir)

        for d in dirs:
            if d == (0,0):
                continue
            if avoid_reverse and self._last_dir != (0,0) and d == rev:
                continue
            if self._can_step(world, d[0], d[1]):
                out.append(d)
        return out


    def _start_step(self, world, dx: int, dy: int) -> bool:
        if dx == 0 and dy == 0:
            return False
        if not self._can_step(world, dx, dy):
            return False

        gx, gy = self.grid_pos()
        self._dir = (dx, dy)
        self._target_px = ((gx + dx) * self.ts, (gy + dy) * self.ts)
        self._moving = True
        self._last_dir = (dx, dy)

        return True

    def update(self, dt: float, world) -> None:
        # 1️⃣ Hareket halindeyse hedefe ilerle
        if self._moving:
            speed_px = self.speed_tiles * self.ts * dt
            cx, cy = self.rect.topleft
            tx, ty = self._target_px

            if cx < tx: cx = min(tx, cx + speed_px)
            if cx > tx: cx = max(tx, cx - speed_px)
            if cy < ty: cy = min(ty, cy + speed_px)
            if cy > ty: cy = max(ty, cy - speed_px)

            self.rect.topleft = (int(cx), int(cy))

            if self.rect.topleft == self._target_px:
                self._moving = False
            return  # 🔴 çok önemli

        # 2️⃣ Tile’a hizala (hareket bitince)
        self._snap_to_tile()

        # 3️⃣ Karar verme timer
        self._rethink_timer += dt
        if self._rethink_timer < self._rethink_interval:
            return
        self._rethink_timer = 0.0


        # 4️⃣ Strategy kararı
        dx, dy = self.strategy.choose_dir(self, world)

        # 5️⃣ Önce strategy yönü
        if not self._start_step(world, dx, dy):
            # Reverse hariç alternatifler
            options = self.valid_dirs(world, avoid_reverse=True)
            random.shuffle(options)
            moved = False
            for adx, ady in options:
                if self._start_step(world, adx, ady):
                    moved = True
                    break

            # Dead-end → reverse dahil
            if not moved:
                options = self.valid_dirs(world, avoid_reverse=False)
                random.shuffle(options)
                for adx, ady in options:
                    if self._start_step(world, adx, ady):
                        break

