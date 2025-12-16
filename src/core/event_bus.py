# src/core/event_bus.py
from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Dict, List, Any, DefaultDict
from collections import defaultdict


class EventType(Enum):
    BOMB_PLACED = auto()
    BOMB_EXPLODED = auto()
    WALL_DESTROYED = auto()
    POWERUP_PICKED=auto()
    PLAYER_DIED = auto()


@dataclass
class Event:
    type: EventType
    payload: Dict[str, Any] | None = None


Listener = Callable[[Event], None]


class EventBus:
    """
    Basit global event bus.
    - subscribe(event_type, listener)
    - publish(Event)
    """
    _subscribers: DefaultDict[EventType, List[Listener]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: EventType, listener: Listener) -> None:
        cls._subscribers[event_type].append(listener)

    @classmethod
    def unsubscribe(cls, event_type: EventType, listener: Listener) -> None:
        if listener in cls._subscribers[event_type]:
            cls._subscribers[event_type].remove(listener)

    @classmethod
    def publish(cls, event: Event) -> None:
        for listener in list(cls._subscribers.get(event.type, [])):
            listener(event)
