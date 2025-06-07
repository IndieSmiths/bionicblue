
### standard library import
from functools import partial


### third-party imports

from pygame import Surface, Rect

from pygame.draw import circle as draw_circle

from pygame.math import Vector2


### local imports

from .....config import REFS, COLORKEY#, SOUND_MAP

from .....pygamesetup.constants import (
    SCREEN_RECT,
    blit_on_screen,
    msecs_to_frames,
)

from .....ourstdlibs.mathutils import get_rect_from_points

from ...common import (
    PROJECTILES,
    BLOCKS_NEAR_SCREEN,
    append_task,
)



def _get_watcher_shot_surf():

    surf = Surface((7, 7)).convert()
    surf.fill(COLORKEY)
    surf.set_colorkey(COLORKEY)
    rect = surf.get_rect()
    draw_circle(surf, 'white', rect.center, 3)
    return surf

SHOT_SURF = _get_watcher_shot_surf()

_MSECS_BEFORE_VANISHING = 3000
FRAMES_BEFORE_VANISHING = msecs_to_frames(_MSECS_BEFORE_VANISHING)


class WatcherShot:

    def __init__(self, watcher_center, player_center):

        self.aim_point = get_aim_point(watcher_center, player_center)

        self.image = SHOT_SURF

        self.art_rect = self.image.get_rect()

        rect = self.rect = self.art_rect.copy()
        rect.size = (4, 4)
        self.colliderect = rect.colliderect

        self.player = REFS.states.level_manager.player

        self.vector = Vector2(watcher_center)
        self.vector.move_towards_ip(self.aim_point, 4)

        rect.center = self.vector

        self.life_countdown = FRAMES_BEFORE_VANISHING

    def trigger_kill(self):
        append_task(partial(PROJECTILES.remove, self))

    def update(self):

        self.life_countdown -= 1
        if not self.life_countdown:
            self.trigger_kill()
            return

        center = self.rect.center

        diff = self.vector - center

        if diff:

            self.vector.update(center)
            self.aim_point -= diff

        self.vector.move_towards_ip(self.aim_point, 4)
        self.rect.center = self.vector

        colliderect = self.colliderect

        if not colliderect(SCREEN_RECT):

            self.trigger_kill()
            return

        for block in BLOCKS_NEAR_SCREEN:

            if colliderect(block.rect):

                self.trigger_kill()
                return

        if colliderect(self.player.rect):

            self.player.damage(3)
            self.trigger_kill()
            return

    def draw(self):
        self.art_rect.center = self.rect.center
        blit_on_screen(self.image, self.art_rect)


corner_names = (
    'topleft',
    'topright',
    'bottomleft',
    'bottomright',
)

opposite_corner_map = {
    'topleft': 'bottomright',
    'topright': 'bottomleft',
    'bottomright': 'topleft',
    'bottomleft': 'topright',
}

def get_aim_point(watcher_center, player_center):

    wx, wy = watcher_center
    px, py = player_center

    if wx == px:

        if wy < py:
            ty = py + 10000
        else:
            ty = py - 10000

        aim_point = (px, ty)

    elif wy == py:

        if wx < px:
            tx = px + 10000
        else:
            tx = px - 10000

        aim_point = (tx, py)

    else:

        rect = Rect(get_rect_from_points(watcher_center, player_center))

        for corner_name in corner_names:

            if watcher_center == getattr(rect, corner_name):

                watcher_pos_name = corner_name
                break

        rect.w *= 10
        rect.h *= 10

        setattr(rect, watcher_pos_name, watcher_center)

        player_pos_name = opposite_corner_map[watcher_pos_name]
        aim_point = getattr(rect, player_pos_name)

    return Vector2(aim_point)
