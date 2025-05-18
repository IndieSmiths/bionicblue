
### standard library import
from functools import partial


### third-party import
from pygame import Surface


### local imports

from .....config import SOUND_MAP

from .....pygamesetup.constants import SCREEN_RECT, blit_on_screen

from ...common import (
    PROJECTILES,
    ACTORS_ON_SCREEN,
    BLOCKS_ON_SCREEN,
    append_task,
)



class DefaultProjectile:

    surf = Surface((3, 2)).convert()
    surf.fill('yellow')

    abs_speed = 10

    def __init__(self, x_orientation, pos_name, pos_value):

        self.x_speed = x_orientation * self.abs_speed

        self.image = self.surf

        self.rect = rect = self.image.get_rect()
        self.colliderect = rect.colliderect

        self.expanded_rect = rect.inflate(2, 0)
        self.colliderect_expanded = self.expanded_rect.colliderect

        setattr(self.rect, pos_name, pos_value)
        SOUND_MAP['default_projectile_shot.wav'].play()

    def trigger_kill(self):
        append_task(partial(PROJECTILES.remove, self))

    def update(self):

        self.rect.move_ip(self.x_speed, 0)

        colliderect = self.colliderect

        if not colliderect(SCREEN_RECT):

            self.trigger_kill()
            return

        exp_rect = self.expanded_rect
        exp_rect.center = self.rect.center

        colliderect_expanded = self.colliderect_expanded

        for actor in ACTORS_ON_SCREEN:

            if colliderect_expanded(actor.rect):

                if actor.health > 0:

                    try: actor.damage(1)
                    except AttributeError:
                        pass

                    self.trigger_kill()
                    SOUND_MAP['default_projectile_hit.wav'].play()

                    return

        for block in BLOCKS_ON_SCREEN:

            if colliderect(block.rect):

                self.trigger_kill()
                return

    def draw(self):
        blit_on_screen(self.image, self.rect)
