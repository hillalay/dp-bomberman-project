from __future__ import annotations
import pygame
from net.client import GameClient


class NetworkInputProxy:
    def __init__(self, client: GameClient):
        self.client = client

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.client.send_input("MOVE", {"dx": 0, "dy": -1})
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.client.send_input("MOVE", {"dx": 0, "dy": 1})
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self.client.send_input("MOVE", {"dx": -1, "dy": 0})
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.client.send_input("MOVE", {"dx": 1, "dy": 0})
            elif event.key == pygame.K_SPACE:
                self.client.send_input("BOMB", {})

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                self.client.send_input("STOP_MOVE", {"axis": "y"})
            elif event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                self.client.send_input("STOP_MOVE", {"axis": "x"})
                
                
        