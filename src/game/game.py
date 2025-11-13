import pygame

class Game:
    _instance = None

    @staticmethod
    def get_instance():
        if Game._instance is None:
            Game()
        return Game._instance

    def __init__(self, width: int = 800, height: int = 600):
        if Game._instance is not None:
            raise Exception("Game is a singleton! Use get_instance().")
        Game._instance = self

        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("DP Bomberman Project")

        self.clock = pygame.time.Clock()
        self.is_running = True

        self.current_state_name = "PlayingState (stub)"
        self.font = pygame.font.SysFont("consolas", 18)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.is_running = False

    def update(self, dt: float):
        pass

    def draw(self):
        self.screen.fill((0, 0, 0))
        fps = self.clock.get_fps()
        debug_text = f"State: {self.current_state_name} | FPS: {fps:.1f}"
        text_surface = self.font.render(debug_text, True, (0, 255, 0))
        self.screen.blit(text_surface, (10, 10))
        pygame.display.flip()

    def run(self):
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False

            self.handle_input()
            self.update(dt)
            self.draw()

        pygame.quit()
