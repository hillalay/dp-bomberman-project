import random
from factory.entity_factory import EntityFactory
from model.entities import WallType
from factory.powerup_factory import PowerUpFactory


class World:
    def __init__(self, config):
        self.config = config
        self.factory = EntityFactory(config)

        # Oyuncu başlangıç tile'ı
        self.player = self.factory.create("player", x=1, y=1)

        self.walls = []
        self.bombs = []

        self.powerups=[]
        self.powerup_factory = PowerUpFactory(config)


        self._build_level()

    def _build_level(self):
        gw, gh = self.config.GRID_WIDTH, self.config.GRID_HEIGHT

        # -------------------------
        # 1) Kenar: UNBREAKABLE walls
        # -------------------------
        for x in range(gw):
            self.walls.append(
                self.factory.create(
                    "wall",
                    x=x,
                    y=0,
                    wall_type=WallType.UNBREAKABLE,
                )
            )
            self.walls.append(
                self.factory.create(
                    "wall",
                    x=x,
                    y=gh - 1,
                    wall_type=WallType.UNBREAKABLE,
                )
            )

        for y in range(gh):
            self.walls.append(
                self.factory.create(
                    "wall",
                    x=0,
                    y=y,
                    wall_type=WallType.UNBREAKABLE,
                )
            )
            self.walls.append(
                self.factory.create(
                    "wall",
                    x=gw - 1,
                    y=y,
                    wall_type=WallType.UNBREAKABLE,
                )
            )

        # -------------------------
        # 2) İçerideki HARD walls
        #    Satranç tahtası gibi 2x2 aralıklarla
        # -------------------------
        for x in range(2, gw - 2, 2):
            for y in range(2, gh - 2, 2):
                self.walls.append(
                    self.factory.create(
                        "wall",
                        x=x,
                        y=y,
                        wall_type=WallType.HARD,
                    )
                )

        # -------------------------
        # 3) Aralara BREAKABLE walls (rastgele)
        # -------------------------
        random.seed(0)  # deterministik olsun, her çalıştırmada aynı map gelsin

        for x in range(1, gw - 1):
            for y in range(1, gh - 1):

                # Oyuncunun spawn çevresini boş bırak
                if (x, y) in [(1, 1), (1, 2), (2, 1)]:
                    continue

                # Bu tile'da zaten bir UNBREAKABLE/HARD var mı?
                occupied = any(
                    (w.rect.x // self.config.TILE_SIZE == x)
                    and (w.rect.y // self.config.TILE_SIZE == y)
                    for w in self.walls
                )
                if occupied:
                    continue

                # %45 ihtimalle kırılabilir duvar koy
                if random.random() < 0.45:
                    self.walls.append(
                        self.factory.create(
                            "wall",
                            x=x,
                            y=y,
                            wall_type=WallType.BREAKABLE,
                        )
                    )

    # -------------------------
    # GAME LOOP API
    # -------------------------

    def update(self, dt):
        self.player.update(dt, self)

        for bomb in list(self.bombs):
            bomb.update(dt, self)

        # Player power-up aldı mı?
        for pu in list(self.powerups):
            if pu.rect.colliderect(self.player.rect):
                pu.apply(self.player)
                self.powerups.remove(pu)

    def draw(self, s):
        # Eğer Renderer kullanmıyorsan, buradan da çizebilirsin.
        # Şu an Renderer.draw_world kullanıyoruz, o yüzden burada bir şey yapmıyoruz.
        pass

    def collides_with_solid(self, rect):
        return any(rect.colliderect(w.rect) for w in self.walls)
    
    def _get_wall_at(self, gx:int, gy:int):
        """
        Verilen grid koordinatında (gx, gy) bir duvar varsa onu döndürür,
        yoksa None döner.
        """
        ts=self.config.TILE_SIZE
        for w in self.walls:
            wx = w.rect.x // ts
            wy = w.rect.y // ts
            if wx == gx and wy == gy:
                return w 
        return None
    


    def place_bomb(self):
        #Önce oyuncunun şu an kaç bombası var,say
        current_bombs = sum(
            1 for b in self.bombs 
            if getattr(b, "owner", None) is self.player)
        max_bombs = getattr(self.player, "max_bombs",self.config.MAX_BOMBS)
        if current_bombs >= max_bombs:
            return  # Maksimum bombaya ulaşıldı, yeni bomba yerleştirilemez
        
        tile_x = self.player.rect.x // self.config.TILE_SIZE
        tile_y = self.player.rect.y // self.config.TILE_SIZE
        bomb = self.factory.create(
            "bomb",
            x=tile_x,
            y=tile_y,
            owner=self.player,
        )
        self.bombs.append(bomb)

    # -------------------------
    # 💣 PATLAMA LOGİĞİ
    # -------------------------
    def handle_explosion(self, bomb, tiles=None):
        """
        - bomb: patlayan bomba objesi
        - tiles: şimdilik sadece görsel/ilerideki kullanım için; burada
                 patlama mantığını kendimiz hesaplayacağız.

        Mantık:
        - Patlama artı şeklinde yayılır (sağ, sol, yukarı, aşağı).
        - Her yönde:
            * UNBREAKABLE görürse: durur, duvar zarar almaz.
            * HARD / BREAKABLE görürse: hasar verir, SONRA durur (arka taraf patlamaz).
        """
        ts = self.config.TILE_SIZE

        # Bombanın grid koordinatı
        gx = bomb.rect.x // ts
        gy = bomb.rect.y // ts

        # Bomba gücü (owner'dan veya config'ten geliyor)
        power = getattr(bomb, "power", 2)

        destroyed_walls = []

        # --- Merkez tile'da duvar varsa önce onu kontrol et ---
        center_wall = self._get_wall_at(gx, gy)
        if center_wall is not None:
            if getattr(center_wall, "wall_type", None) != WallType.UNBREAKABLE:
                if hasattr(center_wall, "take_damage"):
                    if center_wall.take_damage():
                        destroyed_walls.append(center_wall)
                else:
                    # Eski fallback: breakable ise tek seferde kır
                    if getattr(center_wall, "wall_type", None) == WallType.BREAKABLE:
                        destroyed_walls.append(center_wall)

        # --- Dört yöne doğru yayıl ---
        directions = [
            (1, 0),   # sağ
            (-1, 0),  # sol
            (0, -1),  # yukarı
            (0, 1),   # aşağı
        ]

        gw, gh = self.config.GRID_WIDTH, self.config.GRID_HEIGHT

        for dx, dy in directions:
            for step in range(1, power + 1):
                nx = gx + dx * step
                ny = gy + dy * step

                # Harita dışına çıktıysak o yönde dur
                if nx < 0 or ny < 0 or nx >= gw or ny >= gh:
                    break

                wall = self._get_wall_at(nx, ny)
                if wall is None:
                    # Burada istersen ileride player/enemy damage bakarsın
                    continue

                # UNBREAKABLE → patlama buradan öteye geçmesin, duvar da hasar almasın
                if getattr(wall, "wall_type", None) == WallType.UNBREAKABLE:
                    break

                # HARD / BREAKABLE → hasar ver
                if hasattr(wall, "take_damage"):
                    destroyed = wall.take_damage()
                else:
                    # Fallback: sadece BREAKABLE'lar tek seferde kırılsın
                    destroyed = (getattr(wall, "wall_type", None) == WallType.BREAKABLE)

                if destroyed:
                    destroyed_walls.append(wall)

                # Hangi tip olursa olsun (UNBREAKABLE / HARD / BREAKABLE),
                # ilk duvardan SONRA patlama devam ETMEMELİ, o yüzden break
                break

        # --- Duvarları sil + breakable'lardan power-up dene ---
        for wall in destroyed_walls:
            wx = wall.rect.x // ts
            wy = wall.rect.y // ts

            if wall in self.walls:
                self.walls.remove(wall)

            # Sadece BREAKABLE duvarlardan power-up çıksın
            if getattr(wall, "wall_type", None) == WallType.BREAKABLE:
                pu = self.powerup_factory.maybe_spawn(wx, wy)
                if pu is not None:
                    self.powerups.append(pu)

        # --- Bombayı listeden sil ---
        if bomb in self.bombs:
            self.bombs.remove(bomb)

        # İleride: player/enemy damage vs. buraya gelir
