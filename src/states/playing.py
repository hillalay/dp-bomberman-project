# src/states/playing.py

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING
from states.game_over import GameOverState
from states.base import GameState
from states.paused import PausedState
from controller.command_mapper import CommandMapper
from controller.command_invoker import CommandInvoker
from model.entities import ExplosionFX, WallType
from model.enemy import Enemy
from model.ai.move_strategies import RandomMoveStrategy

if TYPE_CHECKING:
    from core.game import Game


class PlayingState(GameState):
    def __init__(self, game: Game):
        super().__init__(game)
        self.world = game.world
        self.renderer = game.renderer

        self.command_mapper = CommandMapper()
        self.command_invoker = CommandInvoker()
        self.debug_font = pygame.font.SysFont("Arial", 24, bold=True)

        # snapshot anim yönleri için
        self._prev_pos = {}  # pid -> (x,y)
        self._prev_enemy_pos = []  # index -> (x,y)  (snapshot sırası)

    def enter(self):
        print("[PlayingState] enter")
        self.world = self.game.world
        self.renderer = self.game.renderer
        self.game.sound.stop_music()

    def exit(self):
        print("[PlayingState] exit")
        self.game.sound.stop_music()

    def handle_event(self, event: pygame.event.Event):
        mode = getattr(self.game, "mode", "local")

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.set_state(PausedState(self.game, self))
            return

        # client: input'u server'a yolla
        if mode == "client":
            if self.game.net_proxy is not None:
                self.game.net_proxy.handle_event(event)
            return

        # server: local klavye almaz
        if mode == "server":
            return

        # local (Command pattern)
        cmd = self.command_mapper.map_event(event, self.world)
        if cmd is not None:
            self.command_invoker.execute(cmd)

    def update(self, dt: float):
        mode = getattr(self.game, "mode", "local")

        # ---------------- SERVER ----------------
        if mode == "server" and self.game.server is not None:
            inputs = self.game.server.poll_inputs()

            for pid, msg in inputs:
                print("[Server] got:", pid, msg)
                if msg.get("type") != "INPUT":
                    continue

                action = msg.get("action")
                data = msg.get("data", {})

                p = self.world.players.get(pid)
                if p is None or not getattr(p, "alive", True):
                    continue

                if action == "MOVE":
                    p.move_dir.x = int(data.get("dx", 0))
                    p.move_dir.y = int(data.get("dy", 0))

                elif action in ("STOP_MOVE", "STOP"):
                    axis = data.get("axis")
                    if axis == "x":
                        p.move_dir.x = 0
                    elif axis == "y":
                        p.move_dir.y = 0

                elif action == "BOMB":
                    self.world.place_bomb(p)

            # fizik sadece server'da
            self.world.update(dt)
            alive_players = self.world.alive_player_count()
            remaining_breakable = self.world.breakable_wall_count()

            if remaining_breakable == 0 and alive_players > 0:
                snap = self._make_snapshot()
                snap["win"] = True
                snap["game_over"] = False

                # ✅ 1 kere değil, garanti olsun diye birkaç kere gönder
                for _ in range(5):
                    self.game.server.broadcast({"type": "SNAPSHOT", "data": snap})

                from states.win import WinState
                self.game.set_state(WinState(self.game))
                return

            alive = self.world.alive_player_count()

            if alive == 0:
                # ✅ client'lara son snapshot (game_over=True) gönder
                snap = self._make_snapshot()
                snap["game_over"] = True
                self.game.server.broadcast({"type": "SNAPSHOT", "data": snap})

                from states.game_over import GameOverState
                self.game.set_state(GameOverState(self.game))
                return

            # snapshot her frame
            snap = self._make_snapshot()
            snap["game_over"] = False  # opsiyonel ama netlik iyi
            self.game.server.broadcast({"type": "SNAPSHOT", "data": snap})
            return


        # ---------------- CLIENT ----------------
        if mode == "client" and self.game.client is not None:
            snap = self.game.client.get_snapshot()
            if snap:
                self._apply_snapshot(snap)

                if snap.get("win"):
                    from states.win import WinState
                    self.game.set_state(WinState(self.game))
                    return

                print("[CLIENT] snap win=", snap.get("win"), "game_over=", snap.get("game_over"))
                # DEBUG
                print("[CLIENT] game_over =", snap.get("game_over"))

                if snap.get("game_over"):
                    print("[CLIENT] SWITCHING TO GAME OVER")
                    from states.game_over import GameOverState
                    self.game.set_state(GameOverState(self.game))
                    return
            return





        # ---------------- LOCAL ----------------
        self.world.update(dt)

        alive = self.world.alive_player_count()
        print("[DEBUG] alive_count =", alive)

        # ✅ TEK GAMEOVER KONTROLÜ (local)
        if alive == 0:
            self.game.set_state(GameOverState(self.game))       # ✅ set_state
            return


    def render(self, surface: pygame.Surface):
        # server headless ise render etme
        if getattr(self.game, "mode", "local") == "server":
            return

        self.renderer.draw_world(self.world)

        label = "ESC – Pause"
        text_surf = self.debug_font.render(label, True, (255, 255, 255))
        padding = 8

        bg_rect = text_surf.get_rect(topleft=(16, 16))
        bg_rect.inflate_ip(padding * 2, padding * 2)

        hud = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        hud.fill((0, 0, 0, 130))

        surface.blit(hud, bg_rect.topleft)
        surface.blit(text_surf, (bg_rect.x + padding, bg_rect.y + padding))

    def _make_snapshot(self) -> dict:
        ts = self.world.config.TILE_SIZE

        snap = {
            "players": {
                str(pid): {
                    "x": int(p.rect.x),
                    "y": int(p.rect.y),
                    "alive": bool(getattr(p, "alive", True)),
                    "hp": int(getattr(p, "hp", 0)),
                    # blink için istersen şimdiden ekle:
                    "invincible": bool(getattr(p, "invincible", False)),
                    "inv_timer": float(getattr(p, "inv_timer", 0.0)),
                }
                for pid, p in self.world.players.items()
            },
            "bombs": [
                {"x": int(b.rect.x), "y": int(b.rect.y)}
                for b in getattr(self.world, "bombs", [])
                if not getattr(b, "exploded", False)
            ],
            "enemies": [
                {"x": int(e.rect.x), "y": int(e.rect.y),
                "type": int(getattr(e, "enemy_type", 1))}
                for e in getattr(self.world, "enemies", [])
            ],
            "walls": [
                {
                    "gx": int(w.rect.x // ts),
                    "gy": int(w.rect.y // ts),
                    "type": str(getattr(w, "wall_type", "")),
                    "hp": int(getattr(w, "hp", 1)),
                }
                for w in getattr(self.world, "walls", [])
            ],
            "powerups": [
                {
                    "gx": int(pu.rect.centerx // ts),
                    "gy": int(pu.rect.centery // ts),
                    "kind": getattr(getattr(pu, "kind", None), "name",
                                    str(getattr(pu, "kind", ""))),
                }
                for pu in getattr(self.world, "powerups", [])
            ],
            "score": int(getattr(self.game, "score", 0)),
            "explosions": [
                {"x": int(fx.rect.x), "y": int(fx.rect.y)}
                for fx in getattr(self.world, "explosions_fx", [])
            ],
        }

        # ✅ gameover flag (client bununla state değiştirecek)
        snap["game_over"] = (self.world.alive_player_count() == 0)
        snap.setdefault("game_over", False)
        snap.setdefault("win", False)
        return snap


    

    def _apply_snapshot(self, snap: dict) -> None:
        ts = self.world.config.TILE_SIZE

        # ---------------- PLAYERS ----------------
        for pid_str, pdata in snap.get("players", {}).items():
            pid = int(pid_str)
            p = self.world.players.get(pid)
            if p is None:
                continue

            new_x = int(pdata["x"])
            new_y = int(pdata["y"])

            prev = self._prev_pos.get(pid)
            dx = (new_x - prev[0]) if prev is not None else 0
            dy = (new_y - prev[1]) if prev is not None else 0

            p.rect.x = new_x
            p.rect.y = new_y
            p.alive = bool(pdata.get("alive", True))
            p.hp = int(pdata.get("hp", getattr(p, "hp", 0)))

            p.invincible = bool(pdata.get("invincible", getattr(p, "invincible", False)))
            p.inv_timer = float(pdata.get("inv_timer", getattr(p, "inv_timer", 0.0)))


            # Basit yürüyüş yönü (anim)
            if hasattr(p, "move_dir"):
                if dx == 0 and dy == 0:
                    p.move_dir.x = 0
                    p.move_dir.y = 0
                else:
                    if abs(dx) >= abs(dy):
                        p.move_dir.x = 1 if dx > 0 else -1
                        p.move_dir.y = 0
                    else:
                        p.move_dir.x = 0
                        p.move_dir.y = 1 if dy > 0 else -1

            if hasattr(p, "moving"):
                p.moving = (dx != 0 or dy != 0)

            self._prev_pos[pid] = (new_x, new_y)

        # ---------------- WALLS ----------------
        def _parse_wall_type(s: str) -> WallType:
            s = (s or "").upper()
            if "UNBREAKABLE" in s:
                return WallType.UNBREAKABLE
            if "HARD" in s:
                return WallType.HARD
            return WallType.BREAKABLE

        if not hasattr(self.world, "_net_wall_map"):
            self.world._net_wall_map = {}  # (gx,gy) -> Wall

        wall_map = self.world._net_wall_map
        new_keys = set()

        for w in snap.get("walls", []):
            gx = int(w["gx"])
            gy = int(w["gy"])
            wt = _parse_wall_type(w.get("type", ""))

            key = (gx, gy)
            new_keys.add(key)

            obj = wall_map.get(key)
            if obj is None or getattr(obj, "wall_type", None) != wt:
                obj = self.world.factory.create(
                    "wall", x=gx, y=gy, wall_type=wt)
                wall_map[key] = obj

            if hasattr(obj, "hp"):
                obj.hp = int(w.get("hp", getattr(obj, "hp", 1)))

        for key in list(wall_map.keys()):
            if key not in new_keys:
                del wall_map[key]

        self.world.walls = list(wall_map.values())

        # ---------------- ENEMIES (KRİTİK DÜZELTME) ----------------
        enemies_data = snap.get("enemies", [])

        # İlk kez: client world'deki mevcut enemy objelerini baz al (varsa)
        if not hasattr(self.world, "_net_enemy_objs"):
            self.world._net_enemy_objs = list(
                getattr(self.world, "enemies", []))

        objs: list[Enemy] = self.world._net_enemy_objs

        # obj sayısını snapshot'a eşitle
        while len(objs) < len(enemies_data):
            objs.append(
                Enemy(0, 0, ts, strategy=RandomMoveStrategy(), enemy_type=1))
        if len(objs) > len(enemies_data):
            del objs[len(enemies_data):]

        # prev listesi eşitle
        if len(self._prev_enemy_pos) < len(enemies_data):
            self._prev_enemy_pos.extend(
                [None] * (len(enemies_data) - len(self._prev_enemy_pos)))
        if len(self._prev_enemy_pos) > len(enemies_data):
            self._prev_enemy_pos = self._prev_enemy_pos[:len(enemies_data)]

        for i, ed in enumerate(enemies_data):
            obj = objs[i]

            new_x = int(ed["x"])
            new_y = int(ed["y"])
            etype = int(ed.get("type", 1))

            prev = self._prev_enemy_pos[i]
            dx = (new_x - prev[0]) if prev is not None else 0
            dy = (new_y - prev[1]) if prev is not None else 0

            obj.rect.x = new_x
            obj.rect.y = new_y
            obj.enemy_type = etype

            # anim yönü için (Enemy.draw -> _moving + _last_dir kullanıyor)
            moving = (dx != 0 or dy != 0)
            obj._moving = moving  # Enemy sınıfındaki internal flag

            if moving:
                if abs(dx) >= abs(dy):
                    obj._last_dir = (1, 0) if dx > 0 else (-1, 0)
                else:
                    obj._last_dir = (0, 1) if dy > 0 else (0, -1)

            # olası “yarım step” görsel hatasını engelle
            obj._target_px = obj.rect.topleft

            self._prev_enemy_pos[i] = (new_x, new_y)

        # Renderer artık gerçek objeleri çizecek
        self.world.enemies = objs

        # ---------------- NET LISTS ----------------
        self.world._net_bombs = snap.get("bombs", [])
        self.world._net_powerups = snap.get("powerups", [])
        self.game.score = int(
            snap.get("score", getattr(self.game, "score", 0)))

        # debug amaçlı tutmak istersen:
        self.world._net_enemies = enemies_data

        # ---------------- EXPLOSIONS FX ----------------
        if not hasattr(self.world, "_net_expl_seen"):
            self.world._net_expl_seen = set()

        # ölü fx'leri temizle
        self.world.explosions_fx = [
            fx for fx in self.world.explosions_fx if fx.alive()]

        alive_keys = {(fx.rect.x, fx.rect.y)
                      for fx in self.world.explosions_fx}
        self.world._net_expl_seen = set(alive_keys)

        for e in snap.get("explosions", []):
            x = int(e["x"])
            y = int(e["y"])
            key = (x, y)
            if key in self.world._net_expl_seen:
                continue
            self.world.explosions_fx.append(ExplosionFX(x, y, ts))
            self.world._net_expl_seen.add(key)

        

