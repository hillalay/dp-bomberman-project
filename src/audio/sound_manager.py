# src/audio/sound_manager.py

import pygame
from typing import Dict
from utils.paths import asset_path

class SoundManager:
    """
    Tüm müzik ve efekt seslerini yöneten basit sınıf.
    - Oyun başında bir kere oluşturuyoruz (Game içinde).
    - States (MenuState, PlayingState, OptionsState) buradan müzik/SFX çağırıyor.
    """

    def __init__(self, music_volume: float = 1.0, sfx_volume: float = 1.0) -> None:
        # mixer daha önce init edilmemişse burada başlat
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        self.music_volume = music_volume
        self.sfx_volume = sfx_volume

        # İsim → Sound objesi
        self.sfx: Dict[str, pygame.mixer.Sound] = {}

    # ---------------------- MUSIC ----------------------
    def play_music(self, path: str, loop: bool = True) -> None:
        """
        path: 'music/menu_theme.mp3' gibi RELATIVE asset path
        """
        try:
            full_path = asset_path(path)  # <-- KRİTİK SATIR
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            # loop=True ise -1, değilse 0 kere çal
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception as e:
            print("[SoundManager] Müzik dosyası yüklenemedi:", path, repr(e))

    def stop_music(self) -> None:
        """Çalan müziği durdurur."""
        pygame.mixer.music.stop()

    def set_music_volume(self, volume: float) -> None:
        """
        Müzik sesini 0.0–1.0 aralığında ayarlar.
        Hem SoundManager içindeki değeri, hem pygame'in volume'ünü günceller.
        """
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    # ---------------------- SFX ----------------------
    def load_sfx(self, name: str, path: str) -> None:
        """
        Bir efekt sesini belleğe yükleyip dictionary'e koyar.
        name: 'explosion'
        path: 'sfx/explosion.wav' gibi RELATIVE asset path
        """
        full_path = asset_path(path)  # <-- KRİTİK SATIR
        try:
            
            sound = pygame.mixer.Sound(full_path)
            sound.set_volume(self.sfx_volume)
            self.sfx[name] = sound
            print("[SoundManager] SFX yüklendi:", name, full_path)
        except Exception as e:
            print("[SoundManager] SFX yüklenemedi:", name, full_path,repr(e))


    def play_sfx(self, name: str) -> None:
        """
        Daha önce load_sfx ile yüklenmiş bir efekti çalar.
        """
        name=name.strip()
        sound = self.sfx.get(name)
        if sound is not None:
            print(f"[SoundManager] play_sfx: '{name}' bulunamadı. Yüklü olanlar: {list(self.sfx.keys())}")
            sound.set_volume(self.sfx_volume)
            sound.play()
        else:
            print(f"[SoundManager] play_sfx: '{name}' bulunamadı. Yüklü olanlar: {list(self.sfx.keys())}")

    def set_sfx_volume(self, volume: float) -> None:
        """
        Tüm efekt seslerinin ses seviyesini günceller.
        OptionsState içindeki SFX slider'ı burayı çağırmalı.
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        for s in self.sfx.values():
            s.set_volume(self.sfx_volume)
