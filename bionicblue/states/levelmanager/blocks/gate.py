"""Facility for multi-purpose gate."""

### third-party imports

from pygame import Surface, Rect

from pygame.draw import rect as draw_rect


### local import

from ....config import REFS, SOUND_MAP, COLORKEY

from ....pygamesetup.constants import blit_on_screen

from ....ourstdlibs.behaviour import do_nothing



DOOR_COLOR = 'grey'


class Gate:

    def __init__(self, name):

        self.name = name
        self.layer_name = 'blocks'
        
        image = self.image = Surface((16, 64)).convert()
        image.set_colorkey(COLORKEY)

        rect = self.rect = image.get_rect()
        self.colliderect = rect.colliderect
        self.cover_rect = rect.move(0, -rect.height)
        self.open_counter = 0

        self.update = do_nothing

    def prepare(self):

        self.image.fill(DOOR_COLOR)
        self.update = self.check_approaching_player

    def trigger_opening(self):
        self.update = self.open_the_gate
        SOUND_MAP['arena_door_moving.wav'].play()

    def trigger_closing(self):
        self.update = self.close_the_gate
        SOUND_MAP['arena_door_moving.wav'].play()

    def open_the_gate(self):

        if self.open_counter < self.rect.height:

            self.open_counter += 2

            self.rect.y += -2

            self.delta += (0, -2) # so the chunk can keep track of obj's pos

            self.cover_rect.y += 2

            draw_rect(self.image, COLORKEY, self.cover_rect)

        else:
            SOUND_MAP['arena_door_moving.wav'].stop()

    def close_the_gate(self):

        if self.open_counter > 0:

            self.image.fill(DOOR_COLOR)

            self.open_counter += -2

            self.rect.y += 2

            self.delta += (0, 2) # so the chunk can keep track of obj's pos

            self.cover_rect.y += -2

            draw_rect(self.image, COLORKEY, self.cover_rect)

        else:

            SOUND_MAP['arena_door_moving.wav'].stop()

    def draw(self):
        blit_on_screen(self.image, self.rect)
