import random
import pygame
from factory.entity_factory import EntityFactory
from model.entities import WallType
from factory.powerup_factory import PowerUpFactory
from model.enemy import Enemy
from model.ai.move_strategies import RandomMoveStrategy, ChasePlayerStrategy
from model.entities import ExplosionFX



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

        self.enemies = []

        self.explosions_fx = []

        self._build_level()
        ts = self.config.TILE_SIZE
        
        ts = self.config.TILE_SIZE

        # Enemy spawn noktaları (grid koordinatı)
        enemy_spawns = [
            (self.config.GRID_WIDTH - 2, self.config.GRID_HEIGHT - 2),
            (self.config.GRID_WIDTH - 3, self.config.GRID_HEIGHT - 2),
        ]

        self.enemies.append(
            Enemy(
                enemy_spawns[0][0],
                enemy_spawns[0][1],
                ts,
                strategy=RandomMoveStrategy(),
                enemy_type=1
            )
        )

        self.enemies.append(
            Enemy(
                enemy_spawns[1][0],
                enemy_spawns[1][1],
                ts,
                strategy=ChasePlayerStrategy(),
                enemy_type=2
            )
        )


        print("Spawned enemy type:", self.enemies[-1].enemy_type)



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

    def is_blocking(self, pos):
        gx, gy = pos
        if gx < 0 or gy < 0 or gx >= self.config.GRID_WIDTH or gy >= self.config.GRID_HEIGHT:
            return True
        return self.is_solid_cell(gx, gy)

    def is_breakable(self, pos):
        gx, gy = pos
        ts = self.config.TILE_SIZE
        r = pygame.Rect(gx * ts, gy * ts, ts, ts)
        # breakable duvarlarını nasıl tutuyorsan ona göre:
        return any(getattr(w, "breakable", False) and w.rect.colliderect(r) for w in self.walls)



    # -------------------------
    # GAME LOOP API
    # -------------------------

    def update(self, dt):
        self.player.update(dt, self)

        for e in self.enemies:
            e.update(dt, self)
            if e.rect.colliderect(self.player.rect):
                self.player.take_damage(1)


        for bomb in list(self.bombs):
            bomb.update(dt, self)

        # explosion FX cleanup
        self.explosions_fx = [fx for fx in self.explosions_fx if fx.alive()]


        # Player power-up aldı mı?
        for pu in list(self.powerups):
            if pu.rect.colliderect(self.player.rect):
                pu.apply(self.player)
                if hasattr(self.config, "game"):
                    self.config.game.score += 5
                self.powerups.remove(pu)
            if hasattr(self.config, "game"):
                self.config.game.score += 5

         # WIN: kırılabilir duvar kalmadıysa
        breakable_left = any(getattr(w, "wall_type", None) == WallType.BREAKABLE for w in self.walls)
        if not breakable_left and hasattr(self.config, "game"):
                self.config.game.on_win()


    def draw(self, s):
        # Eğer Renderer kullanmıyorsan, buradan da çizebilirsin.
        # Şu an Renderer.draw_world kullanıyoruz, o yüzden burada bir şey yapmıyoruz.
        pass

    def collides_with_solid(self, rect):
        return any(rect.colliderect(w.rect) for w in self.walls)
    
    def is_solid_cell(self, gx: int, gy: int) -> bool:
        ts = self.config.TILE_SIZE
        cell_rect = pygame.Rect(gx * ts, gy * ts, ts, ts)
        return any(cell_rect.colliderect(w.rect) for w in self.walls)


    
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
    # Owner'a ait aktif bombalar
        active = sum(
            1 for b in self.bombs
            if not b.exploded and b.owner is self.player
            )
        if active >= self.player.max_bombs:
            return  # limit dolu

        tile_x = self.player.rect.centerx // self.config.TILE_SIZE
        tile_y = self.player.rect.centery // self.config.TILE_SIZE
        
        bomb = self.factory.create(
            "bomb",
            x=tile_x,
            y=tile_y,
            owner=self.player,
            )
        self.bombs.append(bomb)

    def handle_explosion(self, bomb, tiles=None):
            
            print("[World] handle_explosion called, bomb in bombs:", hasattr(self,"bombs") and (bomb in self.bombs))

            ts = self.config.TILE_SIZE
        # Bombanın grid koordinatı
            gx = bomb.rect.x // ts
            gy = bomb.rect.y // ts

        # Bomba gücü (menzil)
            power = getattr(bomb, "power", 2)

            destroyed_walls = []

        # Patlama alanını SET olarak tut (duvar bloklaması sonrası gerçek alan)
            blast_tiles = set(tiles) if tiles else set()
            blast_tiles.add((gx, gy))  # merkez her zaman etkilenir

            ts = self.config.TILE_SIZE
            for (tx, ty) in blast_tiles:
                self.explosions_fx.append(ExplosionFX(tx * ts, ty * ts, ts))


        # --- Merkez tile'da duvar varsa önce onu kontrol et ---
            center_wall = self._get_wall_at(gx, gy)
            if center_wall is not None:
                if getattr(center_wall, "wall_type", None) != WallType.UNBREAKABLE:
                    if hasattr(center_wall, "take_damage"):
                        if center_wall.take_damage():
                            destroyed_walls.append(center_wall)
                    else:
                        if getattr(center_wall, "wall_type", None) == WallType.BREAKABLE:
                            destroyed_walls.append(center_wall)

        # --- Dört yöne doğru yayıl (duvar bloklama burada) ---
            directions = [
                (1, 0),   # sağ
                (-1, 0),  # sol
                (0, -1),  # yukarı
                (0, 1),   # aşağı
                ]
            
            gw, gh = self.config.GRID_WIDTH, self.config.GRID_HEIGHT

            ts = self.config.TILE_SIZE
            for (tx, ty) in tiles:
                self.explosions_fx.append(ExplosionFX(tx * ts, ty * ts, ts))

            if bomb in self.bombs:
                self.bombs.remove(bomb)

            
            for dx, dy in directions:
                for step in range(1, power + 1):
                    nx = gx + dx * step
                    ny = gy + dy * step

                # Harita dışı
                    if nx < 0 or ny < 0 or nx >= gw or ny >= gh:
                        break

                    wall = self._get_wall_at(nx, ny)

                # Boş tile -> patlama etkiler, devam eder
                    if wall is None:
                        blast_tiles.add((nx, ny))
                        continue

                # Duvarın olduğu tile'a kadar patlama gelir
                    blast_tiles.add((nx, ny))

                # UNBREAKABLE -> hasar yok, bu yönde dur
                    if getattr(wall, "wall_type", None) == WallType.UNBREAKABLE:
                        break

                # HARD / BREAKABLE -> hasar ver (varsa take_damage)
                    if hasattr(wall, "take_damage"):
                        destroyed = wall.take_damage()
                    else:
                        destroyed = (getattr(wall, "wall_type", None) == WallType.BREAKABLE)

                    if destroyed:
                        destroyed_walls.append(wall)

                # Duvar gördükten sonra patlama o yönde devam etmez
                    break
    # --- Duvarları sil + breakable'lardan power-up dene ---
                
            for wall in destroyed_walls:
                wx = wall.rect.x // ts
                wy = wall.rect.y // ts

                if wall in self.walls:
                    self.walls.remove(wall)

            # Sadece BREAKABLE duvarlardan power-up çıksın
                if getattr(wall, "wall_type", None) == WallType.BREAKABLE:
                    if hasattr(self.config, "game"):
                        self.config.game.score += 10
                    pu = self.powerup_factory.maybe_spawn(wx, wy)
                    if pu is not None:
                        self.powerups.append(pu)

            # --- Bombayı listeden sil ---
            if bomb in self.bombs:
                self.bombs.remove(bomb)

    # -------------------------
    # 💥 PLAYER HIT CHECK
    # -------------------------
            ts = self.config.TILE_SIZE
            px = self.player.rect.centerx // ts
            py = self.player.rect.centery // ts

            if (px, py) in blast_tiles:
                damage = getattr(self.config, "BOMB_DAMAGE", 1)
                self.player.take_damage(damage)
                
                if not self.player.alive:
                    print("[World] Player killed by explosion!")

            # --- bomb cleanup (mutlaka) ---
            try:
                if hasattr(self, "bombs") and bomb in self.bombs:
                    self.bombs.remove(bomb)
            except Exception as e:
                print("[ERROR] bomb cleanup:", repr(e))

            # owner bomb sayısını düşürüyorsan (sende varsa)
            try:
                if hasattr(bomb.owner, "active_bombs") and bomb.owner.active_bombs > 0:
                    bomb.owner.active_bombs -= 1
            except Exception:
                pass


    def is_tile_free(self, gx, gy) -> bool:
        ts = self.config.TILE_SIZE
        r = pygame.Rect(gx*ts, gy*ts, ts, ts)
        return (not self.collides_with_solid(r)) and (not r.colliderect(self.player.rect))

   
    