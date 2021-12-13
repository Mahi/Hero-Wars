# Site-Package imports
from paths import PLUGIN_DATA_PATH, PLUGIN_PATH

# Hero-Wars imports
from .utils import flatten

SOLO_PLAYER_EVENTS = {
    'player_spawn',
    'player_disconnect',
    'player_jump',
}

CUSTOM_PLAYER_EVENTS = {
    'player_ultimate',
    'player_ability',
    'player_change_hero',
    'hero_level_up',  # It's still an event with a player actor
    'pre_player_attack',
    'pre_player_victim',
}

DUO_PLAYER_EVENTS = {
    'player_death': ('player_death', 'player_kill'),
    'player_hurt': ('player_victim', 'player_attack'),
}

ALL_EVENTS = SOLO_PLAYER_EVENTS | CUSTOM_PLAYER_EVENTS | set(flatten(DUO_PLAYER_EVENTS.values()))


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
