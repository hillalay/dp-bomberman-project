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
        * Koyu gri 3D metal blok
        * Kenarlarda köşe topçukları
    - BREAKABLE:
        * Tuğla deseni (forest’te yaptığımız):
          Satır 1 : [■■■■■■■■]      (tek uzun tuğla)
          Satır 2 : [■][■■■■■■]     (1 | 23)
          Satır 3 : [■■■■■■][■]     (12 | 3)
    """

    def __init__(self, x, y, config, wall_type: WallType | None = None, breakable: bool = False):
        super().__init__(x, y, config)

        if wall_type is None:
            wall_type = WallType.BREAKABLE if breakable else WallType.UNBREAKABLE

        self.wall_type = wall_type

    def _base_color(self):
        # UNBREAKABLE / HARD → koyu gri
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            return (112, 112, 112)
        # BREAKABLE → forest’te seçtiğimiz koyu tuğla gri (#767a7a)
        if self.wall_type == WallType.BREAKABLE:
            return (118, 122, 122)
        return (255, 0, 255)

    def draw(self, s):
        base = self._base_color()
        outer = self.rect

        tile_size = self.config.TILE_SIZE
        gw, gh = self.config.GRID_WIDTH, self.config.GRID_HEIGHT
        tx = self.rect.x // tile_size
        ty = self.rect.y // tile_size
        is_border = (tx == 0 or tx == gw - 1 or ty == 0 or ty == gh - 1)

        # -------------------------------------------------
        # UNBREAKABLE / HARD → 3D metal blok
        # -------------------------------------------------
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            pygame.draw.rect(s, base, outer)

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

            # ÜST highlight
            top_rect = pygame.Rect(outer.x, outer.y, outer.width, border_thick)
            pygame.draw.rect(s, strong_light, top_rect)

            # SOL highlight
            left_rect = pygame.Rect(outer.x, outer.y, border_thick, outer.height)
            pygame.draw.rect(s, strong_light, left_rect)

            # ALT yumuşak highlight
            bottom_rect = pygame.Rect(
                outer.x,
                outer.bottom - border_thick,
                outer.width,
                border_thick,
            )
            pygame.draw.rect(s, soft_light, bottom_rect)

            # SAĞ hafif gölge
            right_rect = pygame.Rect(
                outer.right - border_thick,
                outer.y,
                border_thick,
                outer.height,
            )
            pygame.draw.rect(s, slight_shadow, right_rect)

            # İnce outline
            pygame.draw.rect(s, (30, 30, 30), outer, 1)

            # Kenar duvar köşe topçukları
            if is_border:
                radius = max(tile_size // 10, 3)
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
                    pygame.draw.circle(s, knob_dark, (cx, cy), radius)
                    pygame.draw.circle(s, knob_light, (cx, cy - 1), radius - 1)

            return

        # -------------------------------------------------
        # BREAKABLE → forest-style tuğla pattern
        # -------------------------------------------------
        if self.wall_type == WallType.BREAKABLE:
            inner = outer  # full tile

            # Harç arka planı (koyu)
            pygame.draw.rect(s, (20, 20, 20), inner)

            brick_color = base
            highlight = (
                min(brick_color[0] + 30, 255),
                min(brick_color[1] + 30, 255),
                min(brick_color[2] + 30, 255),
            )
            border_color = (
                max(brick_color[0] - 30, 0),
                max(brick_color[1] - 30, 0),
                max(brick_color[2] - 30, 0),
            )

            rows = 3
            row_h = inner.height / rows
            gap = 2  # tuğlalar arası harç boşluğu

            def make_brick(row_idx: int, start_r: float, end_r: float):
                """
                start_r, end_r: 0.0–1.0 arası yatay oranlar
                """
                y = int(inner.y + row_idx * row_h + gap / 2)
                h = int(row_h - gap)
                x = int(inner.x + start_r * inner.width + gap / 2)
                w = int((end_r - start_r) * inner.width - gap)

                if w <= 0 or h <= 0:
                    return None

                return pygame.Rect(x, y, w, h)

            def draw_brick(rect: pygame.Rect):
                # gövde
                pygame.draw.rect(s, brick_color, rect)

                # üst highlight bandı
                band_h = max(1, rect.height // 4)
                band_rect = pygame.Rect(rect.x, rect.y, rect.width, band_h)
                pygame.draw.rect(s, highlight, band_rect)

                # brick outline
                pygame.draw.rect(s, border_color, rect, 1)

            # ÜST SATIR: tek uzun tuğla (0.0 → 1.0)
            top_brick = make_brick(0, 0.0, 1.0)
            if top_brick:
                draw_brick(top_brick)

            # ORTA SATIR: 1 | 23  → [küçük][uzun]
            mid_left = make_brick(1, 0.0, 1.0 / 3.0)
            mid_right = make_brick(1, 1.0 / 3.0, 1.0)
            for b in (mid_left, mid_right):
                if b:
                    draw_brick(b)

            # ALT SATIR: 12 | 3  → [uzun][küçük]
            bot_left = make_brick(2, 0.0, 2.0 / 3.0)
            bot_right = make_brick(2, 2.0 / 3.0, 1.0)
            for b in (bot_left, bot_right):
                if b:
                    draw_brick(b)

            # Genel outline
            pygame.draw.rect(s, (0, 0, 0), inner, 1)
            return

        # Fallback
        inner = outer.inflate(-8, -8)
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
