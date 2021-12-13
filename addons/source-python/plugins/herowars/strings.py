# Source.Python imports
from messages.colors.saytext2 import *
from translations.strings import LangStrings

# Hero-Wars imports
from .utils import create_translation_string


common = LangStrings('herowars/common')
menus = LangStrings('herowars/menus')
messages = LangStrings('herowars/messages')

welcome = create_translation_string(
    f"{GREEN}{{welcome_str}}",
    welcome_str=messages['Welcome'],
)

hero_info = create_translation_string(
    f"{GREEN}{{name}} {WHITE}- {{level_str}}: {ORANGE}{{level}} ",
    f"{WHITE}- {{xp_str}}: {ORANGE}{{xp}}{WHITE}/{ORANGE}{{required_xp}}",
    level_str=common['Level'],
    xp_str=common['XP'],
)

change_hero = create_translation_string(
    f"{{change_hero_str}} {GREEN}{{hero_name}}",
    change_hero_str=messages['Change Hero'],
)

unspent_skill_points = create_translation_string(
    f"{GREEN}{{hero_name}} {WHITE}- {{unspent_skill_points_str}}: {ORANGE}{{skill_points}}",
    unspent_skill_points_str=messages['Unspent Skill Points'],
)
