"""Facility for Giovanni NPC."""

### local imports

from ....config import REFS

from ....ani2d.player import AnimationPlayer2D



class Giovanni:

    def __init__(self, pos):

        self.player = REFS.states.level_manager.player

        self.name = 'giovanni'

        self.x_speed = 0

        animation_name = 'idle_left'

        self.aniplayer = (
            AnimationPlayer2D(
                self, 'giovanni_npc', animation_name, 'midbottom', pos
            )
        )

        self.update = self.idle_update

    def idle_update(self):
        """Do nothing."""

    def leaving_update(self):

        rect = self.rect
        center = rect.center

        x_speed = self.x_speed
        colliderect = rect.colliderect

        rect.move_ip(x_speed, 0)

        ###

        if rect.center != center:

            self.delta += tuple(
                a - b
                for a, b
                in zip(rect.center, center)
            )

    def draw(self):
        self.aniplayer.draw()
