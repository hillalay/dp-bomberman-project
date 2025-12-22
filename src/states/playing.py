from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from controller.command_mapper import CommandMapper
from controller.command_invoker import CommandInvoker

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

    def enter(self):
        print("[PlayingState] enter")
        self.world = self.game.world
        self.renderer = self.game.renderer
        self.game.sound.stop_music()

    def exit(self):
        print("[PlayingState] exit")
        self.game.sound.stop_music()

    def handle_event(self, event: pygame.event.Event):
        # client: input'u server'a yolla
        mode = getattr(self.game, "mode", "local")

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from states.paused import PausedState
            self.game.set_state(PausedState(self.game, self))
            return

        if mode == "client":
            if self.game.net_proxy is not None:
                self.game.net_proxy.handle_event(event)
            return

        if mode == "server":
            return  # server local klavye almaz

        # local (eski command pattern)
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

            # gameover kontrolü
            if hasattr(self.world, "players") and all((not p.alive) for p in self.world.players.values()):
                from states.game_over import GameOverState
                self.game.set_state(GameOverState(self.game))
                return

            # snapshot her frame
            snap = self._make_snapshot()
            self.game.server.broadcast({"type": "SNAPSHOT", "data": snap})
            return

        # ---------------- CLIENT ----------------
        if mode == "client" and self.game.client is not None:
            snap = self.game.client.get_snapshot()
            if snap:
                print("[Client] snapshot received:")
                self._apply_snapshot(snap)
            return

        # ---------------- LOCAL ----------------
        self.world.update(dt)

        if hasattr(self.world, "players") and all((not p.alive) for p in self.world.players.values()):
            from states.game_over import GameOverState
            self.game.set_state(GameOverState(self.game))

    def render(self, surface: pygame.Surface):
        # server headless ise render etme (istersen tamamen kapat)
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
        return {
            "players": {
                str(pid): {
                    "x": int(p.rect.x),
                    "y": int(p.rect.y),
                    "alive": bool(getattr(p, "alive", True)),
                    "hp": int(getattr(p, "hp", 0)),
                }
                for pid, p in self.world.players.items()
            },
            "bombs": [
                {"x": int(b.rect.x), "y": int(b.rect.y)}
                for b in getattr(self.world, "bombs", [])
                if not getattr(b, "exploded", False)
            ],
            "enemies": [
                {"x": int(e.rect.x), "y": int(e.rect.y), "type": int(getattr(e, "enemy_type", 1))}
                for e in getattr(self.world, "enemies", [])
            ],
            "walls": [
                {"gx": int(w.rect.x // ts), "gy": int(w.rect.y // ts),
                 "type": str(getattr(w, "wall_type", "")), "hp": int(getattr(w, "hp", 1))}
                for w in getattr(self.world, "walls", [])
            ],
            "powerups": [
                {
                    "x": int(pu.rect.x), 
                    "y": int(pu.rect.y),
                    "kind": str(getattr(pu, "powerup_type", ""))
                    }
                
                for pu in getattr(self.world, "powerups", [])
            ],
            "score": int(getattr(self.game, "score", 0)),
            "explosions": [
                {"x": int(fx.rect.x), "y": int(fx.rect.y)}
                for fx in getattr(self.world, "explosions_fx", [])
                ],

        }
    def _apply_snapshot(self, snap: dict) -> None:
        import pygame
        from model.entities import ExplosionFX, WallType

        ts = self.world.config.TILE_SIZE

        # --- Player animasyonu için önceki pozisyonları tut ---
        if not hasattr(self, "_prev_pos"):
            self._prev_pos = {}  # pid -> (x,y)

        for pid_str, pdata in snap.get("players", {}).items():
            pid = int(pid_str)
            p = self.world.players.get(pid)
            if p is None:
                continue

            new_x = int(pdata["x"])
            new_y = int(pdata["y"])

            prev = self._prev_pos.get(pid)
            dx = 0
            dy = 0
            if prev is not None:
                dx = new_x - prev[0]
                dy = new_y - prev[1]

            p.rect.x = new_x
            p.rect.y = new_y
            p.alive = bool(pdata.get("alive", True))
            p.hp = int(pdata.get("hp", getattr(p, "hp", 0)))

            # Basit yürüyüş yönü
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

        # --- WALLS: snapshot'tan gerçek Wall objelerine map'le ---
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
                obj = self.world.factory.create("wall", x=gx, y=gy, wall_type=wt)
                wall_map[key] = obj

            if hasattr(obj, "hp"):
                obj.hp = int(w.get("hp", getattr(obj, "hp", 1)))

        for key in list(wall_map.keys()):
            if key not in new_keys:
                del wall_map[key]

        self.world.walls = list(wall_map.values())

        # --- Net listeleri ---
        self.world._net_bombs = snap.get("bombs", [])
        self.world._net_enemies = snap.get("enemies", [])
        self.world._net_powerups = snap.get("powerups", [])
        self.game.score = int(snap.get("score", getattr(self.game, "score", 0)))

        # --- Explosions: pixel coords ile FX ---
        if not hasattr(self.world, "_net_expl_seen"):
            self.world._net_expl_seen = set()

        self.world.explosions_fx = [fx for fx in self.world.explosions_fx if fx.alive()]

        alive_keys = {(fx.rect.x, fx.rect.y) for fx in self.world.explosions_fx}
        self.world._net_expl_seen = set(alive_keys)

        for e in snap.get("explosions", []):
            x = int(e["x"])
            y = int(e["y"])
            key = (x, y)
            if key in self.world._net_expl_seen:
                continue
            self.world.explosions_fx.append(ExplosionFX(x, y, ts))
            self.world._net_expl_seen.add(key)
