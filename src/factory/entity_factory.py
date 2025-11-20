from model.entities import Player, Wall, Bomb, WallType


class EntityFactory:
    def __init__(self, config):
        self.config = config

    def create(self, entity_type: str, **kwargs):
        if entity_type == "player":
            return self._create_player(**kwargs)
        elif entity_type == "wall":
            return self._create_wall(**kwargs)
        elif entity_type == "bomb":
            return self._create_bomb(**kwargs)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

    # ---- Factory Methods ----

    def _create_player(self, x, y):
        return Player(x, y, self.config)

    def _create_wall(
        self,
        x,
        y,
        wall_type: WallType | None = None,
        breakable: bool = False,
    ):
        # Wall sınıfı zaten wall_type None ise breakable’a göre karar verecek
        return Wall(x, y, self.config, wall_type=wall_type, breakable=breakable)

    def _create_bomb(self, x, y, owner):
        return Bomb(x, y, owner, self.config)
