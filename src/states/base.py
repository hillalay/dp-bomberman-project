# src/states/base.py

from __future__ import annotations
from abc import ABC, abstractmethod
import pygame

# Tip döngüsünü kırmak için runtime import yok, ama union type artık normal kullanılabilir
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.game import Game


class GameState(ABC):
    """
    State Pattern için temel soyut sınıf.
    Tüm state'ler (Menu, Playing, Paused...) burayı miras alır.
    """

    def __init__(self, game: Game):
        self.game = game

    # ---------------------- LIFECYCLE ----------------------

    def enter(self):
        """State'e girildiğinde bir kere çalışır."""
        pass

    def exit(self):
        """State'den çıkılırken bir kere çalışır."""
        pass

    # ---------------------- EVENT --------------------------

    def handle_event(self, event: pygame.event.Event):
        """Alt sınıflar override edecek."""
        pass

    # ---------------------- UPDATE -------------------------

    @abstractmethod
    def update(self, dt: float):
        """Her state kendi mantığını burada çalıştırır."""
        ...

    # ---------------------- RENDER -------------------------

    @abstractmethod
    def render(self, surface: pygame.Surface):
        """Her state kendi çizimini burada yapar."""
        ...
