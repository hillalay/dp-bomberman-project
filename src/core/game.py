# src/core/game.py

from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

from core.config import GameConfig
from model.world import World
from view.renderer import Renderer
from data.users_repo import UsersRepo
from data.preferences_repo import PreferencesRepo
from audio.sound_manager import SoundManager
from audio.sound_events import SoundEventListener
from controller.command_invoker import CommandInvoker
from controller.command_mapper import CommandMapper


if TYPE_CHECKING:
    from states.base import GameState


class Game:
    def __init__(self):
        # -------------------------
        # Pygame + mixer init
        # -------------------------
        pygame.init()
        try:
            pygame.mixer.init()
            print("[Audio] mixer init OK")
        except Exception as e:
            print("[Audio] mixer init FAILED:", repr(e))

        # -------------------------
        # Config & ekran
        # -------------------------
        self.config = GameConfig.get_instance()
        # World içinden skora erişmek için
        self.config.game = self

        # Sprint 4: skor tek kaynak
        self.score = 0

        self.screen = pygame.display.set_mode(
            (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("DP Bomberman")

        # -------------------------
        # Repository Pattern: Users & Preferences
        # -------------------------
        self.users_repo = UsersRepo()
        self.preferences_repo = PreferencesRepo()

        # Şimdilik tek kullanıcı: "player1"
        self.active_user = self._ensure_default_user()
        self.active_user_id = self.active_user.id

        # Kullanıcının tercihlerini DB'den yükle
        prefs = self.preferences_repo.get_or_create_for_user(self.active_user_id)

        # Temayı config'e uygula
        self.config.set_theme(prefs.theme)

        # Volume & mute durumlarını config'te tutalım
        self.config.MUSIC_VOLUME = prefs.music_volume
        self.config.SFX_VOLUME = prefs.sfx_volume
        self.config.MUSIC_MUTED = prefs.music_muted
        self.config.SFX_MUTED = prefs.sfx_muted

        # -------------------------
        # SoundManager (müzik + efektler)
        # -------------------------
        initial_music_vol = 0.0 if prefs.music_muted else prefs.music_volume
        initial_sfx_vol = 0.0 if prefs.sfx_muted else prefs.sfx_volume

        self.sound = SoundManager(
            music_volume=initial_music_vol,
            sfx_volume=initial_sfx_vol,
        )

        # SFX dosyalarını yükle (path'ler sende wav ise ona göre)
        self.sound.load_sfx("explosion", "sfx/explosion.wav")
        self.sound.load_sfx("bomb_place", "sfx/bomb_place.wav")
        self.sound.load_sfx("powerup", "sfx/powerup.wav")

        # EventBus üzerinden ses event'lerini dinleyen observer
        self.sound_events = SoundEventListener(self.sound)

        # -------------------------
        # Oyun loop bileşenleri
        # -------------------------
        self.clock = pygame.time.Clock()
        self.running = True

        # Model & View (PlayingState kullanacak)
        self.world = World(self.config)
        self.renderer = Renderer(self.screen)
        self.command_invoker=CommandInvoker()
        self.command_mapper = CommandMapper()

        # İlk state: Menü
        from states.menu import MenuState
        self.current_state: GameState = MenuState(self)
        self.current_state.enter()

    # Aktif user yoksa player1 oluştur
    def _ensure_default_user(self):
        """
        Şimdilik tek oyunculu profil:
        'player1' diye bir kullanıcı yoksa DB'de oluştur, varsa onu kullan.
        """
        user = self.users_repo.get_by_username("player1")
        if user is None:
            user = self.users_repo.create_user("player1", "player1")
            print("[Game] New default user created: player1/player1")
        else:
            print(f"[Game] Existing user loaded: {user.username}")
        return user
    
    def start_new_game(self) -> None:
        self.score = 0
        self.world = World(self.config)

    def on_win(self) -> None:
        from states.win import WinState
        self.set_state(WinState(self))




    # STATE DEĞİŞTİRME
    def set_state(self, new_state: "GameState"):
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()

    # ANA LOOP
    def run(self):
        while self.running:
            dt = self.clock.tick(self.config.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_state.handle_event(event)

            if not self.running:
                break

            self.current_state.update(dt)
            self.current_state.render(self.screen)

            pygame.display.flip()

        pygame.quit()
