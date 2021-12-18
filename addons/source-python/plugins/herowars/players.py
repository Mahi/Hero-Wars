# Python imports
from typing import Dict

# Source.Python imports
from players.dictionary import PlayerDictionary

# Hero-Wars imports
from . import config, database, strings
from .entities import Hero, HeroType
from .hero_types import hero_types
from .player import Player
from .utils import first


def get_starting_hero_type() -> HeroType:
    """Get the starting hero type object for new players."""
    starting_hero_key = config.starting_hero.get_string()
    if not starting_hero_key:
        return first(hero_types)
    return hero_types[starting_hero_key]


def init_player(player_index: int) -> Player:
    """Create and initialize a new player.

    Intended to be used automatically by a PlayerDictionary.
    """
    player = Player(player_index)
    exists = database.load_player_data(player)
    if not player.hero:

        # Prior data might still exist, just particular hero has been deleted
        if player.heroes:
            player.hero = first(player.heroes)

        # Give one hero by default
        else:
            hero = Hero(get_starting_hero_type())
            player.heroes[hero.key] = hero
            player.hero = hero

    # Create player hero's skills
    player.hero._create_skills()
    if exists:
        database.load_skills_data(player.hero)

    else:
        # Pre-emptively insert into database to allow update operations 
        # in the future, without having to query for existance every time
        database.create_player_data(player)
        player.chat(strings.welcome)

    # Call init_callbacks for heroes and skills
    player.invoke_init_callbacks()
    return player


player_dict: Dict[str, Player] = PlayerDictionary(init_player)
