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
        options = enemy.valid_dirs(world, avoid_reverse=True)
        if options:
            random.shuffle(options)
            return options[0]

        # dead-end: reverse dahil dene
        options = enemy.valid_dirs(world, avoid_reverse=False)
        if options:
            random.shuffle(options)
            return options[0]

        return (0, 0)





class ChasePlayerStrategy:
    def choose_dir(self, enemy: "Enemy", world: "World") -> tuple[int, int]:
        ex, ey = enemy.grid_pos()
        px = world.player.rect.centerx // world.config.TILE_SIZE
        py = world.player.rect.centery // world.config.TILE_SIZE

        dx = 0 if px == ex else (1 if px > ex else -1)
        dy = 0 if py == ey else (1 if py > ey else -1)

        preferred: list[tuple[int,int]] = []

        # Hangisi daha uzaksa önce onu dene
        if abs(px - ex) >= abs(py - ey):
            if dx != 0: preferred.append((dx, 0))
            if dy != 0: preferred.append((0, dy))
        else:
            if dy != 0: preferred.append((0, dy))
            if dx != 0: preferred.append((dx, 0))

        # Reverse engelli şekilde dene
        valid = set(enemy.valid_dirs(world, avoid_reverse=True))
        for d in preferred:
            if d in valid:
                return d

        # Olmadıysa reverse engelli başka bir valid yön seç
        options = enemy.valid_dirs(world, avoid_reverse=True)
        if options:
            random.shuffle(options)
            return options[0]

        # dead-end: reverse dahil
        options = enemy.valid_dirs(world, avoid_reverse=False)
        if options:
            random.shuffle(options)
            return options[0]

        return (0, 0)

