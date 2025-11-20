class Renderer:
    def __init__(self, screen):
        self.screen = screen

    def draw_world(self, world):
        # Sıra: duvarlar → bombalar → oyuncu
        for wall in world.walls:
            wall.draw(self.screen)

        for bomb in world.bombs:
            bomb.draw(self.screen)

        world.player.draw(self.screen)
