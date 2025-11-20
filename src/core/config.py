class GameConfig:
    _instance = None

    def __init__(self):
        if GameConfig._instance is not None:
            raise Exception("Use GameConfig.get_instance() instead of GameConfig()")

        # --- Grid / ekran ---
        self.TILE_SIZE = 48
        self.GRID_WIDTH = 15
        self.GRID_HEIGHT = 13

        self.SCREEN_WIDTH = self.TILE_SIZE * self.GRID_WIDTH
        self.SCREEN_HEIGHT = self.TILE_SIZE * self.GRID_HEIGHT

        # --- Oyun / bomba ---
        self.FPS = 60
        self.PLAYER_SPEED = 4 * self.TILE_SIZE
        self.BOMB_TIMER = 2.0
        self.MAX_BOMBS = 3

        # 🔹 OYUNCU ve BOMBA RENKLERİ (BUNLAR EKSİKTİ)
        self.COLOR_PLAYER = (255, 255, 255)
        self.COLOR_BOMB = (255, 255, 0)

        # --- Başlangıç teması ---
        self.THEME = "forest"  # "desert", "forest", "city"
        self._apply_theme_colors()

    def _apply_theme_colors(self):
        # Varsayılanlar
        self.BG_COLOR = (0, 0, 0)
        self.COLOR_WALL_UNBREAKABLE = (160, 160, 160)
        self.COLOR_WALL_BREAKABLE = (190, 120, 60)
        self.COLOR_WALL_HARD = (110, 110, 110)

        if self.THEME == "desert":
            self.BG_COLOR = (194, 178, 128)
            self.COLOR_WALL_UNBREAKABLE = (160, 160, 160)
            self.COLOR_WALL_BREAKABLE = (210, 180, 140)
            self.COLOR_WALL_HARD = (120, 120, 120)

        elif self.THEME == "forest":
            self.BG_COLOR = (16, 120, 16)
            self.COLOR_WALL_UNBREAKABLE = (120, 120, 120)
            self.COLOR_WALL_BREAKABLE = (80, 120, 60)
            self.COLOR_WALL_HARD = (60, 60, 60)

        elif self.THEME == "city":
            self.BG_COLOR = (40, 40, 40)
            self.COLOR_WALL_UNBREAKABLE = (100, 100, 100)
            self.COLOR_WALL_BREAKABLE = (170, 70, 50)
            self.COLOR_WALL_HARD = (60, 60, 60)

    def set_theme(self, theme_name: str):
        """UI’den çağıracağız. Temayı değiştirip renkleri yeniden uygular."""
        if theme_name not in ("desert", "forest", "city"):
            return
        self.THEME = theme_name
        self._apply_theme_colors()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameConfig()
        return cls._instance
