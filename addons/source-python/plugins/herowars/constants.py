# Site-Package imports
from paths import PLUGIN_DATA_PATH, PLUGIN_PATH

# Custom packages
from easyplayer.events import DEFAULT_GAME_EVENT_CONVERSIONS


CUSTOM_PLAYER_EVENTS = {
    'player_ultimate',
    'player_ultimate_end',
    'player_ability',
    'player_ability_end',
    'player_change_hero',
    'hero_level_up',
    'pre_player_attack',
    'pre_player_victim',
}


ALL_PLAYER_EVENTS = CUSTOM_PLAYER_EVENTS | {
    conversion.event_name
    for conversions in DEFAULT_GAME_EVENT_CONVERSIONS.values()
    for conversion in conversions
}


BASE_XP = 80
XP_PER_LEVEL = 15
XP_VALUES = {
    'player_kill': 30,
    'player_assist': 15,
    'bomb_defused': 30,
    'bomb_exploded': 20,
    'bomb_planted': 20,
}


DEFAULT_HERO_KEY = None  # If None, use first hero (basically random)
HEROES_PATH = PLUGIN_PATH / 'herowars' / 'heroes'
DATABASE_URL = {
    'drivername': 'sqlite',
    'username': '',
    'password': '',
    'host': '',
    'port': None,
    'database': PLUGIN_DATA_PATH / 'herowars.db',
    'query': '',
}
