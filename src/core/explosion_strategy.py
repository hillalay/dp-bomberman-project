# src/core/explosion_strategy.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, List, Tuple


GridPos = Tuple[int, int]


class ExplosionStrategy(ABC):
    """
    Patlamanın hangi tile'lara yayılacağını hesaplayan arayüz.
    Normal, plus-shaped, cross-shaped, vs. farklı stratejiler buradan türeyecek.
    """

    @abstractmethod
    def compute_tiles(
        self,
        origin: GridPos,
        power: int,
        is_blocking: Callable[[GridPos], bool],
        is_breakable: Callable[[GridPos], bool],
    ) -> List[GridPos]:
        """
        origin: (x, y) bomba tile'ı
        power: kaç tile uzağa kadar gidebilir
        is_blocking: unbreakable / map dışı mı?
        is_breakable: breakable wall var mı?
        """
        raise NotImplementedError
        

class NormalExplosionStrategy(ExplosionStrategy):
    """
    Klasik Bomberman patlaması:
    - Ortadan 4 yöne (sağ, sol, yukarı, aşağı)
    - Unbreakable wall'da dur
    - Breakable wall'ı kapsa ama devam etme
    """

    DIRECTIONS: list[GridPos] = [(1, 0), (-1, 0), (0, -1), (0, 1)]

    def compute_tiles(
        self,
        origin: GridPos,
        power: int,
        is_blocking: Callable[[GridPos], bool],
        is_breakable: Callable[[GridPos], bool],
    ) -> List[GridPos]:
        x0, y0 = origin
        tiles: List[GridPos] = [origin]  # merkez her zaman var

        for dx, dy in self.DIRECTIONS:
            for step in range(1, power + 1):
                nx = x0 + dx * step
                ny = y0 + dy * step
                pos = (nx, ny)

                # Map dışı veya unbreakable wall
                if is_blocking(pos):
                    break

                tiles.append(pos)

                # Breakable wall varsa burayı kapsa ama devam etme
                if is_breakable(pos):
                    break

        return tiles
