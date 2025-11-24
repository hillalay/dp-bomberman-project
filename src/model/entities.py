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
        # Debug için default pembe kare
        pygame.draw.rect(surface, (255, 0, 255), self.rect)


# ----------------------------------------------------
# PLAYER
# ----------------------------------------------------
class Player(Entity):
    def __init__(self, x, y, config):
        super().__init__(x, y, config)
        self.speed = config.PLAYER_SPEED
        self.color = self.config.COLOR_PLAYER
        self.move_dir = pygame.Vector2(0, 0)

    def update(self, dt, world):
        if self.move_dir.length_squared() > 0:
            move = self.move_dir.normalize() * self.speed * dt
            new_rect = self.rect.move(move.x, move.y)

            # Duvarlara çarpıyorsa hareket etme
            if not world.collides_with_solid(new_rect):
                self.rect = new_rect

    def draw(self, s):
        pygame.draw.rect(s, self.color, self.rect)


# ----------------------------------------------------
# WALL
# ----------------------------------------------------
class Wall(Entity):
    """
    - UNBREAKABLE + HARD: tek renk koyu gri blok (kenarlar + orta sütunlar)
    - BREAKABLE: açık gri tuğla desenli blok (kırılabilir duvar)
    """

    def __init__(self, x, y, config, wall_type: WallType | None = None, breakable: bool = False):
        super().__init__(x, y, config)

        if wall_type is None:
            wall_type = WallType.BREAKABLE if breakable else WallType.UNBREAKABLE

        self.wall_type = wall_type

    def _base_color(self):
        # Kenar ve ortadaki sert bloklar: aynı koyu gri
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            return (120, 120, 130)  # koyu gri
        # Kırılabilir duvar: açık gri
        if self.wall_type == WallType.BREAKABLE:
            return (192, 192, 204)  # açık gri
        return (255, 0, 255)
    
    def draw(self, s):
        base = self._base_color()
        outer = self.rect.inflate(-8, -8)  # çim payı

        # ------------------------------------------
        # UNBREAKABLE + HARD → koyu gri blok + ışık/gölge
        # ------------------------------------------
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            # Ana blok
            pygame.draw.rect(s, base, outer)

            # Highlight ve shadow renkleri
            light = (min(base[0] + 60, 255),
                     min(base[1] + 60, 255),
                     min(base[2] + 60, 255))
            shadow = (max(base[0] - 60, 0),
                      max(base[1] - 60, 0),
                      max(base[2] - 60, 0))

            border_thick = 3

            # ÜST highlight
            top_rect = pygame.Rect(
                outer.x,
                outer.y,
                outer.width,
                border_thick,
            )
            pygame.draw.rect(s, light, top_rect)

            # SOL highlight
            left_rect = pygame.Rect(
                outer.x,
                outer.y,
                border_thick,
                outer.height,
            )
            pygame.draw.rect(s, light, left_rect)

            # ALT shadow
            bottom_rect = pygame.Rect(
                outer.x,
                outer.bottom - border_thick,
                outer.width,
                border_thick,
            )
            pygame.draw.rect(s, shadow, bottom_rect)

            # SAĞ shadow
            right_rect = pygame.Rect(
                outer.right - border_thick,
                outer.y,
                border_thick,
                outer.height,
            )
            pygame.draw.rect(s, shadow, right_rect)

            # İnce dış çizgi (kontrast için)
            pygame.draw.rect(s, (30, 30, 30), outer, 1)

            return

        # ------------------------------------------
        # BREAKABLE → açık gri tuğla (daha önce yaptığımız)
        # ------------------------------------------
        if self.wall_type == WallType.BREAKABLE:
            # Ana gövde
            pygame.draw.rect(s, base, outer)

            # Üst highlight şeridi
            highlight = tuple(min(c + 40, 255) for c in base)
            h_strip = max(outer.height // 6, 2)
            top_strip = pygame.Rect(outer.x, outer.y, outer.width, h_strip)
            pygame.draw.rect(s, highlight, top_strip)

            mortar = (60, 60, 60)

            # 3 yatay sıra
            row_h = outer.height // 3
            y1 = outer.y + row_h
            y2 = outer.y + 2 * row_h

            pygame.draw.line(s, mortar, (outer.x, y1), (outer.right, y1), 2)
            pygame.draw.line(s, mortar, (outer.x, y2), (outer.right, y2), 2)

            # 3 sütunluk dikey derzler
            col_w = outer.width // 3
            x1 = outer.x + col_w
            x2 = outer.x + 2 * col_w

            for top in (outer.y, y1, y2):
                bottom = top + row_h
                pygame.draw.line(s, mortar, (x1, top), (x1, bottom), 2)
                pygame.draw.line(s, mortar, (x2, top), (x2, bottom), 2)

            pygame.draw.rect(s, (40, 40, 40), outer, 2)
            return

        # ------------------------------------------
        # Fallback (gerek kalmaz ama dursun)
        # ------------------------------------------
        pygame.draw.rect(s, base, outer)
        pygame.draw.rect(s, (40, 40, 40), outer, 2)


    

# ----------------------------------------------------
# BOMB
# ----------------------------------------------------
class Bomb(Entity):
    def __init__(self, x, y, owner, config):
        super().__init__(x, y, config)
        self.owner = owner
        self.timer = config.BOMB_TIMER
        self.color = self.config.COLOR_BOMB

    def update(self, dt, world):
        self.timer -= dt
        if self.timer <= 0:
            self.explode(world)

    def explode(self, world):
        print("BOOM!")
        world.handle_explosion(self)

    def draw(self, s):
        pygame.draw.rect(s, self.color, self.rect)
