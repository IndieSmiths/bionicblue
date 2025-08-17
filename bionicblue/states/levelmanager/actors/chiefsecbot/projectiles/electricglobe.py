
### standard library import
from functools import partial


### third-party imports

from pygame import Surface

from pygame.draw import circle as draw_circle


### local imports

from ......config import REFS, COLORKEY

from ......constants import GRAVITY_ACCEL

from ......pygamesetup.constants import SCREEN_RECT, blit_on_screen

from ....common import (
    PROJECTILES,
    ACTORS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    append_task,
)



class ElectricGlobe:

    def __init__(self, center, orientation):

        image = self.image = Surface((8, 8)).convert()

        self.rect = rect = image.get_rect()

        image.set_colorkey(COLORKEY)
        image.fill(COLORKEY)
        draw_circle(image, 'white', rect.center, rect.width//2)

        setattr(self.rect, 'center', center)

        self.x_speed = -1 if orientation == 'left' else 1

    def trigger_kill(self):
        append_task(partial(PROJECTILES.remove, self))

    def update(self):

        rect = self.rect
        rect.move_ip(self.x_speed, 0)

        ### destroy if hit block...

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):

                self.trigger_kill()
                return

        ### or if hits player...

        player = REFS.states.level_manager.player

        if rect.colliderect(player.rect):

            player.damage(3)
            self.trigger_kill()
            return

    def draw(self):
        blit_on_screen(self.image, self.rect)
