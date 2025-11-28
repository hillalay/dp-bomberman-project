# src/model/player_state.py
from __future__ import annotations


class PlayerState:
    """
    Tüm player durumları için temel state sınıfı.
    """
    def __init__(self, player: "Player"):
        self.player = player

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, dt: float):
        pass

    def get_speed(self) -> float:
        # Varsayılan: base_speed
        return self.player.base_speed


class NormalState(PlayerState):
    """
    Varsayılan state – buff yok.
    """
    pass


class SpeedBoostState(PlayerState):
    """
    Geçici hız artışı sağlayan state.
    """
    def __init__(self, player: "Player", duration: float = 5.0, multiplier: float = 3.0):
        super().__init__(player)
        self.duration = duration
        self.remaining = duration
        self.multiplier = multiplier

    def enter(self):
        print(f"[State] SpeedBoostState enter ({self.duration:.1f}s)")

    def exit(self):
        print("[State] SpeedBoostState exit")

    def update(self, dt: float):
        self.remaining -= dt
        if self.remaining <= 0:
            # Süre bitti → NormalState'e geç
            from model.player_state import NormalState
            self.player.change_state(NormalState(self.player))

    def get_speed(self) -> float:
        return self.player.base_speed * self.multiplier
