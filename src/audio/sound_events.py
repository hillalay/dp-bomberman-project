# src/audio/sound_events.py

from __future__ import annotations

from typing import TYPE_CHECKING
from model.entities import EventBus, EventType, Event
from audio.sound_manager import SoundManager
from core.event_bus import EventBus, EventType, Event

if TYPE_CHECKING:
    from core.game import Game


class SoundEventListener:
    """
    EventBus'tan gelen oyun olaylarını dinler ve uygun SFX'i çalar.
    - BOMB_PLACED   → bomb_place
    - BOMB_EXPLODED → explosion
    Gelecekte:
    - POWERUP_PICKED → powerup (istersen ekleriz)
    """

    def __init__(self, sound: SoundManager):
        self.sound = sound

        # Observer Pattern: EventBus'a abone ol
        EventBus.subscribe(EventType.BOMB_PLACED, self.on_bomb_placed)
        EventBus.subscribe(EventType.BOMB_EXPLODED, self.on_bomb_exploded)
        EventBus.subscribe(EventType.POWERUP_PICKED,self.on_powerup_picked)  

        # Eğer ileride POWERUP_PICKED eklersen:
        # EventBus.subscribe(EventType.POWERUP_PICKED, self.on_powerup_picked)

        print("[SoundEventListener] subscribed to bomb events")

    # ------------- Event Handlers -------------

    def on_bomb_placed(self, event: Event) -> None:
        """
        Bomba yerleştirildiğinde çağrılır.
        Event payload içinde 'grid_pos', 'owner' vs. olabilir;
        burada sadece sesi çalıyoruz.
        """
        # Debug istersen:
        # print("[SoundEventListener] BOMB_PLACED:", event.payload)
        self.sound.play_sfx("bomb_place")

    def on_bomb_exploded(self, event: Event) -> None:
        """
        Bomba patladığında çağrılır.
        """
        # print("[SoundEventListener] BOMB_EXPLODED:", event.payload)
        self.sound.play_sfx("explosion")

    # Eğer POWERUP_PICKED event'i eklersen:
    def on_powerup_picked(self, event: Event):
        self.sound.play_sfx("powerup")

    def dispose(self) -> None:
        """
        Oyun kapanırken aboneliği iptal etmek istersen kullanabilirsin.
        (Şart değil ama pattern açısından tam olsun diye var.)
        """
        EventBus.unsubscribe(EventType.BOMB_PLACED, self.on_bomb_placed)
        EventBus.unsubscribe(EventType.BOMB_EXPLODED, self.on_bomb_exploded)
        # POWERUP_PICKED için de ekleyebilirsin
