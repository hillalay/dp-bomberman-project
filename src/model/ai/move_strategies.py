from __future__ import annotations
import random
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from model.enemy import Enemy
    from model.world import World


class IMoveStrategy(Protocol):
    def choose_dir(self, enemy: "Enemy", world: "World") -> tuple[int, int]: ...


class RandomMoveStrategy:
    def choose_dir(self, enemy: "Enemy", world: "World") -> tuple[int, int]:
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            if enemy._can_step(world, dx, dy):
                return (dx, dy)
        return (0, 0)




class ChasePlayerStrategy:
    def choose_dir(self, enemy: "Enemy", world: "World") -> tuple[int, int]:
        ex, ey = enemy.grid_pos()
        px = world.player.rect.centerx // world.config.TILE_SIZE
        py = world.player.rect.centery // world.config.TILE_SIZE

        dx = 0 if px == ex else (1 if px > ex else -1)
        dy = 0 if py == ey else (1 if py > ey else -1)

        # Hangisi daha uzaksa önce onu dene
        if abs(px - ex) >= abs(py - ey):
            if dx != 0 and enemy._can_step(world, dx, 0):
                return (dx, 0)
            if dy != 0 and enemy._can_step(world, 0, dy):
                return (0, dy)
        else:
            if dy != 0 and enemy._can_step(world, 0, dy):
                return (0, dy)
            if dx != 0 and enemy._can_step(world, dx, 0):
                return (dx, 0)

        return (0, 0)
