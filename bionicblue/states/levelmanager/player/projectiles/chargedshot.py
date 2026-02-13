
### standard library import
from functools import partial


### third-party import
from pygame import Surface


### local imports

from .....config import SOUND_MAP

from .....pygamesetup.constants import SCREEN_RECT, blit_on_screen

from .....constants import CHARGED_SHOT_SPEED

from .....ani2d.player import AnimationPlayer2D

from ...common import (
    PROJECTILES,
    ACTORS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
)

from ...taskmgmt import append_ready_task



class ChargedShot:

    def __init__(self, charge_type, x_orientation, pos_name, pos_value):

        self.x_speed = x_orientation * CHARGED_SHOT_SPEED

        animation_data_key = (
            'full_charged_shot'
            if charge_type == 'full'
            else 'middle_charged_shot'
        )

        initial_animation = (
            'appearing_right'
            if x_orientation > 0
            else 'appearing_left'
        )

        self.aniplayer = (
            AnimationPlayer2D(self, animation_data_key, initial_animation)
        )

        self.firing_sound_name = (
            'full_charged_shot_shot.wav'
            if charge_type == 'full'
            else 'middle_charged_shot_shot.wav'
        )
        self.disappearing_sound_name = (
            'full_charged_shot_vanish.wav'
            if charge_type == 'full'
            else 'middle_charged_shot_vanish.wav'
        )

        self.damage_to_inflict = 5 if charge_type == 'full' else 3

        setattr(self.rect, pos_name, pos_value)

        self.update = self.appearing_update

    def trigger_kill(self):
        append_ready_task(partial(PROJECTILES.remove, self))

    def appearing_update(self):

        ap = self.aniplayer

        if ap.main_timing.peek_loops_no(1) == 1:

            self.update = self.moving_update

            ap.switch_animation(
                'idle_right'
                if 'right' in ap.anim_name
                else 'idle_left'
            )

            SOUND_MAP[self.firing_sound_name].play()

    def moving_update(self):
        
        colliderect = self.rect.colliderect

        if not colliderect(SCREEN_RECT):
            self.trigger_kill()
            return

        for actor in ACTORS_NEAR_SCREEN:

            if colliderect(actor.rect):

                if actor.health > 0:

                    try:
                        method = getattr(actor, 'damage')
                    except AttributeError:
                        pass
                    else:
                        method(self.damage_to_inflict)

                    if actor.health > 0:
                        self.trigger_disappearing(actor)
                        return

        for block in BLOCKS_NEAR_SCREEN:

            if colliderect(block.rect):
                self.trigger_disappearing(block)
                return

        self.rect.x += self.x_speed

    def trigger_disappearing(self, colliding_obj):

        self.update = self.disappearing_update
        SOUND_MAP[self.disappearing_sound_name].play()

        ap = self.aniplayer

        oriented_right = 'right' in ap.anim_name

        ap.switch_animation(
            'disappearing_right'
            if oriented_right
            else 'disappearing_left'
        )

        rect = self.rect

        opposite_end_name = 'left' if oriented_right else 'right'

        block_opposite_end = getattr(colliding_obj.rect, opposite_end_name)
        shot_opposite_end = getattr(rect, opposite_end_name)

        ### if difference between opposite ends of block and shot is not
        ### that large (for instance, smaller than the shot width),
        ### move shot's centerx to opposite end of block;
        ###
        ### before this measure, we just always moved the shot's centerx
        ### to the block opposite end, which looks nice in common static
        ### blocks; however, once we introduced moving platforms, a platform
        ### moving upwards would have its top hit the full charged shot when
        ### the player shot while standing on it, and the shot would
        ### then be snaped to one of the opposite ends of the platform, far
        ### from the spot where the shot hit the platform; now we always check
        ### such distance and only move the shot when it is small, ensuring
        ### the shot is only moved a small amount, if at all.

        if abs(block_opposite_end - shot_opposite_end) < rect.width:
            rect.centerx = block_opposite_end

    def disappearing_update(self):

        ap = self.aniplayer

        if ap.main_timing.peek_loops_no(1) == 1:
            self.trigger_kill()

    def draw(self):
        self.aniplayer.draw()
