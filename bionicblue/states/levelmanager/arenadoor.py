
### standard library import
from functools import partial


### third-party imports

from pygame import Surface, Rect

from pygame.draw import rect as draw_rect


### local import

from ...config import REFS, COLORKEY

from ...pygamesetup.constants import blit_on_screen

from ...ourstdlibs.behaviour import do_nothing

from .common import append_task



DOOR_COLOR = 'grey'


class ArenaDoor:

    def __init__(self, name):

        self.name = name
        self.layer_name = 'middleprops'
        
        image = self.image = Surface((16, 64)).convert()
        image.set_colorkey(COLORKEY)

        self.rect = image.get_rect()
        self.inflating_rect = Rect(0, 0, 16, 1)

    def prepare(self):

        self.image.fill(DOOR_COLOR)
        self.inflating_rect.height = 1
        self.inflating_rect.centery = self.rect.height // 2

        self.update = self.check_approaching_player
        self.draw = self.normal_draw

    def check_approaching_player(self):

        player_rect = REFS.states.level_manager.player.rect

        if self.rect.move(-64, 0).colliderect(player_rect):

            self.update = self.check_advancing_player
            self.draw = self.opening_draw

            REFS.states.level_manager.passing_through_arena_door(self.name)

    def check_advancing_player(self):

        player_rect = REFS.states.level_manager.player.rect

        if self.rect.move(64, 0).colliderect(player_rect):

            self.update = do_nothing
            self.draw = self.closing_draw

    def normal_draw(self):
        blit_on_screen(self.image, self.rect)

    def opening_draw(self):

        image = self.image

        draw_rect(image, COLORKEY, self.inflating_rect)

        blit_on_screen(image, self.rect)

        if self.inflating_rect.height < self.rect.height:
            self.inflating_rect.inflate_ip(0, 4)

    def closing_draw(self):

        image = self.image
        image.fill(DOOR_COLOR)

        draw_rect(image, COLORKEY, self.inflating_rect)
        self.inflating_rect.inflate_ip(0, -4)

        blit_on_screen(image, self.rect)

        if self.inflating_rect.height == 1:

            image.fill(DOOR_COLOR)
            self.draw = self.normal_draw

            append_task(
                partial(
                    REFS.states.level_manager.replace_arena_door,
                    self.name,
                )
            )



DOOR_1 = ArenaDoor('door_1')
DOOR_2 = ArenaDoor('door_2')

class BlockDoor:

    def __init__(self):

        self.rect = DOOR_1.rect.copy()
        self.colliderect = self.rect.colliderect

        self.image = Surface(self.rect.size).convert()
        self.image.fill(DOOR_COLOR)

        self.layer_name = 'blocks'

    def update(self): pass

    def draw(self):
        blit_on_screen(self.image, self.rect)


BLOCK_DOOR_1 = BlockDoor()
BLOCK_DOOR_2 = BlockDoor()
