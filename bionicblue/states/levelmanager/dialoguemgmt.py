"""Facility with class extension for managing dialogues."""

### third-party imports

from pygame.display import update as update_screen


### local imports

from ...pygamesetup.constants import SCREEN

from .common import (

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,

    PROJECTILES,
    FRONT_PROPS,
    HEALTH_COLUMNS,

    CHUNKS,

    VICINITY_RECT,

    scrolling,
    scrolling_backup,

    execute_tasks,
    update_chunks_and_layers,

)



class DialogueManagement:
    """Methods to help drive dialogue encounters."""

    def enter_dialogue(self, dialogue_name):

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

        self.control = self.dialogue_control
        self.update = self.dialogue_update
        self.draw = self.dialogue_draw

        ... ### TODO set actions for given dialogue

    def exit_dialogue(self):

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

        self.enable_overall_tracking_for_camera()
        self.enable_feet_tracking_for_camera()

    def dialogue_control(self):
        ...

    def dialogue_update(self):

        self.player.update()

        ### backup scrolling
        scrolling_backup.update(scrolling)

        for prop in BACK_PROPS_NEAR_SCREEN:
            prop.update()

        for prop in MIDDLE_PROPS_NEAR_SCREEN:
            prop.update()

        for block in BLOCKS_NEAR_SCREEN:
            block.update()

        for actor in ACTORS_NEAR_SCREEN:
            actor.update()

        for projectile in PROJECTILES:
            projectile.update()

        for prop in FRONT_PROPS:
            prop.update()

        self.update_actions()

    def update_actions(self):
        """Drive actions toward completion, so dialogue can end."""

    def dialogue_draw(self):
        """Draw level elements and dialogue elements on top."""

        SCREEN.fill(self.bg_color)

        for prop in BACK_PROPS_NEAR_SCREEN:
            prop.draw()

        for prop in MIDDLE_PROPS_NEAR_SCREEN:
            prop.draw()

        for projectile in PROJECTILES:
            projectile.draw()

        for block in BLOCKS_NEAR_SCREEN:
            block.draw()

        self.player.draw()

        for actor in ACTORS_NEAR_SCREEN:
            actor.draw()

        for prop in FRONT_PROPS:
            prop.draw()

        self.draw_dialogue_elements(self)

        update_screen()

    def draw_dialogue_elements(self):
        """Draw dialogue elements (as needed).

        "As needed" means that dialogue may have intervals where nothing is
        said, so no dialogue element is drawn during that interval.
        """
