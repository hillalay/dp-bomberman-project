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
    - UNBREAKABLE + HARD:
        * Renk: koyu gri (112,112,112)
        * Hepsi aynı boyutta (tile'ı doldurur)
        * Işık/gölge ile 3D efekti
        * SADECE kenardakilerde köşelerde küçük gölgeli topçuklar
    - BREAKABLE:
        * Açık gri tuğla desenli blok
    """

    def __init__(self, x, y, config, wall_type: WallType | None = None, breakable: bool = False):
        super().__init__(x, y, config)

        if wall_type is None:
            wall_type = WallType.BREAKABLE if breakable else WallType.UNBREAKABLE

        self.wall_type = wall_type

    def _base_color(self):
        # UNBREAKABLE + HARD → aynı koyu gri (#707070)
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            return (112, 112, 112)
        # BREAKABLE → açık gri
        if self.wall_type == WallType.BREAKABLE:
            return (192, 192, 204)
        return (255, 0, 255)

    def draw(self, s):
        base = self._base_color()
        outer = self.rect  # hepsi aynı boyut

        # Tile koordinatı → kenarda mıyız?
        tile_size = self.config.TILE_SIZE
        gw, gh = self.config.GRID_WIDTH, self.config.GRID_HEIGHT
        tx = self.rect.x // tile_size
        ty = self.rect.y // tile_size
        is_border = (tx == 0 or tx == gw - 1 or ty == 0 or ty == gh - 1)

        # ------------------------------------------
        # UNBREAKABLE + HARD
        # ------------------------------------------
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            # Ana blok
            pygame.draw.rect(s, base, outer)

            # Highlight tonları
            strong_light = (
                min(base[0] + 60, 255),
                min(base[1] + 60, 255),
                min(base[2] + 60, 255),
            )
            soft_light = (
                min(base[0] + 30, 255),
                min(base[1] + 30, 255),
                min(base[2] + 30, 255),
            )
            slight_shadow = (
                max(base[0] - 20, 0),
                max(base[1] - 20, 0),
                max(base[2] - 20, 0),
            )

            border_thick = 3

            # ÜST: güçlü highlight
            top_rect = pygame.Rect(outer.x, outer.y, outer.width, border_thick)
            pygame.draw.rect(s, strong_light, top_rect)

            # SOL: güçlü highlight
            left_rect = pygame.Rect(outer.x, outer.y, border_thick, outer.height)
            pygame.draw.rect(s, strong_light, left_rect)

            # ALT: yumuşak highlight
            bottom_rect = pygame.Rect(
                outer.x,
                outer.bottom - border_thick,
                outer.width,
                border_thick,
            )
            pygame.draw.rect(s, soft_light, bottom_rect)

            # SAĞ: hafif gölge
            right_rect = pygame.Rect(
                outer.right - border_thick,
                outer.y,
                border_thick,
                outer.height,
            )
            pygame.draw.rect(s, slight_shadow, right_rect)

            # İnce dış çerçeve
            pygame.draw.rect(s, (30, 30, 30), outer, 1)

            # ---- Kenar duvarlar için köşe topçukları ----
            if is_border:
                # Topçuk boyutu
                radius = max(tile_size // 10, 3)
                # Biraz koyu gölgeli ton
                knob_dark = (
                    max(base[0] - 25, 0),
                    max(base[1] - 25, 0),
                    max(base[2] - 25, 0),
                )
                knob_light = (
                    min(base[0] + 35, 255),
                    min(base[1] + 35, 255),
                    min(base[2] + 35, 255),
                )

                # Köşe merkezleri (biraz içerde)
                offset = radius + 3
                cx1 = outer.x + offset
                cx2 = outer.right - offset
                cy1 = outer.y + offset
                cy2 = outer.bottom - offset

                corners = [
                    (cx1, cy1),
                    (cx2, cy1),
                    (cx1, cy2),
                    (cx2, cy2),
                ]

                for (cx, cy) in corners:
                    # Alt taraf hafif gölge, üst taraf highlight hissi
                    pygame.draw.circle(s, knob_dark, (cx, cy), radius)
                    pygame.draw.circle(s, knob_light, (cx, cy - 1), radius - 1)

            return

        # ------------------------------------------
        # BREAKABLE → açık gri tuğla
        # ------------------------------------------
        if self.wall_type == WallType.BREAKABLE:
            inner = self.rect.inflate(-8, -8)

            # Ana gövde
            pygame.draw.rect(s, base, inner)

            # Üst highlight şeridi
            highlight = tuple(min(c + 40, 255) for c in base)
            h_strip = max(inner.height // 6, 2)
            top_strip = pygame.Rect(inner.x, inner.y, inner.width, h_strip)
            pygame.draw.rect(s, highlight, top_strip)

            mortar = (60, 60, 60)

            # 3 yatay sıra
            row_h = inner.height // 3
            y1 = inner.y + row_h
            y2 = inner.y + 2 * row_h

            pygame.draw.line(s, mortar, (inner.x, y1), (inner.right, y1), 2)
            pygame.draw.line(s, mortar, (inner.x, y2), (inner.right, y2), 2)

            # 3 sütunluk dikey derzler
            col_w = inner.width // 3
            x1 = inner.x + col_w
            x2 = inner.x + 2 * col_w

            for top in (inner.y, y1, y2):
                bottom = top + row_h
                pygame.draw.line(s, mortar, (x1, top), (x1, bottom), 2)
                pygame.draw.line(s, mortar, (x2, top), (x2, bottom), 2)

            pygame.draw.rect(s, (40, 40, 40), inner, 2)
            return

        # Fallback
        inner = self.rect.inflate(-8, -8)
        pygame.draw.rect(s, base, inner)
        pygame.draw.rect(s, (40, 40, 40), inner, 2)





    

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
