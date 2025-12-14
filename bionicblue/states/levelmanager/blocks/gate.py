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
    """A gate that opens or closes when requested."""

    def __init__(self, midbottom=(0, 0), closed=True):

        self.name = 'gate'
        self.layer_name = 'blocks'
        self.closed = closed
        
        image = self.image = Surface((16, 64)).convert()
        image.set_colorkey(COLORKEY)

        image.fill(
            DOOR_COLOR if closed else COLORKEY
        )

        rect = self.rect = image.get_rect()

        self.colliderect = rect.colliderect

        cover_rect = self.cover_rect = Rect(0, 0, *rect.size)
        cover_rect.y = -rect.height if closed else 0

        self.update = do_nothing

        rect.midbottom = midbottom

        self.open_counter = 0 if closed else rect.height

        if not closed:
            rect.y += -rect.height

    def trigger_opening(self):

        if self.closed and self.update != self.open_the_gate:

            self.update = self.open_the_gate
            SOUND_MAP['arena_door_moving.wav'].play()
            return True

        return False

    def trigger_closing(self):

        if not self.closed and self.update != self.close_the_gate:

            self.update = self.close_the_gate
            SOUND_MAP['arena_door_moving.wav'].play()
            return True

        return False

    def open_the_gate(self):

        if self.open_counter < self.rect.height:

            self.open_counter += 2

            self.rect.y += -2

            self.delta += (0, -2) # so the chunk can keep track of obj's pos

            self.cover_rect.y += 2

            draw_rect(self.image, COLORKEY, self.cover_rect)

        else:
            SOUND_MAP['arena_door_moving.wav'].stop()
            self.update = do_nothing
            self.closed = False

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
            self.update = do_nothing
            self.closed = True

    def draw(self):
        blit_on_screen(self.image, self.rect)
