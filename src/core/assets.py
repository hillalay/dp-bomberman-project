import pygame
from core.assets import Assets

class Assets:
    _cache = {}

    @staticmethod
    def load(path, scale=None):
        if path not in Assets._cache:
            img = pygame.image.load(path).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            Assets._cache[path] = img
        return Assets._cache[path]

def draw(self, s):
    # 150ms per frame → 3 frame döngü
    elapsed = pygame.time.get_ticks() - self.placed_ms
    frame = (elapsed // 150) % 3

    img = Assets.load(
        f"assets/sprites/bomb/bomb_{frame}.png",
        (self.rect.width, self.rect.height)
    )
    s.blit(img, self.rect)
