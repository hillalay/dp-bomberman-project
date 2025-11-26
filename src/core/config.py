# src/core/config.py

class GameConfig:
    _instance: "GameConfig | None" = None

    @classmethod
    def get_instance(cls) -> "GameConfig":
        if cls._instance is None:
            cls._instance = GameConfig()
        return cls._instance

    def __init__(self):
        if GameConfig._instance is not None:
            raise Exception("Use GameConfig.get_instance() instead of GameConfig()")

        # -------------------------
        # Grid & ekran
        # -------------------------
        self.TILE_SIZE = 48
        self.GRID_WIDTH = 15
        self.GRID_HEIGHT = 13

        self.SCREEN_WIDTH = self.TILE_SIZE * self.GRID_WIDTH
        self.SCREEN_HEIGHT = self.TILE_SIZE * self.GRID_HEIGHT

        # -------------------------
        # Oyun ayarları
        # -------------------------
        self.FPS = 60
        self.PLAYER_SPEED = 4 * self.TILE_SIZE
        self.BOMB_TIMER = 2.0
        self.MAX_BOMBS = 3

        # -------------------------
        # Aktif tema
        # -------------------------
        self.THEME = "forest"  # "desert", "forest", "city"

        # -------------------------
        # Tema paletleri
        # -------------------------
        self.THEMES = {
                 "forest": {
                # Toprak rengi arkaplan
                "bg": (130, 90, 50),     # kahverengi toprak
                "bg_alt": (130, 90, 50), # tek renk kullanıyoruz
                            

                # UNBREAKABLE taş duvarlar (açık gri)
                "solid_wall": (205, 205, 215),
                "solid_wall_border": (130, 130, 140),

                # BREAKABLE (kahverengi kutular)
                "soft_wall": (189, 140, 92),
                "soft_wall_border": (132, 95, 60),

                # Oyuncu / bomba / patlama (şimdilik placeholder)
                "player": (255, 255, 255),
                "bomb": (30, 30, 30),
                "explosion": (255, 210, 90),
            },


            "desert": {
                "bg": (222, 200, 140),
                "bg_alt": (210, 185, 130),

                "solid_wall": (170, 170, 170),
                "solid_wall_border": (120, 120, 120),

                "soft_wall": (200, 160, 120),
                "soft_wall_border": (140, 110, 85),

                "player": (255, 255, 255),
                "bomb": (30, 30, 30),
                "explosion": (255, 210, 100),
            },

            "city": {
                "bg": (185, 185, 185),  # CITY zemin rengi
                "bg_alt": (185, 185, 185),  # düz tek renk

                "solid_wall": (110, 110, 120),
                "solid_wall_border": (60, 60, 70),

                "soft_wall": (160, 60, 60),
                "soft_wall_border": (110, 40, 40),

                "player": (240, 240, 240),
                "bomb": (20, 20, 20),
                "explosion": (255, 160, 60),
            },
        }

        # Aktif temaya göre derived renkleri doldur
        self._apply_active_theme_colors()

    # -------------------------------------------------
    # Tema değiştirme
    # -------------------------------------------------
    def set_theme(self, theme_name: str) -> None:
        if theme_name in self.THEMES:
            self.THEME = theme_name
            self._apply_active_theme_colors()

    # -------------------------------------------------
    # Aktif temadan eski isimlerle renk üret
    # -------------------------------------------------
    def _apply_active_theme_colors(self) -> None:
        theme = self.THEMES[self.THEME]

        # Arka plan (bazı yerler BG_COLOR kullanıyor)
        self.BG_COLOR = theme["bg"]

        # Eski isimlerle uyumluluk:
        # Player & Bomb
        self.COLOR_PLAYER = theme["player"]
        self.COLOR_BOMB = theme["bomb"]

        # Duvar renkleri (entities.Wall burada bunları bekliyor)
        self.COLOR_WALL_UNBREAKABLE = theme["solid_wall"]
        self.COLOR_WALL_BREAKABLE = theme["soft_wall"]
        # HARD için biraz koyu bir ton seçiyoruz
        self.COLOR_WALL_HARD = theme["solid_wall_border"]
