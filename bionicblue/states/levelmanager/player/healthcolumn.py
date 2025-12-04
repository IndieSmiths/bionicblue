
### standard library imports

from math import tau

from itertools import cycle

from collections import deque


### third-party imports

from pygame import Surface, Rect

from pygame.draw import (
    arc as draw_arc,
    circle as draw_circle,
    line as draw_line,
    polygon as draw_polygon,
    rect as draw_rect,
)

from pygame.math import Vector2


### local imports

from ....config import SURF_MAP, SOUND_MAP, COLORKEY, MOTION_PATHS_DIR

from ....pygamesetup.constants import SCREEN, blit_on_screen, msecs_to_frames

from ....ourstdlibs.behaviour import do_nothing

from ....ourstdlibs.pyl import load_pyl

from ....pointsman2d.create import yield_circle_points



### XXX use variables to indicate the role of the named colors
### used


_HEALTH_INCREASE_MSECS = 5000
HEALTH_INCREASE_FRAMES = msecs_to_frames(_HEALTH_INCREASE_MSECS)

NEXT_INCREASE_TWINKLING_COLOR = cycle(
    (('red',) * 15)
    + (('brown',) * 15)
).__next__

### star points

OUTER_STAR_RADIUS = 8
INNER_STAR_RADIUS = 4

INNER_RADIUS_PROPORTION = INNER_STAR_RADIUS / OUTER_STAR_RADIUS

NO_OF_STAR_TIPS = 5
NO_OF_ROTATIONS = 6

NO_OF_CIRCLE_POINTS = NO_OF_STAR_TIPS * NO_OF_ROTATIONS

def _get_all_possible_rotated_star_points():

    _circle_points_deque = deque(

        yield_circle_points(
            quantity=NO_OF_CIRCLE_POINTS,
            radius=OUTER_STAR_RADIUS,
        )

    )

    ###
    points_of_each_rotated_star = deque()

    center = Vector2(0, 0)

    for _ in range(NO_OF_ROTATIONS):

        star_points = []
        append_point = star_points.append

        star_tip = Vector2(_circle_points_deque[0])

        for _ in range(NO_OF_STAR_TIPS):

            _circle_points_deque.rotate(-NO_OF_ROTATIONS)

            next_star_tip = Vector2(_circle_points_deque[0])

            _midpoint = star_tip.lerp(next_star_tip, .5)
            star_inner_point = center.lerp(_midpoint, INNER_RADIUS_PROPORTION)

            append_point(star_inner_point)
            append_point(next_star_tip)

            star_tip = next_star_tip


        points_of_each_rotated_star.append(star_points)

        _circle_points_deque.rotate(-1)

    _circle_points_deque.clear()

    return points_of_each_rotated_star


POINTS_OF_EACH_ROTATED_STAR = _get_all_possible_rotated_star_points()

### offset just so the green outline covering the head's icon doesn't starts
### to be drawing from 0, but rather from the angle that starts more or less
### at the topleft corner of the head
ARC_OFFSET = tau * .35


class HealthColumn:

    def __init__(self):

        ### store values/objects

        self.full_health = 32
        self.health = 32

        self.head_surf = SURF_MAP['blue_shooter_man_head.png']
        self.head_rect = self.head_surf.get_rect()

        ### create surface and subelements to help manage
        ### health and what is drawn depending on its value

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

        self.inflated_bg_rect = hbg.inflate(4, 4)
        self.inflated_bg_rect_height = self.inflated_bg_rect.height
        self.inflated_bg_rect_bottom = self.inflated_bg_rect.bottom

        draw_rect(image, 'grey80', self.inflated_bg_rect)
        draw_circle(image, 'grey80', head_rect.center, 7)

        self.draw_health_indicator_bar()

        image.blit(self.head_surf, head_rect)

        self.rect.topleft = (3, 28)

        self.update = do_nothing
        self.draw = self.normal_draw

        ### store an inflated head rect for later use
        self.inflated_head_rect = head_rect.inflate(8, 8)

        ### store rect of height 1 and same width as health_bg rect

        self.hbg_height_one = hbg.copy()
        self.hbg_height_one.height = 1

        ### load and offset spiral points representing a motion path
        ### so the spiral ends on the head

        offset = Vector2(head_rect.center) + self.rect.topleft

        self.spiral_points = tuple(

            point + offset
            for point in load_pyl(MOTION_PATHS_DIR / 'star_spiral.pos')

        )

        ### also create list for temporarily storing points of a star
        ### to be drawn along the path
        self.star_points = []

    def damage(self, amount):

        self.health = min(max(self.health - amount, 0), self.full_health)

        self.health_fg.height = self.health
        self.health_fg.bottom = self.health_bg.bottom

        self.draw_health_indicator_bar()

    def draw_health_indicator_bar(self):

        draw_rect(self.image, 'brown', self.health_bg)
        draw_rect(self.image, 'gold', self.health_fg)

    def is_depleted(self):
        return self.health <= 0

    def trigger_health_recovery(self):

        self.update = self.advance_spiral_animation
        self.draw = self.spiral_draw
        self.next_point = iter(self.spiral_points).__next__

    def advance_spiral_animation(self):

        try: 
            self.point = self.next_point()

        except StopIteration:

            SOUND_MAP['star_landing_on_healthbar.wav'].play()

            self.image.fill(COLORKEY)

            self.draw_health_indicator_bar()
            self.image.blit(self.head_surf, self.head_rect)

            self.bar_bg_percentage = 0

            self.update = self.advance_recovery_animation
            self.draw = self.normal_draw

    def advance_recovery_animation(self):

        self.bar_bg_percentage += 1
        image = self.image

        if self.bar_bg_percentage <= 100:

            image.fill(COLORKEY)

            unit_interval_percentage = self.bar_bg_percentage / 100

            ### draw bar bg percentage

            ihbg = self.inflated_bg_rect
            ihbg.height = self.inflated_bg_rect_height * unit_interval_percentage
            ihbg.bottom = self.inflated_bg_rect_bottom

            draw_rect(image, 'springgreen', self.inflated_bg_rect)

            ### draw head bg percentage

            draw_circle(image, 'springgreen', self.head_rect.center, 7)

            start_angle = 0 + ARC_OFFSET
            stop_angle = (tau * (1 - unit_interval_percentage)) + ARC_OFFSET

            draw_arc(

                image,
                COLORKEY,
                self.inflated_head_rect,
                start_angle,
                stop_angle,
                8,

            )

            ### draw health indicator and head

            self.draw_health_indicator_bar()
            image.blit(self.head_surf, self.head_rect)

        else:

            self.update = self.check_recovery
            self.health_increase_countdown = HEALTH_INCREASE_FRAMES

    def check_recovery(self):

        if 0 < self.health < self.full_health:

            self.health_increase_countdown -= 1

            if self.health_increase_countdown == 0:

                self.damage(-1)
                self.health_increase_countdown = HEALTH_INCREASE_FRAMES

                self.draw_health_indicator_bar()

            else:

                hbg_height_one = self.hbg_height_one
                top = hbg_height_one.bottom = self.health_fg.top

                color = NEXT_INCREASE_TWINKLING_COLOR()

                draw_line(
                    self.image,
                    color,
                    (hbg_height_one.left, top),
                    (hbg_height_one.right-1, top),
                    1,
                )

    def normal_draw(self):
        blit_on_screen(self.image, self.rect)

    def spiral_draw(self):

        ### draw health bar
        blit_on_screen(self.image, self.rect)

        ### grab star points and perform other setups

        offset = self.point
        star_points = self.star_points

        star_points.extend(point + offset for point in  POINTS_OF_EACH_ROTATED_STAR[0])
        POINTS_OF_EACH_ROTATED_STAR.rotate(-1)

        ### draw star

        draw_polygon(
            SCREEN,
            'yellow',
            star_points,
        )

        ### clear the list of star points so we can reuse it
        star_points.clear()
