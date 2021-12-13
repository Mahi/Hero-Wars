# Site-Package imports
from paths import PLUGIN_DATA_PATH, PLUGIN_PATH

# Custom packages
from easyevents import DUO_PLAYER_GAME_EVENT_MAP, SOLO_PLAYER_GAME_EVENTS

# Hero-Wars imports
from .utils import flatten


CUSTOM_PLAYER_EVENTS = {
    'player_ultimate',
    'player_ultimate_end',
    'player_ability',
    'player_ability_end',
    'player_change_hero',
    'hero_level_up',  # It's still an event with a player actor
    'pre_player_attack',
    'pre_player_victim',
}

ALL_EVENTS = CUSTOM_PLAYER_EVENTS | set(flatten(DUO_PLAYER_GAME_EVENT_MAP.values())) | SOLO_PLAYER_GAME_EVENTS


# XP Values

BASE_XP = 80
XP_PER_LEVEL = 15
XP_ON_KILL = 50
BONUS_WEAPON_XP = {
    # TODO
}

# Misc

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
