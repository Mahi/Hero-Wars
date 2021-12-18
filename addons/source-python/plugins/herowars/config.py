# Source.Python imports
from config.manager import ConfigManager
from paths import PLUGIN_PATH, PLUGIN_DATA_PATH


with ConfigManager('herowars/main', cvar_prefix='hw_', indention=0) as main_config:
    heroes_dir = main_config.cvar('heroes_dir', PLUGIN_PATH / 'herowars' / 'heroes', 'Path to load heroes from')

    starting_hero = main_config.cvar('starting_hero', '', 'Default starting hero given to new players')
    starting_hero.Description.append('Leave empty to give the first available hero')


with ConfigManager('herowars/database', cvar_prefix='hw_db_', indention=0) as db_config:
    db_url = {
        'drivername': db_config.cvar('url_drivername', 'sqlite', 'SQLAlchemy drivername'),
        'username': db_config.cvar('url_username', '', 'SQLAlchemy username'),
        'password': db_config.cvar('url_password', '', 'SQLAlchemy password'),
        'host': db_config.cvar('url_host', '', 'SQLAlchemy host'),
        'port': db_config.cvar('url_port', '', 'SQLAlchemy port'),
        'database': db_config.cvar('url_database', PLUGIN_DATA_PATH / 'herowars.db', 'SQLAlchemy database'),
        'query': db_config.cvar('url_query', '', 'SQLAlchemy query'),
    }


with ConfigManager('herowars/xp', cvar_prefix='hw_xp_', indention=0) as xp_config:
    xp_formula_base = xp_config.cvar('formula_base', 80, 'Base XP required to level up')
    xp_formula_per_level = xp_config.cvar('formula_per_level', 15, 'Additional XP each level requires')

    xp_for_event = {
        'player_kill': xp_config.cvar('player_kill', 30, 'XP granted for killing a player'),
        'player_assist': xp_config.cvar('player_assist', 15, 'XP granted for assisting a kill'),
        'bomb_defused': xp_config.cvar('bomb_defused', 30, 'XP granted for defusing the bomb'),
        'bomb_exploded': xp_config.cvar('bomb_exploded', 20, 'XP granted for the bomb exploding'),
        'bomb_planted': xp_config.cvar('bomb_planted', 20, 'XP granted for planting the bomb'),
    }
