
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

from ....pygamesetup.gamepadservices.common import GAMEPAD_NS

from ....pygamesetup.constants import GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS

from ....userprefsman.main import GAMEPAD_CONTROLS



class ScriptedActing:

    def scripted_acting_control(self):
        
        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    REFS.pause()

                elif event.key == K_RETURN:
                    REFS.pause()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    REFS.pause()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def scripted_acting_update(self):

        self.rect.move_ip(self.x_speed, 0)

        self.avoid_blocks_horizontally()
        self.react_to_gravity()

        if self.anim_blend:

            anim_blend = self.anim_blend
            self.aniplayer.blend(f'+{anim_blend}')

        self.scripted_frames_count -= 1

        if not self.scripted_frames_count:

            if self.scripted_actions_deque:

                self._set_next_scripted_action(
                    self.scripted_actions_deque.popleft()
                )

            else:

                if self.orientation_to_face:

                    state_name = anim_name = (
                        'idle_left'
                        if self.orientation_to_face == 'left'
                        else 'idle_right'
                    )

                else:

                    state_name = anim_name = (
                        'idle_left'
                        if 'left' in self.aniplayer.anim_name
                        else 'idle_right'
                    )

                self.x_speed = 0
                self.set_state(state_name)
                self.aniplayer.switch_animation(anim_name)
