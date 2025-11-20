import pygame
from enum import Enum, auto
class WallType(Enum):
    UNBREAKABLE = auto()
    BREAKABLE = auto()
    HARD = auto()


class Entity:
    def __init__(self, x, y, config):
        self.config = config
        self.rect = pygame.Rect(
            x * config.TILE_SIZE,
            y * config.TILE_SIZE,
            config.TILE_SIZE,
            config.TILE_SIZE,
        )

    def update(self, dt, world):
        pass

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 255), self.rect)  # default pembe kare


class Player(Entity):
    def __init__(self, x, y, config):
        super().__init__(x, y, config)
        self.speed = config.PLAYER_SPEED
        self.color = config.COLOR_PLAYER
        self.move_dir = pygame.Vector2(0, 0)  # input buraya yazılacak

    def update(self, dt, world):
        if self.move_dir.length_squared() > 0:
            move = self.move_dir.normalize() * self.speed * dt
            new_rect = self.rect.move(move.x, move.y)

            # Duvarlara çarparsa gitmesin
            if not world.collides_with_solid(new_rect):
                self.rect = new_rect

    def draw(self, s):
        pygame.draw.rect(s, self.color, self.rect)

class Wall(Entity):
    def __init__(self, x, y, config, wall_type: WallType | None = None, breakable: bool = False):
        super().__init__(x, y, config)

        # Eğer wall_type verilmemişse eski breakable paramına göre belirle
        if wall_type is None:
            wall_type = WallType.BREAKABLE if breakable else WallType.UNBREAKABLE

        self.wall_type = wall_type

    def _get_color(self):
        # wall_type -> renk map’i
        if self.wall_type == WallType.UNBREAKABLE:
            return self.config.COLOR_WALL_UNBREAKABLE
        elif self.wall_type == WallType.BREAKABLE:
            return self.config.COLOR_WALL_BREAKABLE
        elif self.wall_type == WallType.HARD:
            return self.config.COLOR_WALL_HARD

        # Her ihtimale karşı fallback (mor)
        return (255, 0, 255)

    def draw(self, s):
        color = self._get_color()
        pygame.draw.rect(s, color, self.rect)
        inner = self.rect.inflate(-8, -8)
        pygame.draw.rect(s, (0, 0, 0), inner, width=1)


class Bomb(Entity):
    def __init__(self, x, y, owner, config):
        super().__init__(x, y, config)
        self.owner = owner
        self.timer = config.BOMB_TIMER
        self.color = config.COLOR_BOMB

    def update(self, dt, world):
        self.timer -= dt
        if self.timer <= 0:
            self.explode(world)

    def explode(self, world):
        print("BOOM!")  # şimdilik sadece log
        world.handle_explosion(self)

    def draw(self, s):
        pygame.draw.rect(s, self.color, self.rect)
