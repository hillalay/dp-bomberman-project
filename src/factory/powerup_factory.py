# src/factory/powerup_factory.py

import random
from model.entities import PowerUp, PowerUpType


class PowerUpFactory:
    """
    Breakable duvar kırılınca:
      maybe_spawn(grid_x, grid_y) çağrılır.
    Belirli bir ihtimalle PowerUp döner, yoksa None döner.
    """

    def __init__(self, config):
        self.config = config

    def maybe_spawn(self, grid_x: int, grid_y: int) -> PowerUp | None:
        # Çıkma ihtimali (örnek: %35)
        if random.random() > 0.35:
            return None

        # Rastgele tür seç
        kind = random.choice([
            PowerUpType.BOMB_COUNT,
            PowerUpType.BOMB_POWER,
            PowerUpType.SPEED,
        ])

        return PowerUp(grid_x, grid_y, self.config, kind)
