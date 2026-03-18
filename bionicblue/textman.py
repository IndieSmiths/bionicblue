
### third-party imports

from pygame import Surface

from pygame.font import Font


### local imports

from .config import FONTS_DIR, COLORKEY



REGULAR_FONT_PATH = FONTS_DIR / 'ark_pixel_12px_latin.ttf'

STYLE_TO_FONT = {
  'regular': REGULAR_FONT_PATH,
}

class FontMap(dict):

    def __missing__(self, key):

        if not isinstance(key, tuple):
            raise TypeError("'key' must be a tuple")

        elif not isinstance(key[0], str):
            raise TypeError("first item must be a str")

        elif not isinstance(key[1], int):
            raise TypeError("second item must be an int")

        elif key[0] not in STYLE_TO_FONT.keys():
            raise ValueError(
                "first item must one of the values inside the tuple:"
                f" {tuple(STYLE_TO_FONT.keys())}"
            )

        elif key[1] <= 0:
            raise ValueError("second item must be a positive integer")

        style, size = key

        return self.setdefault(key, Font(str(STYLE_TO_FONT[style]), size))


FONT_MAP = FontMap()


def render_text(
    text,
    style,
    size,
    padding = 0,
    foreground_color='white',
    background_color='black',
):

    surf = (

        FONT_MAP

        [(style, size)]

        .render(
            text,
            False,
            foreground_color,
            background_color,
        )

        .convert()

    )

    if padding > 0:

        double_padding = padding * 2

        padded_surf = (
            Surface(
                tuple(
                    dimension + double_padding
                    for dimension in surf.get_size()
                )
            ).convert()
        )

        padded_surf.fill(background_color)

        padded_surf.blit(surf, (padding, padding))

        return padded_surf

    else:
        return surf


def update_text_surface(
        obj,
        new_text,
        text_settings,
        pos_to_align='topleft',
    ):
    """Update obj's text surface and rect.

    Also align the new rect with the previous one before replacing.
    """

    ### generate new surf and rect

    new_surf = render_text(new_text, **text_settings)
    new_rect = new_surf.get_rect()

    ### align new rect with old one
    setattr(
        new_rect,
        pos_to_align,
        getattr(obj.rect, pos_to_align),
    )

    ### replace surface and rect with new ones

    obj.image = new_surf
    obj.rect = new_rect


def render_text_with_shadow(text, style, size):

    font = FONT_MAP[(style, size)]

    text_surf = (

        font.render(
            text,
            False,
            'white',
        )

        .convert_alpha()

    )

    text_shadow_surf = (

        font.render(
            text,
            False,
            'black',
        )

        .convert_alpha()

    )

    size = tuple(dimension + 1 for dimension in text_surf.get_size())

    canvas_surf = Surface(size).convert()

    canvas_surf.fill(COLORKEY)
    canvas_surf.set_colorkey(COLORKEY)

    canvas_surf.blit(
        text_shadow_surf,
        (1, 1)
    )

    canvas_surf.blit(
        text_surf,
        (0, 0)
    )

    return canvas_surf
