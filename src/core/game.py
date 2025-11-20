# src/core/game.py
import pygame
from core.config import GameConfig
from model.world import World
from controller.input_handler import InputHandler
from view.renderer import Renderer


class Game:
    def __init__(self):
        pygame.init()
        self.config = GameConfig.get_instance()

        self.screen = pygame.display.set_mode(
            (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("DP Bomberman")

        self.clock = pygame.time.Clock()

        # Font (tema butonları için)
        self.font = pygame.font.SysFont("Arial", 18)

        # Tema butonları: ekranın sol üst köşesine 3 kutu
        self.theme_buttons = [
            {"theme": "desert", "rect": pygame.Rect(10, 10, 90, 30), "label": "Desert"},
            {"theme": "forest", "rect": pygame.Rect(110, 10, 90, 30), "label": "Forest"},
            {"theme": "city",   "rect": pygame.Rect(210, 10, 90, 30), "label": "City"},
        ]

        self.world = World(self.config)
        self.input_handler = InputHandler()
        self.renderer = Renderer(self.screen)

    def run(self):
        running = True

        while running:
            dt = self.clock.tick(self.config.FPS) / 1000.0

            # --- EVENT LOOP ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break  # event loop'u bırak, bu frame'de artık devam etmeyeceğiz
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_mouse_click(event.pos)
                else:
                    self.input_handler.handle_event(event, self.world)

            if not running:
                break  # ana while'dan çık

            # --- Model Update ---
            self.world.update(dt)

            # --- View Draw ---
            self.screen.fill(self.config.BG_COLOR)
            self.renderer.draw_world(self.world)
            self._draw_theme_buttons()
            pygame.display.flip()

        # Döngü tamamen bittikten sonra pygame'i kapat
        pygame.quit()

    def _handle_mouse_click(self, pos):
        for btn in self.theme_buttons:
            if btn["rect"].collidepoint(pos):
                self.config.set_theme(btn["theme"])
                # Sadece tıkladığımız butonda çalışsın, sonra çık
                break

    def _draw_theme_buttons(self):
        for btn in self.theme_buttons:
            rect = btn["rect"]
            is_active = (btn["theme"] == self.config.THEME)

            # Aktif tema ise farklı renk
            bg = (220, 220, 220) if is_active else (120, 120, 120)
            border = (255, 255, 255) if is_active else (0, 0, 0)

            pygame.draw.rect(self.screen, bg, rect)
            pygame.draw.rect(self.screen, border, rect, width=2)

            text_surf = self.font.render(btn["label"], True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)
