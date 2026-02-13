"""Facility for electric globe projectile."""

### standard library import

from functools import partial

from itertools import cycle


### third-party imports

from pygame import Surface

from pygame.draw import (
    circle as draw_circle,
    lines as draw_lines,
)


### local imports

from .......config import REFS, COLORKEY, SOUND_MAP

from .......pygamesetup.constants import blit_on_screen, msecs_to_frames

from .....common import PROJECTILES

from .....taskmgmt import append_ready_task

from .assist import (
    RADII,
    RADIUS_TO_AREA_MAP,
    MAX_RADIUS,
    MIN_RADIUS,
    FULL_SIZE,
    CENTER,
    LIGHTNING_BOLT_INDICES,
    LIGHTNING_POINTS_MAP,
)



_RADIUS_SWITCH_MSECS = 200
RADIUS_SWITCH_FRAMES = msecs_to_frames(_RADIUS_SWITCH_MSECS)

_LIFESPAN_MSECS = 6000
LIFESPAN_FRAMES = msecs_to_frames(_LIFESPAN_MSECS)

FILL_COLORS = (
    (('white',) * 3)
    + (('',)* 5)
)


class ElectricGlobe:
    
    # set to keep track of existing instances;
    # used so we know when to start/stop playing the electric
    # globe sound
    instances = set()

    def __init__(self, center, orientation):

        image = self.image = Surface(FULL_SIZE).convert()

        image.set_colorkey(COLORKEY)
        image.fill(COLORKEY)

        self.radius_switch_countdown = RADIUS_SWITCH_FRAMES
        self.lifespan_countdown = LIFESPAN_FRAMES

        self.next_radius = cycle(RADII).__next__
        self.next_lightning_bolt = cycle(LIGHTNING_BOLT_INDICES).__next__
        self.next_fill_color = cycle(FILL_COLORS).__next__

        self.radius = self.next_radius()

        self.update_image()

        self.rect = image.get_rect()
        setattr(self.rect, 'center', center)

        self.x_speed = -1 if orientation == 'left' else 1

        # only start playing if there isn't already an existing
        # electric globe

        if not self.instances:
            SOUND_MAP['electric_globe_crackling.wav'].play(-1)

        self.instances.add(self)

    def update(self):

        self.lifespan_countdown -= 1
        self.radius_switch_countdown -= 1

        if self.lifespan_countdown == 0:

            self.trigger_kill()
            return

        if self.radius_switch_countdown == 0:

            self.radius_switch_countdown = RADIUS_SWITCH_FRAMES
            self.radius = self.next_radius()

        rect = self.rect
        rect.move_ip(self.x_speed, 0)

        ### destroy if hits player...

        player = REFS.states.level_manager.player

        if rect.colliderect(player.rect) and self.confirm_radius(player.rect):

            player.damage(4)
            self.trigger_kill()
            return

    def update_image(self):

        image = self.image

        image.fill(COLORKEY)

        fill_color = self.next_fill_color()
        if fill_color:
            draw_circle(image, fill_color, CENTER, self.radius)

        if self.radius != MIN_RADIUS:

            for lightning_points in (
                LIGHTNING_POINTS_MAP[(self.radius, self.next_lightning_bolt())]
            ):

                draw_lines(image, 'yellow', False, lightning_points, 2)
                draw_lines(image, 'cyan', False, lightning_points, 1)

        draw_circle(image, 'yellow', CENTER, self.radius, 2)

    def trigger_kill(self):

        append_ready_task(partial(PROJECTILES.remove, self))

        self.instances.remove(self)

        # only stop playing if there is no remaining electric globe

        if not self.instances:
            SOUND_MAP['electric_globe_crackling.wav'].stop()

    def confirm_radius(self, colliding_rect):

        if self.radius != MAX_RADIUS:

            area = RADIUS_TO_AREA_MAP[self.radius]
            area.center = self.rect.center

            return (
                area.inflate(-4, -4).colliderect(colliding_rect)
                if area.width >= 8
                else area.colliderect(colliding_rect)
            )

        return True

    def draw(self):
        self.update_image()
        blit_on_screen(self.image, self.rect)
