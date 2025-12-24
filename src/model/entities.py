import pygame
import os
from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Tuple, DefaultDict
from collections import defaultdict
from abc import ABC, abstractmethod
from model.player_state import PlayerState, NormalState, SpeedBoostState
from core.event_bus import EventBus, EventType, Event
from core.explosion_strategy import ExplosionStrategy, NormalExplosionStrategy



# ====================================================
# EVENT SYSTEM (Observer / Mediator)
# ====================================================



# ====================================================
# EXPLOSION STRATEGY (Strategy Pattern)
# ====================================================

GridPos = Tuple[int, int]


class ExplosionStrategy(ABC):
    """
    Patlamanın hangi tile'lara yayılacağını hesaplayan arayüz.
    İleride:
      - NormalExplosionStrategy
      - LongRangeExplosion
      - PierceExplosion
    gibi varyantlar buradan türetilebilir.
    """

    @abstractmethod
    def compute_tiles(
        self,
        origin: GridPos,
        power: int,
        grid_width: int,
        grid_height: int,
    ) -> List[GridPos]:
        """
        origin: (gx, gy) bomba tile'ı
        power: kaç tile uzağa kadar
        grid_width / grid_height: tilemap boyutları
        """
        raise NotImplementedError




# ====================================================
# WALL TYPE
# ====================================================

class WallType(Enum):
    UNBREAKABLE = auto()
    BREAKABLE = auto()
    HARD = auto()

class PowerUpType(Enum):
    BOMB_COUNT=auto()
    BOMB_POWER=auto()
    SPEED=auto()



# ====================================================
# BASE ENTITY
# ====================================================

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

        self.max_bombs=1
        self.hp_max=3
        self.hp = 3
        self.alive = True
        self.invuln_time = 0.0  # opsiyonel
        self.invincible = False
        self.inv_timer = 0.0
        self.inv_duration = 0.8  # saniye


        # --- HITBOX KÜÇÜLTME ---
        # Tile 32x32 ise shrink=8 → 24x24 oyuncu
        shrink = 14
        self.rect.inflate_ip(-shrink, -shrink)

        # -----------------------

        #Hız Bomba özellikleri
        self.base_speed = config.PLAYER_SPEED #Temel hız
        self.color=self.config.COLOR_PLAYER

        #Aynı anda kaç bomba koyulur
        self.max_bombs = getattr(config,"MAX_BOMBS",1)

        #Bombanın patlama menzili
        self.bomb_power = getattr(self.config,"BOMB_POWER",2)

        self.moving = False
        self.facing = "f"


        self.move_dir = pygame.Vector2(0, 0)
        self.moving = False
        self.facing="f" # idle bakış yönü default (front)

        # ---- STATE PATTERN ----
        # Player'ın current state'i (NormalState ile başlıyoruz)
        self.state: PlayerState = NormalState(self)
        self.state.enter()

    def change_state(self, new_state: PlayerState):
        """
        State değişimi için tek nokta.
        """
        if self.state is not None:
            self.state.exit()
        self.state = new_state
        self.state.enter()

    def take_damage(self,amount:int=1):
        if self.invincible:
            return
        if not self.alive:
            return
        if self.invuln_time >0:
            return
        self.hp -=amount
        self.invuln_time =1.0
        print(f"[Player] Damage taken! HP={self.hp}")

        self.invincible = True
        self.inv_timer = self.inv_duration

        if self.hp <= 0:
            self.alive = False
            self.invincible = False
            self.inv_timer = 0.0
            self.invuln_time = 0.0
            print("[Player] DEAD")


    def update(self, dt, world):
        # --- invincibility timer (alive olmasa bile düşsün) ---
        if self.invincible:
            self.inv_timer -= dt
            if self.inv_timer <= 0:
                self.invincible = False

        if self.invuln_time > 0:
            self.invuln_time -= dt
            if self.invuln_time < 0:
                self.invuln_time = 0

        # sonra alive check
        if not self.alive:
            self.moving = False
            self.move_dir.update(0, 0)
            return

        # state update
        if self.state is not None:
            self.state.update(dt)

        # moving flag (anim için)
        self.moving = self.move_dir.length_squared() > 0

        # Hareket
        if self.moving:
            speed = self.state.get_speed() if self.state is not None else self.base_speed
            move = self.move_dir.normalize() * speed * dt

            # 1) X ekseni
            if move.x !=0:
                new_rect = self.rect.move(move.x, 0)
                if not world.collides_with_solid(new_rect):
                    self.rect = new_rect

            # 2) Y ekseni
            if move.y !=0:
                new_rect = self.rect.move(0, move.y)
                if not world.collides_with_solid(new_rect):
                    self.rect = new_rect


    def draw(self, s):
        if not hasattr(self,"moving"):
            self.moving = False
        if self.invincible:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return

        frame = (pygame.time.get_ticks() // 120) % 3 if self.moving else 1
        letter = self._dir_to_letter()
        code = f"p{letter}{frame}"

        img = Player._load_player_sprite(code, (self.rect.width, self.rect.height))
        s.blit(img, self.rect)



    PLAYER_SPRITE_BASE = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "assets", "sprites", "player"
    )

    _PLAYER_SPRITE_CACHE = {}

    @staticmethod
    def _load_player_sprite(code: str, size: tuple[int, int]) -> pygame.Surface:
        key = (code, size)
        if key not in Player._PLAYER_SPRITE_CACHE:
            path = os.path.join(Player.PLAYER_SPRITE_BASE, f"{code}.png")
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            Player._PLAYER_SPRITE_CACHE[key] = img
        return Player._PLAYER_SPRITE_CACHE[key]
    
    def _dir_to_letter(self) -> str:
        dx, dy = float(self.move_dir.x), float(self.move_dir.y)

        # Hareket yoksa son yöne göre bak (yoksa front)
        if dx == 0 and dy == 0:
            return getattr(self, "facing", "f")

        # baskın eksene göre yön seç
        if abs(dx) >= abs(dy):
            self.facing = "r" if dx > 0 else "l"
        else:
            self.facing = "f" if dy > 0 else "b"

        return self.facing







# ----------------------------------------------------
# WALL
# ----------------------------------------------------
class Wall(Entity):
    """
    - UNBREAKABLE + HARD:
        * 3D blok (tema rengine göre)
    - BREAKABLE:
        * Tuğla pattern (üstte tek, ortada 1|23, altta 12|3)
        * Renk tema + wall_type’a göre değişir:
          - forest:
              UNBREAKABLE/HARD → yeşil
              BREAKABLE        → daha koyu yeşil
          - diğer temalar:
              UNBREAKABLE/HARD → koyu gri
              BREAKABLE        → bricky gri
    """

    def __init__(self, x, y, config, wall_type: WallType | None = None, breakable: bool = False):
        super().__init__(x, y, config)

        if wall_type is None:
            wall_type = WallType.BREAKABLE if breakable else WallType.UNBREAKABLE

        self.wall_type = wall_type
        self.invuln_time = 0.0   # <<< KRİTİK SATIR




        #--------HP Sistemı--------

        if self.wall_type == WallType.UNBREAKABLE:
            self.hp = 999999999
        elif self.wall_type == WallType.HARD:
            self.hp = 2
        elif self.wall_type == WallType.BREAKABLE:
            self.hp = 1
        else:
            self.hp = 1


    def take_damage(self,amount:int=1) -> None:
        if self.wall_type ==WallType.UNBREAKABLE:
            return False
        
        if self.invuln_time >0:
            return False
        
        self.hp -=amount
        self.invuln_time=0.6 # 0.6 sn dokunulmazlık (opsiyonel)
        print(f"[Wall] Damage taken! HP={self.hp}")
        return self.hp <= 0


    def _base_color(self):
        theme_name = getattr(self.config, "THEME", "city")

        # -------- FOREST THEME --------
        if theme_name == "forest":
            # Unbreakable + Hard → yeşil
            if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
                return (46, 126, 2)   # #2e7e02
            # Breakable → daha koyu yeşil
            if self.wall_type == WallType.BREAKABLE:
                return (30, 82, 2)

        # -------- DİĞER TEMALAR (CITY vs) --------
        # Unbreakable + Hard → koyu gri beton
        if self.wall_type in (WallType.UNBREAKABLE, WallType.HARD):
            return (112, 112, 112)

        # Breakable → biraz daha bricky gri
        if self.wall_type == WallType.BREAKABLE:
            return (118, 122, 122)  # #767a7a

        return (255, 0, 255)
    
    def update(self, dt, world):
        if self.invuln_time > 0:
            self.invuln_time = max(0.0, self.invuln_time - dt)


    def draw(self, s):
        base = self._base_color()
        outer = self.rect

        tile_size = self.config.TILE_SIZE
        gw, gh = self.config.GRID_WIDTH, self.config.GRID_HEIGHT
        tx = self.rect.x // tile_size
        ty = self.rect.y // tile_size
        is_border = (tx == 0 or tx == gw - 1 or ty == 0 or ty == gh - 1)

        # -------------------------------------------------
        # UNBREAKABLE / HARD → 3D blok
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
        # BREAKABLE → tuğla pattern
        # -------------------------------------------------
        if self.wall_type == WallType.BREAKABLE:
            inner = outer  # full tile

            # Harç arka planı
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
            gap = 2  # tuğlalar arası boşluk

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
                pygame.draw.rect(s, brick_color, rect)

                band_h = max(1, rect.height // 4)
                band_rect = pygame.Rect(rect.x, rect.y, rect.width, band_h)
                pygame.draw.rect(s, highlight, band_rect)

                pygame.draw.rect(s, border_color, rect, 1)

            # ÜST SATIR: tek uzun tuğla
            top_brick = make_brick(0, 0.0, 1.0)
            if top_brick:
                draw_brick(top_brick)

            # ORTA: 1 | 23
            mid_left = make_brick(1, 0.0, 1.0 / 3.0)
            mid_right = make_brick(1, 1.0 / 3.0, 1.0)
            for b in (mid_left, mid_right):
                if b:
                    draw_brick(b)

            # ALT: 12 | 3
            bot_left = make_brick(2, 0.0, 2.0 / 3.0)
            bot_right = make_brick(2, 2.0 / 3.0, 1.0)
            for b in (bot_left, bot_right):
                if b:
                    draw_brick(b)

            pygame.draw.rect(s, (0, 0, 0), inner, 1)
            return

        # Fallback
        inner = outer.inflate(-8, -8)
        pygame.draw.rect(s, base, inner)
        pygame.draw.rect(s, (40, 40, 40), inner, 2)


# --- BOMB ---------------------------------------------------------
class Bomb(Entity):
    """
    - Zamanlayıcı dolunca patlar.
    - Patlama alanını ExplosionStrategy (Strategy Pattern) ile hesaplar.
    - Patlayınca world.handle_explosion'a tiles listesini yollar.
    - EventBus ile BOMB_PLACED / BOMB_EXPLODED event'leri yayınlar (Observer).
    """

    ASSET_BASE = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "assets", "sprites", "bomb"
    )

    _BOMB_CACHE = {}

    def __init__(self, x, y, owner, config):
        super().__init__(x, y, config)
        self.placed_ms = pygame.time.get_ticks()
        self.owner = owner
        self.timer = config.BOMB_TIMER  # dt saniye ise bu da saniye
        self.color = self.config.COLOR_BOMB
        self.explosion_strategy: ExplosionStrategy = NormalExplosionStrategy()


        # --- Bomba menzili ---
        # Owner'ın bomb_power özelliği varsa onu kullan, yoksa config'deki default'u al.
        base_power = getattr(self.config, "BOMB_POWER", 2)
        owner_power = getattr(self.owner, "bomb_power", base_power)
        self.power = owner_power

        # Strategy Pattern: Patlama alanını hesaplayan strateji
        self.explosion_strategy: ExplosionStrategy = NormalExplosionStrategy()

        # Bir kere patlasın diye flag
        self.exploded = False

        # Grid pozisyonu
        tile_size = self.config.TILE_SIZE
        gx = self.rect.x // tile_size
        gy = self.rect.y // tile_size

        # --- Observer Pattern: BOMB_PLACED event'i yayınla ---
        try:
            EventBus.publish(
                Event(
                    type=EventType.BOMB_PLACED,
                    payload={
                        "grid_pos": (gx, gy),
                        "owner": self.owner,
                    },
                )
            )
        except Exception as e:
            print("[ERROR] BOMB_PLACED event sırasında hata:", repr(e))

    def update(self, dt, world):
        # Zaten patladıysa bir daha hiçbir şey yapma
        if self.exploded:
            return

        self.timer -= dt
        if self.timer <= 0:
            self.explode(world)

    def explode(self, world):
        # Güvenlik: iki kere çağrılırsa ignore et
        if self.exploded:
            return
        self.exploded = True

        print("BOOM!")

        tile_size = self.config.TILE_SIZE
        gx = self.rect.x // tile_size
        gy = self.rect.y // tile_size

        # Default: sadece merkez tile
        tiles = [(gx, gy)]

        # --- Strategy Pattern: patlama alanını hesapla ---
        tiles = self.explosion_strategy.compute_tiles(
            origin=(gx, gy),
            power=self.power,
            is_blocking=lambda pos: world.is_blocking(pos),
            is_breakable=lambda pos: world.is_breakable(pos),
)



        # 🔥 Asıl kritik: patlayan tile'ları world'e yolla
        try:
            world.handle_explosion(bomb=self, tiles=tiles)
        except Exception as e:
            print("[ERROR] world.handle_explosion sırasında hata:", repr(e))

        # --- Observer Pattern: BOMB_EXPLODED event'i yayınla ---
        try:
            EventBus.publish(
                Event(
                    type=EventType.BOMB_EXPLODED,
                    payload={
                        "grid_pos": (gx, gy),
                        "tiles": tiles,
                        "owner": self.owner,
                    },
                )
            )
        except Exception as e:
            print("[ERROR] BOMB_EXPLODED event sırasında hata:", repr(e))

    @staticmethod
    def _load_bomb(frame, size):
        key = (frame, size)
        if key not in Bomb._BOMB_CACHE:
            path = os.path.join(Bomb.ASSET_BASE, f"bomb_{frame}.png")
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            Bomb._BOMB_CACHE[key] = img
        return Bomb._BOMB_CACHE[key]


    def draw(self, s):
        elapsed = pygame.time.get_ticks() - self.placed_ms
        frame = (elapsed // 150) % 3
        img = Bomb._load_bomb(frame, (self.rect.width, self.rect.height))
        s.blit(img, self.rect)


class ExplosionFX:
    EXP_BASE = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "assets", "sprites", "explosion"
    )
    _CACHE = {}

    def __init__(self, x_px: int, y_px: int, size: int, duration: float = 0.35):
        self.rect = pygame.Rect(x_px, y_px, size, size)
        self.start_ms = pygame.time.get_ticks()
        self.duration_ms = int(duration * 1000)

    @staticmethod
    def _load(code: str, size: tuple[int, int]) -> pygame.Surface:
        key = (code, size)
        if key not in ExplosionFX._CACHE:
            path = os.path.join(ExplosionFX.EXP_BASE, f"{code}.png")
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            ExplosionFX._CACHE[key] = img
        return ExplosionFX._CACHE[key]

    def alive(self) -> bool:
        return (pygame.time.get_ticks() - self.start_ms) < self.duration_ms

    def draw(self, s: pygame.Surface):
        elapsed = pygame.time.get_ticks() - self.start_ms
        frame = (elapsed // 80) % 3   # 80ms/frame => hızlı patlama hissi
        code = f"ex{frame}"
        img = ExplosionFX._load(code, (self.rect.w, self.rect.h))
        s.blit(img, self.rect)

# --- POWERUP ------------------------------------------------------
class PowerUp(Entity):
    """
    Kırılan duvarlardan çıkan power-up:
    - kind: PowerUpType
    Player üzerinden geçerse apply() çağrılır.
    Burada State Pattern (SpeedBoostState) ile de entegre.
    """

    def __init__(self, x, y, config, kind: PowerUpType):
        super().__init__(x, y, config)
        self.kind = kind

        # Görsel olarak biraz küçük dursun
        shrink = self.config.TILE_SIZE // 3
        self.rect.inflate_ip(-shrink, -shrink)

        # Renkleri türüne göre farklı yapalım
        if self.kind == PowerUpType.BOMB_COUNT:
            self.color = (80, 200, 255)   # mavi
        elif self.kind == PowerUpType.BOMB_POWER:
            self.color = (255, 180, 80)   # turuncu
        elif self.kind == PowerUpType.SPEED:
            self.color = (150, 255, 150)  # yeşilimsi
        else:
            self.color = (255, 255, 255)

    def apply(self, player: Player):
        """
        Power-up player'a uygulanır.
        Şimdilik etkiler kalıcı.
        Burada doğrudan Player'ı güncelliyoruz, istersen EventBus ile POWERUP_PICKED
        event'i de yayınlayıp ses / skor sistemine haber verebilirsin.
        """
        if self.kind == PowerUpType.BOMB_COUNT:
            # Max bomba sayısını 1 arttır
            current = getattr(player, "max_bombs", 1)
            player.max_bombs = current + 1
            print("[PowerUp] Bomb count increased:", player.max_bombs)

        elif self.kind == PowerUpType.BOMB_POWER:
            current = getattr(player, "bomb_power", 2)
            player.bomb_power = current + 1
            print("[PowerUp] Bomb power increased:", player.bomb_power)

        elif self.kind == PowerUpType.SPEED:
            # State Pattern: SpeedBoostState'e geç
            from model.player_state import SpeedBoostState
            player.change_state(SpeedBoostState(player))
            print("[PowerUp] Speed state changed -> SpeedBoostState")

      
        # Eğer EventType'a POWERUP_PICKED eklediysen açabilirsin:
        try:
             EventBus.publish(
                 Event(
                     type=EventType.POWERUP_PICKED,
                     payload={"kind": self.kind, "player": player},
                 )
             )
        except Exception as e:
             print("[ERROR] POWERUP_PICKED event sırasında hata:", repr(e))

    def draw(self, s):
        scale=float(getattr(self.config,"POWERUP_DRAW_SCALE",0.45))
        ts=self.config.TILE_SIZE
        size=max(8,int(ts*scale))
        
        r=pygame.Rect(0,0,size,size)
        r.center=self.rect.center
        pygame.draw.rect(s, self.color, r)
        
