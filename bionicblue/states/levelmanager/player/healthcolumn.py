
### third-party imports

from pygame import Surface, Rect

from pygame.draw import rect as draw_rect, circle as draw_circle


### local import

from ....config import SURF_MAP, COLORKEY

from ....pygamesetup.constants import blit_on_screen



class HealthColumn:

    def __init__(self):

        self.full_health = 32
        self.health = 32

        self.head_surf = SURF_MAP['blue_shooter_man_head.png']
        self.head_rect = self.head_surf.get_rect()

        self.update_structure()

    def update_structure(self):

        hbg = self.health_bg = Rect(0, 0, 4, self.full_health)
        hfg = self.health_fg = Rect(0, 0, 4, self.health)

        head_rect = self.head_rect

        head_rect.top = hbg.bottom + 2

        rects = [hbg, hfg, head_rect]

        centerx = max(hbg.centerx, head_rect.centerx)

        for rect in rects:
            rect.centerx = centerx

        for rect in rects:
            rect.move_ip(2, 2)

        first, *rest = rects

        union_rect = first.unionall(rects)
        self.rect = union_rect.inflate(4, 4)

        image = self.image = Surface(self.rect.size).convert()

        image.set_colorkey(COLORKEY)
        image.fill(COLORKEY)

        draw_rect(image, 'grey80', hbg.inflate(4, 4))
        draw_circle(image, 'grey80', head_rect.center, 7)

        draw_rect(image, 'brown', hbg)
        draw_rect(image, 'gold', hfg)

        image.blit(self.head_surf, head_rect)

        self.rect.topleft = (3, 28)

    def damage(self, amount):

        self.health += -amount

        self.health_fg.height = max(self.health, 0)
        self.health_fg.bottom = self.health_bg.bottom

        draw_rect(self.image, 'brown', self.health_bg)
        draw_rect(self.image, 'gold', self.health_fg)

    def is_depleted(self):
        return self.health <= 0

    def draw(self):
        blit_on_screen(self.image, self.rect)
