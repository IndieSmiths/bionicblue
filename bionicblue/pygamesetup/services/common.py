"""Common utilities for sibling modules."""



def trim_from_msecs(friendly_delta):

    if 'msecs' not in friendly_delta:
        return friendly_delta

    text_before_msecs = friendly_delta[:friendly_delta.index('msecs')]

    return (

        text_before_msecs[:text_before_msecs.rindex(' ')]

        if any(

            c == ' '
            for c in reversed(text_before_msecs)

        )

        else friendly_delta

    )
