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
        self.players={}
        self.players[1] = self.factory.create("player", x=1, y=1)
        self.players[2]=self.factory.create("player",x=2,y=1)

        self.player=self.players[1]  # tek oyunculu için

        self.walls = []
        self.bombs = []

        self.powerups=[]
        self.powerup_factory = PowerUpFactory(config)

        self.enemies = []

        self.explosions_fx = []

        self._build_level()
        ts = self.config.TILE_SIZE
        

        # Enemy spawn noktaları (grid koordinatı)
        enemy_spawns = [
            (self.config.GRID_WIDTH - 2, self.config.GRID_HEIGHT - 2),
            (self.config.GRID_WIDTH - 3, self.config.GRID_HEIGHT - 2),
        ]
        self._clear_enemy_spawn_area(enemy_spawns)

         # Enemy'leri oluştur ve listeye ekle

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
        for p in self.players.values():
            p.update(dt, self)

        for e in self.enemies:
            e.update(dt, self)
            for p in self.players.values():
                if e.rect.colliderect(p.rect):
                    p.take_damage(1)


        for bomb in list(self.bombs):
            bomb.update(dt, self)

        # explosion FX cleanup
        self.explosions_fx = [fx for fx in self.explosions_fx if fx.alive()]


        for pu in list(self.powerups):
            for p in self.players.values():
                if pu.rect.colliderect(p.rect):
                    pu.apply(p)
                    if hasattr(self.config,"game"):
                        self.config.game.score +=5
                        self.powerups.remove(pu)
                        break


    def draw(self, s):
        moving = getattr(self, "moving", False)
        frame = (pygame.time.get_ticks() // 120) % 3 if moving else 1

        # Eğer Renderer kullanmıyorsan, buradan da çizebilirsin.
        # Şu an Renderer.draw_world kullanıyoruz, o yüzden burada bir şey yapmıyoruz.


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
    


    def place_bomb(self, owner):
        if owner is None or not getattr(owner, "alive", True):
            return  # ölü oyuncu bombalayamaz
    # Owner'a ait aktif bombalar
        active = sum(
            1 for b in self.bombs
            if not b.exploded and b.owner is owner
            )
        if active >= owner.max_bombs:
            return  # limit dolu

        tile_x = owner.rect.centerx // self.config.TILE_SIZE
        tile_y = owner.rect.centery // self.config.TILE_SIZE
        
        bomb = self.factory.create(
            "bomb",
            x=tile_x,
            y=tile_y,
            owner=owner,
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

        # tiles None gelirse patlamasın
            tiles_list = list(tiles) if tiles else []

            blast_tiles = set(tiles_list)
            blast_tiles.add((gx, gy))

            # FX: sadece blast_tiles üzerinden bas
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
                    max_pu=int(getattr(self.config,"MAX_POWERUPS_ON_MAP",9999))
                    if len(self.powerups) < max_pu:
                        pu=self.powerup_factory.maybe_spawn(wx, wy)
                        if pu is not None:
                            self.powerups.append(pu)
                            
            # --- Bombayı listeden sil ---
            if bomb in self.bombs:
                self.bombs.remove(bomb)


    # -------------------------
    # 💀 ENEMY HIT CHECK (explosion kills enemies)
    # -------------------------
            ts = self.config.TILE_SIZE

            for e in list(self.enemies):
                ex = e.rect.centerx // ts
                ey = e.rect.centery // ts

                if (ex, ey) in blast_tiles:
                    died = e.take_damage(1) if hasattr(e, "take_damage") else True

                    if died:
                        if e in self.enemies:
                            self.enemies.remove(e)

                        # skor (istersen type'a göre değiştir)
                        if hasattr(self.config, "game"):
                            bonus = 50 if getattr(e, "enemy_type", 1) == 1 else 80
                            self.config.game.score += bonus


    # -------------------------
    # 💥 PLAYER HIT CHECK
    # -------------------------
            ts = self.config.TILE_SIZE

            for p in self.players.values():
                px = p.rect.centerx // ts
                py = p.rect.centery // ts

                if (px, py) in blast_tiles:
                    damage = getattr(self.config, "BOMB_DAMAGE", 1)
                    p.take_damage(damage)
                    
                    if not p.alive:
                        print(f"[World] Player {getattr(p,'id', '?')} killed by explosion!")

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

        if self.collides_with_solid(r):
            return False
        
        for p in self.players.values():
            if r.colliderect(p.rect):
                return False
            
        return True
    
    # world.py içinde (World class)

    def _clear_enemy_spawn_area(self, spawns: list[tuple[int, int]]) -> None:
        offsets = [(0,0), (1,0), (-1,0), (0,1), (0,-1)]
        for sx, sy in spawns:
            for dx, dy in offsets:
                gx, gy = sx + dx, sy + dy
                w = self._get_wall_at(gx, gy)
                if w is None:
                    continue
            # UNBREAKABLE hariç (HARD/BREAKABLE) temizle
                if getattr(w, "wall_type", None) != WallType.UNBREAKABLE:
                    if w in self.walls:
                        self.walls.remove(w)


    def iter_players(self):
        ps = getattr(self, "players", None)
        if ps is None:
            return []
        if isinstance(ps, dict):
            return list(ps.values())
        return list(ps)

    def alive_player_count(self) -> int:
        return sum(1 for p in self.iter_players() if getattr(p, "alive", False))


    def breakable_wall_count(self) -> int:
        return sum(
            1 for w in self.walls
            if getattr(w, "wall_type", None) == WallType.BREAKABLE
        )

    