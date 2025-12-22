# src/net/snapshot.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple

def rect_xy(entity) -> Tuple[int, int]:
    return int(entity.rect.x), int(entity.rect.y)

def world_to_snapshot(world) -> Dict[str, Any]:
    snap: Dict[str, Any] = {}

    # players: world.players varsa onu kullan
    players = getattr(world, "players", None)
    if players:
        snap["players"] = {
            str(pid): {
                "x": int(p.rect.x),
                "y": int(p.rect.y),
                "alive": bool(getattr(p, "alive", True)),
                "hp": int(getattr(p, "hp", 0)),
            }
            for pid, p in players.items()
        }
    else:
        p = world.player
        snap["players"] = {
            "1": {"x": int(p.rect.x), "y": int(p.rect.y), "alive": bool(p.alive), "hp": int(p.hp)}
        }

    snap["bombs"] = [
        {
            "x": int(b.rect.x),
            "y": int(b.rect.y),
            "timer": float(getattr(b, "timer", 0.0)),
            "exploded": bool(getattr(b, "exploded", False)),
        }
        for b in getattr(world, "bombs", [])
    ]

    snap["enemies"] = [
        {
            "x": int(e.rect.x),
            "y": int(e.rect.y),
            "type": int(getattr(e, "enemy_type", 1)),
        }
        for e in getattr(world, "enemies", [])
    ]

    # walls: tile bazlı yolla (rect.x/ts, rect.y/ts)
    ts = world.config.TILE_SIZE
    snap["walls"] = [
        {
            "gx": int(w.rect.x // ts),
            "gy": int(w.rect.y // ts),
            "type": str(getattr(w, "wall_type", None)),
            "hp": int(getattr(w, "hp", 1)),
        }
        for w in getattr(world, "walls", [])
    ]

    snap["powerups"] = [
        {"x": int(pu.rect.x), "y": int(pu.rect.y)}
        for pu in getattr(world, "powerups", [])
    ]

    snap["score"] = int(getattr(getattr(world.config, "game", None), "score", 0))
    return snap
