
### third-party imports

from pygame import Surface

from pygame.draw import rect as draw_rect


### local imports

from ...pygamesetup.constants import blit_on_screen

from ...textman import render_text

from ...ourstdlibs.behaviour import do_nothing


def get_message_surf():

    surfs = tuple(

        render_text(text, 'regular', 12, 0, 'white', 'blue')

        for text in (
            "End of prototype/demo :(",
            " ",
            "Please, consider supporting this",
            "project:",
            "https://indiesmiths.com/donate",
            " ",
            "For more info:",
            "https://bionicblue.indiesmiths.com",
        )

    )

    padding = 6

    height = sum(surf.get_height() for surf in surfs) + padding
    width = max(surf.get_width() for surf in surfs) + padding

    image = Surface((width, height)).convert()
    image.fill('blue')

    x = y = 3

    y_increment = surfs[0].get_height()

    for surf in surfs:

        image.blit(surf, (x, y))
        y += y_increment

    draw_rect(image, 'white', image.get_rect(), 1)

    return image

message = type('Object', (), {})()

message.image = get_message_surf()
message.rect = message.image.get_rect()
message.rect.move_ip(1026, 50)
message.update = do_nothing
message.draw = lambda: blit_on_screen(message.image, message.rect)
