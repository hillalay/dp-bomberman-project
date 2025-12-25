from __future__ import annotations

import os
import random
from typing import Optional

import pygame

from model.ai.move_strategies import IMoveStrategy, RandomMoveStrategy


class Enemy:
    # Path-safe sprite klasörü: src/model/enemy.py -> ../../assets/sprites/enemy
    ENEMY_SPRITE_BASE = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "assets", "sprites", "enemy"
    )

    _SPRITE_CACHE: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}

    def __init__(
        self,
        x: int,
        y: int,
        tile_size: int,
        speed: float = 5.0,
        strategy: Optional[IMoveStrategy] = None,
        enemy_type: int = 1,   # 👈 e1 / e2
    ):
        self.ts = tile_size
        self.rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)

        self.speed_tiles = speed
        self.strategy: IMoveStrategy = strategy or RandomMoveStrategy()

        self.enemy_type = 1 if enemy_type not in (1, 2) else enemy_type

        self._moving = False
        self._dir = (0, 0)
        self._last_dir = (0, 0)
        self._target_px = self.rect.topleft

        self._rethink_timer = 0.0
        # tile süresine yakın aralık: bekleme hissini azaltır
        self._rethink_interval = 1.0 / max(1e-6, self.speed_tiles)
                # --- Combat ---
        # type 1: tek vuruş
        # type 2: biraz daha dayanıklı (istersen 1 yap)
        self.hp = 1 if self.enemy_type == 1 else 2
        self.alive = True


    # ---------- Grid helpers ----------
    def grid_pos(self) -> tuple[int, int]:
        return (self.rect.x // self.ts, self.rect.y // self.ts)

    def _tile_rect(self, gx: int, gy: int) -> pygame.Rect:
        return pygame.Rect(gx * self.ts, gy * self.ts, self.ts, self.ts)

    def _snap_to_tile(self):
        gx, gy = self.grid_pos()
        self.rect.topleft = (gx * self.ts, gy * self.ts)

    def _reverse_of(self, d: tuple[int, int]) -> tuple[int, int]:
        return (-d[0], -d[1])

    def _can_step(self, world, dx: int, dy: int) -> bool:
        gx, gy = self.grid_pos()
        # World tarafında grid-based kontrolün var:
        # is_solid_cell(gx, gy) varsa onu kullanır.
        if hasattr(world, "is_solid_cell"):
            return not world.is_solid_cell(gx + dx, gy + dy)
        # fallback (eski rect collision)
        nxt = self._tile_rect(gx + dx, gy + dy)
        return not world.collides_with_solid(nxt)

    def valid_dirs(self, world, avoid_reverse: bool = True) -> list[tuple[int, int]]:
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        out: list[tuple[int, int]] = []
        rev = self._reverse_of(self._last_dir)

        for d in dirs:
            if avoid_reverse and self._last_dir != (0, 0) and d == rev:
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
        self._last_dir = (dx, dy)
        self._target_px = ((gx + dx) * self.ts, (gy + dy) * self.ts)
        self._moving = True
        return True

    # ---------- Sprite helpers ----------
    @staticmethod
    def _load_enemy_sprite(code: str, size: tuple[int, int]) -> pygame.Surface:
        key = (code, size)
        if key not in Enemy._SPRITE_CACHE:
            path = os.path.join(Enemy.ENEMY_SPRITE_BASE, f"{code}.png")
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            Enemy._SPRITE_CACHE[key] = img
        return Enemy._SPRITE_CACHE[key]

    def _dir_to_letter(self) -> str:
        dx, dy = self._dir
        # pygame: aşağı +y
        if dx == 1:
            return "r"
        if dx == -1:
            return "l"
        if dy == 1:
            return "f"
        if dy == -1:
            return "b"
        return "f"


    def take_damage(self, dmg: int = 1) -> bool:
        """
        Returns True if enemy died.
        """
        if not self.alive:
            return True
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    # ---------- Main loop ----------
    def update(self, dt: float, world) -> None:
        # Hareket halindeyken hedefe ilerle
        if self._moving:
            speed_px = self.speed_tiles * self.ts * dt
            cx, cy = self.rect.topleft
            tx, ty = self._target_px

            if cx < tx:
                cx = min(tx, cx + speed_px)
            if cx > tx:
                cx = max(tx, cx - speed_px)

            if cy < ty:
                cy = min(ty, cy + speed_px)
            if cy > ty:
                cy = max(ty, cy - speed_px)

            self.rect.topleft = (int(cx), int(cy))

            if self.rect.topleft == self._target_px:
                self._moving = False
            return

        # tile üstüne hizala
        self._snap_to_tile()

        # karar verme aralığı
        self._rethink_timer += dt
        if self._rethink_timer < self._rethink_interval:
            return
        self._rethink_timer = 0.0

        # Strategy kararı
        dx, dy = self.strategy.choose_dir(self, world)

        # Önce seçilen yön
        if not self._start_step(world, dx, dy):
            # Reverse hariç alternatif
            options = self.valid_dirs(world, avoid_reverse=True)
            random.shuffle(options)
            moved = False
            for adx, ady in options:
                if self._start_step(world, adx, ady):
                    moved = True
                    break

            # dead-end: reverse dahil
            if not moved:
                options = self.valid_dirs(world, avoid_reverse=False)
                random.shuffle(options)
                for adx, ady in options:
                    if self._start_step(world, adx, ady):
                        break

    def draw(self, screen: pygame.Surface) -> None:
        # hareket ediyorsa anim aksın, değilse orta frame
        if self._moving:
            frame = (pygame.time.get_ticks() // 120) % 3  # 0,1,2
        else:
            frame = 1

        letter = self._dir_to_letter()
        code = f"e{self.enemy_type}{letter}{frame}"  # örn: e2r0

        img = Enemy._load_enemy_sprite(code, (self.rect.width, self.rect.height))
        screen.blit(img, self.rect)
