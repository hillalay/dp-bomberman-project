# src/states/options.py

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from states.base import GameState
from ui.widgets import Button
from data.preferences_repo import PreferencesRepo

if TYPE_CHECKING:
    from core.game import Game


class OptionsState(GameState):
    """
    Oyun ayarları menüsü.
    - Music Volume
    - SFX Volume
    - Music Mute
    - SFX Mute
    Değerler DB'de Preferences tablosunda saklanır (Repository Pattern).
    """

    def __init__(self, game: Game):
        super().__init__(game)

        self.title_font = pygame.font.SysFont("Arial", 42, bold=True)
        self.label_font = pygame.font.SysFont("Arial", 24)
        self.button_font = pygame.font.SysFont("Arial", 22)

        # --- Repo + aktif kullanıcı ---
        # Game içinde zaten bir PreferencesRepo var; aynısını kullanalım.
        self.prefs_repo: PreferencesRepo = self.game.preferences_repo
        self.active_user_id: int = self.game.active_user_id

        # Mevcut preferences'ı DB'den çek
        prefs = self.prefs_repo.get_or_create_for_user(self.active_user_id)

        # Local state (ekranda göstereceğimiz değerler)
        self.current_theme = prefs.theme
        self.music_volume = prefs.music_volume      # 0.0 - 1.0
        self.sfx_volume = prefs.sfx_volume          # 0.0 - 1.0
        self.music_muted = prefs.music_muted
        self.sfx_muted = prefs.sfx_muted

        self.buttons: list[Button] = []
        self._create_buttons()

    # -----------------------------
    # Butonları oluştur
    # -----------------------------
    def _create_buttons(self):
        surface = self.game.screen
        w, h = surface.get_size()

        btn_w, btn_h = 140, 40
        spacing = 10
        center_x = w // 2

        def make_rect(row: int, col_offset: int = 0):
            """
            row: satır indexi (0,1,2,3,...)
            col_offset:
              -1 → solda
               0 → ortada
               1 → sağda
            """
            base_y = h // 2 - 80 + row * (btn_h + spacing)
            x = center_x + col_offset * (btn_w + 12) - btn_w // 2
            return pygame.Rect(x, base_y, btn_w, btn_h)

        self.buttons = [
            # MUSIC VOLUME -
            Button(
                make_rect(0, -1),
                "Music -",
                self._decrease_music_volume,
                self.button_font,
            ),
            # MUSIC VOLUME +
            Button(
                make_rect(0, 1),
                "Music +",
                self._increase_music_volume,
                self.button_font,
            ),
            # SFX VOLUME -
            Button(
                make_rect(1, -1),
                "SFX -",
                self._decrease_sfx_volume,
                self.button_font,
            ),
            # SFX VOLUME +
            Button(
                make_rect(1, 1),
                "SFX +",
                self._increase_sfx_volume,
                self.button_font,
            ),
            # MUSIC MUTE TOGGLE
            Button(
                make_rect(2, -1),
                "Mute Music",
                self._toggle_music_mute,
                self.button_font,
            ),
            # SFX MUTE TOGGLE
            Button(
                make_rect(2, 1),
                "Mute SFX",
                self._toggle_sfx_mute,
                self.button_font,
            ),
            # GERİ DÖN (MENÜYE)
            Button(
                make_rect(4, 0),
                "Back to Menu",
                self._save_and_back_to_menu,
                self.button_font,
            ),
        ]

    # -----------------------------
    # Volume & Mute değişimleri
    # -----------------------------
    def _clamp_volume(self, v: float) -> float:
        return max(0.0, min(1.0, v))

    def _increase_music_volume(self):
        if self.music_muted:
            return
        self.music_volume = self._clamp_volume(self.music_volume + 0.1)
        print("[Options] Music volume:", self.music_volume)

        # Çalan müziğin sesini anında güncelle (SoundManager üzerinden)
        self.game.sound.set_music_volume(self.music_volume)

    def _decrease_music_volume(self):
        if self.music_muted:
            return
        self.music_volume = self._clamp_volume(self.music_volume - 0.1)
        print("[Options] Music volume:", self.music_volume)

        self.game.sound.set_music_volume(self.music_volume)

    def _increase_sfx_volume(self):
        if self.sfx_muted:
            return
        self.sfx_volume = self._clamp_volume(self.sfx_volume + 0.1)
        print("[Options] SFX volume:", self.sfx_volume)

        self.game.sound.set_sfx_volume(self.sfx_volume)

    def _decrease_sfx_volume(self):
        if self.sfx_muted:
            return
        self.sfx_volume = self._clamp_volume(self.sfx_volume - 0.1)
        print("[Options] SFX volume:", self.sfx_volume)

        self.game.sound.set_sfx_volume(self.sfx_volume)

    def _toggle_music_mute(self):
        self.music_muted = not self.music_muted
        print("[Options] Music muted:", self.music_muted)

        # Mute olduysa volume = 0, değilse mevcut değeri kullan
        if self.music_muted:
            self.game.sound.set_music_volume(0.0)
        else:
            self.game.sound.set_music_volume(self.music_volume)

    def _toggle_sfx_mute(self):
        self.sfx_muted = not self.sfx_muted
        print("[Options] SFX muted:", self.sfx_muted)

        if self.sfx_muted:
            self.game.sound.set_sfx_volume(0.0)
        else:
            self.game.sound.set_sfx_volume(self.sfx_volume)

    # -----------------------------
    # DB'ye kaydet ve menüye dön
    # -----------------------------
    def _save_preferences(self):
        """
        Local değişiklikleri DB'ye ve config'e yazar.
        """
        user_id = self.active_user_id

        # 1) DB'ye yaz
        self.prefs_repo.update_preferences(
            user_id=user_id,
            theme=self.current_theme,
            music_volume=self.music_volume,
            sfx_volume=self.sfx_volume,
            music_muted=self.music_muted,
            sfx_muted=self.sfx_muted,
        )

        # 2) Config'e uygula
        cfg = self.game.config
        cfg.set_theme(self.current_theme)
        cfg.MUSIC_VOLUME = self.music_volume
        cfg.SFX_VOLUME = self.sfx_volume
        cfg.MUSIC_MUTED = self.music_muted
        cfg.SFX_MUTED = self.sfx_muted

        # 3) Ses sistemini netle (mute işini de gözden geçir)
        if self.music_muted:
            self.game.sound.set_music_volume(0.0)
        else:
            self.game.sound.set_music_volume(self.music_volume)

        if self.sfx_muted:
            self.game.sound.set_sfx_volume(0.0)
        else:
            self.game.sound.set_sfx_volume(self.sfx_volume)

        print("[Options] Preferences saved to DB & config.")

    def _save_and_back_to_menu(self):
        """
        Ayarları kaydedip ana menüye döner.
        """
        self._save_preferences()
        from states.menu import MenuState
        self.game.set_state(MenuState(self.game))

    # -----------------------------
    # GameState override'ları
    # -----------------------------
    def enter(self):
        print("[OptionsState] enter")

    def exit(self):
        print("[OptionsState] exit")

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # ESC ile de geri dön
            self._save_and_back_to_menu()
            return

        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float):
        for btn in self.buttons:
            btn.update(dt)

    def render(self, surface: pygame.Surface):
        surface.fill((12, 16, 24))

        # Başlık
        title_surf = self.title_font.render("Options", True, (230, 230, 255))
        title_rect = title_surf.get_rect(center=(surface.get_width() // 2, 80))
        surface.blit(title_surf, title_rect)

        # Music Label
        music_text = f"Music Volume: {self.music_volume:.1f}"
        if self.music_muted:
            music_text += " (MUTED)"
        music_surf = self.label_font.render(music_text, True, (220, 220, 220))
        music_rect = music_surf.get_rect(center=(surface.get_width() // 2, 160))
        surface.blit(music_surf, music_rect)

        # SFX Label
        sfx_text = f"SFX Volume: {self.sfx_volume:.1f}"
        if self.sfx_muted:
            sfx_text += " (MUTED)"
        sfx_surf = self.label_font.render(sfx_text, True, (220, 220, 220))
        sfx_rect = sfx_surf.get_rect(center=(surface.get_width() // 2, 220))
        surface.blit(sfx_surf, sfx_rect)

        # Butonları çiz
        for btn in self.buttons:
            btn.render(surface)
