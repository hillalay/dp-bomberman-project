# src/factory/powerup_factory.py
import random
from model.entities import PowerUp, PowerUpType


class PowerUpFactory:
    def __init__(self, config):
        self.config = config

    def maybe_spawn(self, grid_x: int, grid_y: int) -> PowerUp | None:
        chance = float(getattr(self.config, "POWERUP_SPAWN_CHANCE", 0.08))
        if random.random() >= chance:
            return None

        types = [PowerUpType.BOMB_COUNT, PowerUpType.BOMB_POWER, PowerUpType.SPEED]

        weights_conf = getattr(self.config, "POWERUP_TYPE_WEIGHTS", None)
        if isinstance(weights_conf, dict):
            weights = [
                float(weights_conf.get("BOMB_COUNT", 1.0)),
                float(weights_conf.get("BOMB_POWER", 1.0)),
                float(weights_conf.get("SPEED", 1.0)),
            ]
        else:
            # fallback
            weights = [0.45, 0.40, 0.15]

        kind = random.choices(types, weights=weights, k=1)[0]
        return PowerUp(grid_x, grid_y, self.config, kind)
