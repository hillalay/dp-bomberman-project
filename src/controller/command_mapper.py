import pygame
from typing import Optional

from commands.base import Command
from commands.move import MoveCommand, StopMoveCommand
from commands.bomb import PlaceBombCommand


class CommandMapper:
    def map_event(self, event: pygame.event.Event, world) -> Optional[Command]:

        if hasattr(world,"players") and world.players:
            p1=world.players[1]
            p2=world.players[2]

        else:
            p1=world.player
            p2=None

        if event.type == pygame.KEYDOWN:

            #P1
            if event.key in (pygame.K_w,):
                return MoveCommand(p1, 0, -1)
            if event.key in (pygame.K_s,):
                return MoveCommand(p1, 0, 1)
            if event.key in (pygame.K_a,):
                return MoveCommand(p1, -1, 0)
            if event.key in (pygame.K_d,):
                return MoveCommand(p1, 1, 0)
            if event.key == pygame.K_SPACE:
                return PlaceBombCommand(world,p1)

            #P2
            if event.key ==pygame.K_UP:
                return MoveCommand(p2, 0, -1)
            if event.key ==pygame.K_DOWN:
                return MoveCommand(p2, 0, 1)
            if event.key ==pygame.K_LEFT:
                return MoveCommand(p2, -1, 0)
            if event.key ==pygame.K_RIGHT:
                return MoveCommand(p2, 1, 0)
            if event.key == pygame.K_RCTRL:
                return PlaceBombCommand(world,p2)
            
        if event.type == pygame.KEYUP:
            #P1 stop
            if event.key in (pygame.K_w, pygame.K_s):
                return StopMoveCommand(p1, "y")
            if event.key in (pygame.K_a,pygame.K_d):
                return StopMoveCommand(p1, "x")
            
            #P2 stop
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                return StopMoveCommand(p2, "y")
            if event.key in (pygame.K_LEFT,pygame.K_RIGHT):
                return StopMoveCommand(p2, "x")
            

        return None
