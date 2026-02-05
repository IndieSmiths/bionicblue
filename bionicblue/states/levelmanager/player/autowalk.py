
### local imports

class AutoWalk:

    def autowalk_control(self):
        pass

    def autowalk_update(self):

        self.rect.move_ip(self.x_speed, 0)

        self.avoid_blocks_horizontally()
        self.react_to_gravity()

        self.frames_walking -= 1

        if not self.frames_walking:

            state_name = anim_name = (
                'idle_right'
                if self.x_speed > 0
                else 'idle_left'
            )

            self.x_speed = 0
            self.set_state(state_name)
            self.aniplayer.switch_animation(anim_name)
