"""Facility for loading and distributing translated text."""

### standard library imports

from collections import deque

from itertools import takewhile

from textwrap import indent


### local imports

from .config import REFS, LANGUAGE_NAMES_FILEPATH, TRANSLATIONS_DIR

from .ourstdlibs.behaviour import CallList

from .ourstdlibs.pyl import load_pyl



### how each language/locale is called by the locals
LANGUAGE_NAMES_MAP = load_pyl(LANGUAGE_NAMES_FILEPATH)

### module level helper objects

is_space = lambda c: c == ' '

AVAILABLE_LOCALES = set()

INDENTATION = 4 * ' '

_TEMP_LINES = []


### function to create translation namespace

def get_translations_namespace():
    """Load translated texts, gather them in namespace and return it."""

    ### root node
    translations = TranslationNode()

    ###

    ptm = {} # parent tracking map
    lines_deque = deque()

    ###

    translation_sheets_paths = (
        path
        for path in TRANSLATIONS_DIR.iterdir()
        if path.suffix.lower() == '.txt'
    )

    for path in translation_sheets_paths:

        sheet = TranslationNode()
        sheet_name = path.stem
        setattr(translations, sheet_name, sheet)
    
        ptm.clear()

        # parent of node of level 0 have the sheet as their parent node
        ptm[0] = sheet

        ### grab lines
        lines = path.read_text(encoding='utf-8').splitlines()

        ### preprocess lines in case we have a dialogue

        if sheet_name.endswith('dialogue'):

            enumerate_lines_and_extract_action_cueing_data(
                lines,
                sheet_name,
            )

        ### store lines in a deque

        lines_deque.extend(lines)

        identifier_to_be_registered = ''

        watch_out_for_translations = False

        previous_level = 0

        for line in lines:

            ###
            lines_deque.popleft()
            ###

            stripped_line = line.strip()

            ### empty lines or lines starting with '#' are ignored

            if (
                not stripped_line
                or stripped_line[0] == '#'
            ):
                continue

            ### determine current level based on number of spaces
            ### 0 spaces == level 1
            ### 4 spaces == level 2
            ### 8 spaces == level 3
            ### and so on

            spaces = ''.join(takewhile(is_space, line))

            no_of_spaces = len(spaces)

            current_level = (no_of_spaces // 4) + 1

            ###
            remaining_text = line[no_of_spaces:]

            ###

            if current_level < previous_level:
                watch_out_for_translations = False

            ### if we are dealing with translations, simply
            ### store the translation in the parent object
            ### using the locale code as the attribute name

            if watch_out_for_translations:

                locale, _, translation = remaining_text.partition(' ')

                # locale

                formatted_locale = (
                    locale
                    .lower()           # ensure lowercase
                    .replace('-', '_') # ensure '-' is replaced with '_'
                )
                
                # register locale
                AVAILABLE_LOCALES.add(formatted_locale)

                # store translation in parent's translation map

                parent = ptm[current_level-2]

                tmap = (
                    parent._translation_map
                    [identifier_to_be_registered]
                )

                tmap[formatted_locale] = translation

            else:

                identifier_to_be_registered = ''

                # peek into next lines to see if we are dealing
                # with translations or identifiers
                #
                # if dealing with translations, we use the leaf
                # class, otherwise we use the node class

                for deque_line in lines_deque:

                    stripped_deque_line = deque_line.strip()

                    if (
                        not stripped_deque_line
                        or stripped_deque_line[0] == '#'
                    ):
                        continue

                    if ' ' in stripped_deque_line:
                        watch_out_for_translations = True

                    break

                parent = ptm[current_level-1]

                if watch_out_for_translations:

                    if not parent._has_translation_map:

                        parent._translation_map = {}
                        parent._has_translation_map = True

                    parent._translation_map[remaining_text] = {}
                    identifier_to_be_registered = remaining_text

                else:

                    # instantiate and store object in parent's attribute

                    node = TranslationNode()
                    setattr(parent, remaining_text, node)

                    # store it as a parent obj
                    ptm[current_level] = node

            ### mark current level as the previous level
            previous_level = current_level

        ### clear the lines deque
        lines_deque.clear()

    ### clear the helper map
    ptm.clear()

    ### return namespace
    return translations


### helper class;
###
### simple class that falls back to en_us translation
### when another locale fails when retrieved

class TranslationNode():

    # placeholder attribute (to be set within the user preferences
    # subpackage)
    _user_prefs = None

    def __init__(self):
        self._has_translation_map = False

    def __getattr__(self, attr_name):

        if (
            not self._has_translation_map
            or attr_name not in self._translation_map
        ):

            raise AttributeError(
                f"TranslationNode obj doesn't have '{attr_name}' attribute."
            )

        return (
            self._translation_map[attr_name]
            .get(self._user_prefs['LOCALE'], 'en_us')
        )


### helper function

def enumerate_lines_and_extract_action_cueing_data(lines, file_stem):

    _TEMP_LINES.extend(lines)

    lines.clear()

    line_number = 0
    line_number_attr = ''

    action_cueing_data = {}
    character_names = set() 

    for line in _TEMP_LINES:

        ### if a line is not empty, process it further

        if line:

            ## if line starts with this substring, it is a directive
            ## to indicate an action should be executed at that time
            ## (or near that time)

            if line.startswith('# action:'):

                action_id = line.replace('# action:', '').strip()

                cue = (

                    (line_number_attr, 'after')
                    if line_number_attr

                    else ('line_000', 'before')

                )

                action_cueing_data[action_id] = cue

            ## otherwise, if first char is not '#' or space, it means this
            ## line contains the name of a character, marking the start of
            ## a dialogue line, so we add the line number attribute and
            ## make sure the name is in the character_names set

            elif line[0] not in '# ':

                ## add line number

                line_number_attr = f'line_{line_number:>03}'
                lines.append(line_number_attr)

                ## store character name (stripping it just in case)
                character_names.add(line.strip())

                ## increment count
                line_number += 1

            ## the line itself is indented by one level
            line = indent(line, INDENTATION)

        ### all lines are added back, regardless of whether they are
        ### empty or not
        lines.append(line)

    ### at the end, we clear the temp list
    _TEMP_LINES.clear()

    ###

    dialogue_name = file_stem.replace('_dialogue', '')

    REFS.dialogue_action_cueing_data[dialogue_name] = action_cueing_data
    REFS.dialogue_character_names_set_map[dialogue_name] = character_names


### translation namespace
TRANSLATIONS = get_translations_namespace()

### collections of callbacks to reset text surfaces in response to
### changing language
on_language_change = CallList()
