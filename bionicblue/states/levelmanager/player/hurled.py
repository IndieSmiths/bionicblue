
### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,

    JOYBUTTONDOWN,

)


### local imports

from ....config import REFS, quit_game

from ....pygamesetup import SERVICES_NS

from ....pygamesetup.constants import GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS

from ....pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ....userprefsman.main import GAMEPAD_CONTROLS

from ..common import BLOCKS_NEAR_SCREEN



class Hurled:

    def hurled_control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    REFS.pause()

                elif event.key == K_RETURN:
                    REFS.pause()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    REFS.pause()

            elif event.type == QUIT:
                quit_game()

    def hurled_update(self):

        rect = self.rect

        rect.move_ip(self.x_speed, 0)

        ## react to blocks horizontally

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):

                if rect.left < block.rect.left:
                    rect.right = block.rect.left

                else:
                    rect.left = block.rect.right

                self.x_speed = self.y_speed = 0
                self.damage(5)
                return

        ## react to blocks vertically

        rect.move_ip(0, self.y_speed)

        self.midair = True

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):

                if rect.bottom < block.rect.bottom:

                    rect.bottom = block.rect.top
                    self.midair = False

                    if hasattr(block, 'touched_top'):
                        block.touched_top(self)

                else:
                    rect.top = block.rect.bottom

                self.x_speed = self.y_speed = 0
                self.damage(5)
                return
