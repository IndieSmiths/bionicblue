
### standard library import
from functools import partial


### local imports

from ......config import REFS, SURF_MAP

from ......constants import GRAVITY_ACCEL

from ......pygamesetup.constants import SCREEN_RECT, blit_on_screen

from ....common import (
    PROJECTILES,
    ACTORS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    append_task,
)



CRATE_MAX_Y_SPEED = 6


class FallingCrate:

    def __init__(self, midbottom):

        self.image = SURF_MAP['crate16.png']

        self.rect = rect = self.image.get_rect()
        self.inflated_rect = rect.inflate(16, 0)

        self.colliderect = rect.colliderect

        setattr(self.rect, 'midbottom', midbottom)

        self.x_speed = self.y_speed = 0

    def trigger_kill(self):
        append_task(partial(PROJECTILES.remove, self))

    def update(self):

        rect = self.rect
        
        ### move vertically

        if self.x_speed == 0:

            y_speed = self.y_speed
            y_speed = min(y_speed + GRAVITY_ACCEL, CRATE_MAX_Y_SPEED)
            rect.y += y_speed
            self.y_speed = y_speed

        ### move horizontally

        else:
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

        ### if inflated rect hits boss near the floor,
        ### give the crate x speed

        boss = REFS.level_boss

        irect = self.inflated_rect
        irect.center = rect.center

        if irect.colliderect(boss.rect):

            moved_down_rect = rect.move(0, 12)

            for block in BLOCKS_NEAR_SCREEN:

                if block.colliderect(moved_down_rect):

                    self.x_speed = (
                        -10
                        if 'left' in boss.aniplayer.anim_name
                        else 10
                    )

    def draw(self):
        blit_on_screen(self.image, self.rect)
