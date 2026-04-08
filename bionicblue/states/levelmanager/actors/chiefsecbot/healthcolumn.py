
### standard library import
from math import inf as INFINITY


### third-party imports

from pygame import Surface, Rect

from pygame.draw import rect as draw_rect


### local imports

from .....pygamesetup.constants import SCREEN_RECT, blit_on_screen



FULL_HEALTH = 50

class HealthColumn:

    def __init__(self):

        self.health = self.full_health = FULL_HEALTH

        hbg = self.health_bg = Rect(0, 0, 4, self.full_health)
        hfg = self.health_fg = Rect(0, 0, 4, self.health)
        rect = self.rect = hbg.inflate(4, 4)

        rect.topleft = (0, 0)
        hbg.center = rect.center
        hfg.midbottom = hbg.midbottom

        rect.right = SCREEN_RECT.move(-5, 0).right
        rect.top = 28

        image = self.image = Surface(rect.size).convert()

        image.fill('grey80')
        draw_rect(image, 'brown', hbg)
        draw_rect(image, 'red', hfg)

    def reset(self):
        self.damage(-INFINITY)

    def update(self): pass

    def damage(self, amount):

        self.health += -amount
        self.health = min(max(0, self.health), FULL_HEALTH)

        self.health_fg.height = self.health
        self.health_fg.bottom = self.health_bg.bottom

        draw_rect(self.image, 'brown', self.health_bg)
        draw_rect(self.image, 'red', self.health_fg)

    def is_depleted(self):
        return self.health <= 0

    def draw(self):
        blit_on_screen(self.image, self.rect)
