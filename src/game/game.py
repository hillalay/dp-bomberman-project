import pygame

class Game:
    _instance = None  # Singleton: tek örnek tutmak için

    @staticmethod
    def get_instance():
        """Game sınıfının tek örneğini döndürür."""
        if Game._instance is None:
            Game()
        return Game._instance

    def __init__(self, width: int = 800, height: int = 600):
        # Eğer zaten instance varsa, yeni oluşturmayı engelle
        if Game._instance is not None:
            raise Exception("Game is a singleton! get_instance() kullan.")
        Game._instance = self

        # Pygame init
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("DP Bomberman Project")

        self.clock = pygame.time.Clock()
        self.is_running = True

        # Şimdilik sadece aktif state adını string olarak tutalım
        self.current_state_name = "PlayingState (stub)"  # B kişi gerçek state'i yazınca buraya bağlanacağız

        # Basit debug font
        self.font = pygame.font.SysFont("consolas", 18)

    def handle_input(self):
        """Klavye inputlarını yönetir (A kişisinin frontend görevi)."""
        keys = pygame.key.get_pressed()

        # Örnek: ESC ile oyundan çık
        if keys[pygame.K_ESCAPE]:
            self.is_running = False

        # Buraya ileride oyuncu hareketi (WASD, ok tuşları) gelecek
        # Ör: self.player.move(...)

    def update(self, dt: float):
        """Oyun mantığını günceller (backend)."""
        # Şimdilik placeholder
        # İleride: aktif state.update(dt), oyuncu, bomba, düşman güncellemeleri vs.
        pass

    def draw(self):
        """Ekranı çizer (frontend)."""
        # Arka planı siyaha boya
        self.screen.fill((0, 0, 0))

        # Basit debug HUD: aktif state adı ve FPS göster
        fps = self.clock.get_fps()
        debug_text = f"State: {self.current_state_name} | FPS: {fps:.1f}"

        text_surface = self.font.render(debug_text, True, (0, 255, 0))
        self.screen.blit(text_surface, (10, 10))

        # Ekranı güncelle
        pygame.display.flip()

    def run(self):
        """Ana game loop."""
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0  # 60 FPS hedef, dt saniye cinsinden

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False

            self.handle_input()
            self.update(dt)
            self.draw()

        pygame.quit()
