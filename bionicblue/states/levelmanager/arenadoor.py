
### third-party imports

from pygame import Surface, Rect

from pygame.draw import rect as draw_rect


### local import

from ...config import REFS, SOUND_MAP, COLORKEY

from ...pygamesetup.constants import blit_on_screen

from ...ourstdlibs.behaviour import do_nothing



DOOR_COLOR = 'grey'


class ArenaDoor:

    def __init__(self, name):

        self.name = name
        self.layer_name = 'blocks'
        
        image = self.image = Surface((16, 64)).convert()
        image.set_colorkey(COLORKEY)

        rect = self.rect = image.get_rect()
        self.colliderect = rect.colliderect
        self.cover_rect = rect.move(0, -rect.height)
        self.open_counter = 0

        self.door_closing_distance = 90 if name == 'door_1' else 64

    def prepare(self):
        self.image.fill(DOOR_COLOR)
        self.update = self.check_approaching_player

    def check_approaching_player(self):

        player_rect = REFS.states.level_manager.player.rect

        if self.rect.move(-64, 0).colliderect(player_rect):

            self.update = self.check_advancing_player
            SOUND_MAP['arena_door_moving.wav'].play()

            # this must always be the last line in this block,
            # as it may raise an expected exception
            REFS.states.level_manager.passing_through_arena_door(self.name)

    def check_advancing_player(self):
        
        self.open_the_gate()

        player_rect = REFS.states.level_manager.player.rect

        if (self.rect.left + self.door_closing_distance) <= player_rect.left:
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
            self.update = do_nothing

    def draw(self):
        blit_on_screen(self.image, self.rect)


DOOR_1 = ArenaDoor('door_1')
DOOR_2 = ArenaDoor('door_2')


