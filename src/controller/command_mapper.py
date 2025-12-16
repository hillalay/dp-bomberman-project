import pygame
from typing import Optional

from commands.base import Command
from commands.move import MoveCommand, StopMoveCommand
from commands.bomb import PlaceBombCommand


class CommandMapper:
    def map_event(self, event: pygame.event.Event, world) -> Optional[Command]:
        player = world.player

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                return MoveCommand(player, 0, -1)
            if event.key in (pygame.K_s, pygame.K_DOWN):
                return MoveCommand(player, 0, 1)
            if event.key in (pygame.K_a, pygame.K_LEFT):
                return MoveCommand(player, -1, 0)
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                return MoveCommand(player, 1, 0)
            if event.key == pygame.K_SPACE:
                return PlaceBombCommand(world)

        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                return StopMoveCommand(player, "y")
            if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                return StopMoveCommand(player, "x")

        return None
