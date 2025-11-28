import pygame
from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Tuple, DefaultDict
from collections import defaultdict
from abc import ABC, abstractmethod
from model.player_state import PlayerState, NormalState, SpeedBoostState



# ====================================================
# EVENT SYSTEM (Observer / Mediator)
# ====================================================

class EventType(Enum):
    BOMB_PLACED = auto()
    BOMB_EXPLODED = auto()
    WALL_DESTROYED = auto()


@dataclass
class Event:
    type: EventType
    payload: Dict[str, Any] | None = None


Listener = Callable[[Event], None]


class EventBus:
    """
    Basit global EventBus.
    - subscribe(event_type, listener)
    - publish(Event)
    """
    _subscribers: DefaultDict[EventType, List[Listener]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: EventType, listener: Listener) -> None:
        cls._subscribers[event_type].append(listener)

    @classmethod
    def unsubscribe(cls, event_type: EventType, listener: Listener) -> None:
        if listener in cls._subscribers[event_type]:
            cls._subscribers[event_type].remove(listener)

    @classmethod
    def publish(cls, event: Event) -> None:
        for listener in list(cls._subscribers.get(event.type, [])):
            listener(event)


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


class NormalExplosionStrategy(ExplosionStrategy):
    """
    Klasik Bomberman patlaması:
    - Ortadan 4 yöne (sağ, sol, yukarı, aşağı)
    - Şimdilik duvarları dikkate almıyor, sadece map sınırına kadar gidiyor.
      (Duvar kırma / bloklama logic'ini world.handle_explosion içinde
       ya da daha sonra gelişmiş bir strategy içinde ele alırsın.)
    """

    DIRECTIONS: List[GridPos] = [
        (1, 0),   # sağ
        (-1, 0),  # sol
        (0, -1),  # yukarı
        (0, 1),   # aşağı
    ]

    def compute_tiles(
        self,
        origin: GridPos,
        power: int,
        grid_width: int,
        grid_height: int,
    ) -> List[GridPos]:
        gx, gy = origin
        tiles: List[GridPos] = [origin]  # merkez tile her zaman var

        for dx, dy in self.DIRECTIONS:
            for step in range(1, power + 1):
                nx = gx + dx * step
                ny = gy + dy * step

                # Map dışına çıkma
                if nx < 0 or ny < 0 or nx >= grid_width or ny >= grid_height:
                    break

                tiles.append((nx, ny))

        return tiles


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

        # --- HITBOX KÜÇÜLTME ---
        # Tile 32x32 ise shrink=8 → 24x24 oyuncu
        shrink = 8
        self.rect.inflate_ip(-shrink, -shrink)
        # -----------------------

        #Hız Bomba özellikleri
        self.base_speed = config.PLAYER_SPEED #Temel hız
        self.color=self.config.COLOR_PLAYER

        #Aynı anda kaç bomba koyulur
        self.max_bombs = getattr(config,"MAX_BOMBS",1)

        #Bombanın patlama menzili
        self.bomb_power = getattr(self.config,"BOMB_POWER",2)


        self.move_dir = pygame.Vector2(0, 0)

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



    def update(self, dt, world):
        # Önce state'i güncelle (örneğin SpeedBoost süresi azalacak)
        if self.state is not None:
            self.state.update(dt)
        if self.move_dir.length_squared() > 0:
            speed=self.state.get_speed() if self.state is not None else self.base_speed

            move = self.move_dir.normalize() * speed * dt
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

        #--------HP Sistemı--------

        if self.wall_type == WallType.UNBREAKABLE:
            self.hp = 999999999
        elif self.wall_type == WallType.HARD:
            self.hp = 2
        elif self.wall_type == WallType.BREAKABLE:
            self.hp = 1
        else:
            self.hp = 1
    def take_damage(self) -> bool:
        """ True dönerse duvar yok edilir """
        if self.wall_type == WallType.UNBREAKABLE:
            return False
        
        self.hp -= 1
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


# ----------------------------------------------------
# BOMB
# ----------------------------------------------------
class Bomb(Entity):
    """
    - Zamanlayıcı dolunca patlar.
    - Patlama alanını ExplosionStrategy ile hesaplar.
    - Patlayınca world.handle_explosion'a tiles listesini yollar.
    - kill() yok; sprite değiliz, exploded flag ile yönetiyoruz.
    """

    def __init__(self, x, y, owner, config):
        super().__init__(x, y, config)
        self.owner = owner
        self.timer = config.BOMB_TIMER        # dt saniye ise bu da saniye
        self.color = self.config.COLOR_BOMB

        #Bomba menzili:owner.bomb_power varsa onu kullan yoksa configden al
        base_power = getattr(self.config,"BOMB_POWER",2)
        owner_power = getattr(self.owner,"bomb_power",base_power)
        self.power = owner_power


        # Strategy pattern
        self.explosion_strategy: ExplosionStrategy = NormalExplosionStrategy()

        # Bir kere patlasın diye flag
        self.exploded = False

        # Grid pozisyonu
        tile_size = self.config.TILE_SIZE
        gx = self.rect.x // tile_size
        gy = self.rect.y // tile_size

        # Opsiyonel: BOMB_PLACED event
        try:
            EventBus.publish(Event(
                type=EventType.BOMB_PLACED,
                payload={
                    "grid_pos": (gx, gy),
                    "owner": self.owner,
                }
            ))
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

        # Patlama alanını Strategy ile hesapla
        try:
            gw = getattr(self.config, "GRID_WIDTH", 15)
            gh = getattr(self.config, "GRID_HEIGHT", 13)

            tiles = self.explosion_strategy.compute_tiles(
                origin=(gx, gy),
                power=self.power,
                grid_width=gw,
                grid_height=gh,
            )
        except Exception as e:
            print("[ERROR] ExplosionStrategy sırasında hata:", repr(e))

        # 🔥 Asıl kritik: patlayan tile'ları world'e yolla
        try:
            world.handle_explosion(bomb=self, tiles=tiles)
        except Exception as e:
            print("[ERROR] world.handle_explosion sırasında hata:", repr(e))

        # BOMB_EXPLODED event (animasyon vs. için)
        try:
            EventBus.publish(Event(
                type=EventType.BOMB_EXPLODED,
                payload={
                    "grid_pos": (gx, gy),
                    "tiles": tiles,
                    "owner": self.owner,
                }
            ))
        except Exception as e:
            print("[ERROR] BOMB_EXPLODED event sırasında hata:", repr(e))

    def draw(self, s):
        pygame.draw.rect(s, self.color, self.rect)


class PowerUp(Entity):
    """
    Kırılan duvarlardan çıkan power-up:
    - kind: PowerUpType
    Player üzerinden geçerse apply() çağrılır.
    """

    def __init__(self, x, y, config, kind: PowerUpType):
        super().__init__(x, y, config)
        self.kind = kind

        # Görsel olarak biraz küçük dursun
        shrink = self.config.TILE_SIZE // 4
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
            #State pattern:SpeedBoostState'e geç
            from model.player_state import SpeedBoostState
            player.change_state(SpeedBoostState(player))
            print("[PowerUp] Speed state changed ->SpeedBoostState")

    def draw(self, s):
        pygame.draw.rect(s, self.color, self.rect)


