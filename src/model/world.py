# src/model/world.py
import random
from factory.entity_factory import EntityFactory
from model.entities import WallType


class World:
    def __init__(self, config):
        self.config = config
        self.factory = EntityFactory(config)

        # Oyuncu başlangıç tile'ı
        self.player = self.factory.create("player", x=1, y=1)

        self.walls = []
        self.bombs = []

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
        # 2) İçerideki HARD walls (bombermandaki gri bloklar gibi)
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

    def draw(self, s):
        # Eğer Renderer kullanmıyorsan, buradan da çizebilirsin.
        # Şu an Renderer.draw_world kullanıyoruz, o yüzden burada bir şey yapmıyoruz.
        pass

    def collides_with_solid(self, rect):
        return any(rect.colliderect(w.rect) for w in self.walls)

    def place_bomb(self):
        tile_x = self.player.rect.x // self.config.TILE_SIZE
        tile_y = self.player.rect.y // self.config.TILE_SIZE
        bomb = self.factory.create(
            "bomb",
            x=tile_x,
            y=tile_y,
            owner=self.player,
        )
        self.bombs.append(bomb)

        def handle_explosion(self, bomb, tiles=None):
            """
            - bomb: patlayan bomba objesi
            - tiles: patlamadan etkilenen grid koordinatları [(gx, gy), ...]
            """
            ts = self.config.TILE_SIZE

            # tiles gelmediyse fallback: sadece bombanın olduğu tile
            if tiles is None:
                gx = bomb.rect.x // ts
                gy = bomb.rect.y // ts
                tiles = [(gx, gy)]

            # 1) BREAKABLE duvarları bul
            destroyed_walls = []

            for wall in list(self.walls):  # kopya üzerinden dön, silerken patlamasın
                # sadece kırılabilir duvarlar
                if getattr(wall, "wall_type", None) != WallType.BREAKABLE:
                    continue

                wx = wall.rect.x // ts
                wy = wall.rect.y // ts

                if (wx, wy) in tiles:
                    destroyed_walls.append(wall)

            # 2) Bulduğumuz duvarları dünyadan sil
            for wall in destroyed_walls:
                if wall in self.walls:
                    self.walls.remove(wall)

            # 3) Bombayı bombs listesinden sil
            if bomb in self.bombs:
                self.bombs.remove(bomb)

            # İleride: player/enemy damage vs. buraya gelir
