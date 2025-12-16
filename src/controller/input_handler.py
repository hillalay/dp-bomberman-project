"""
DEPRECATED:
Bu sınıf Command Pattern öncesi kontrol akışıydı.
Artık PlayingState -> CommandMapper -> CommandInvoker -> Command üzerinden input işlenir.
Rapor amacıyla korunmuştur.



import pygame


class InputHandler:
    def handle_event(self, event, world):
        player = world.player

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                player.move_dir.y = -1
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                player.move_dir.y = 1
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                player.move_dir.x = -1
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                player.move_dir.x = 1
            elif event.key == pygame.K_SPACE:
                world.place_bomb()

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                player.move_dir.y = 0
            if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                player.move_dir.x = 0
"""