# src/ui/widgets.py

from __future__ import annotations
import pygame
from typing import Callable


class Button:
    """
    Basit ama şık pygame butonu:
      - yuvarlatılmış köşeler
      - hover rengi
      - hafif gölge efekti
    """

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Callable[[], None],
        font: pygame.font.Font,
        *,
        base_color: tuple[int, int, int] = (45, 45, 50),
        hover_color: tuple[int, int, int] = (70, 70, 80),
        text_color: tuple[int, int, int] = (240, 240, 240),
        shadow_offset: int = 4,
    ) -> None:
        self.rect = rect
        self.text = text
        self.on_click = on_click
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.shadow_offset = shadow_offset

        self._hovered = False

        self._text_surf = self.font.render(self.text, True, self.text_color)
        self._text_rect = self._text_surf.get_rect(center=self.rect.center)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        color = self.hover_color if self._hovered else self.base_color

        # Gölge
        shadow_rect = self.rect.move(self.shadow_offset, self.shadow_offset)
        pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=10)

        # Ana buton
        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        surface.blit(self._text_surf, self._text_rect)
