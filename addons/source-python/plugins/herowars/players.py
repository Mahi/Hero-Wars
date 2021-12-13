# Python imports
from typing import Dict

# Source.Python imports
from players.dictionary import PlayerDictionary

# Hero-Wars imports
from . import database, strings
from .constants import DEFAULT_HERO_KEY
from .entities import Hero, HeroType
from .hero_types import hero_types
from .player import Player
from .utils import first


def _get_default_hero_type() -> HeroType:
    if DEFAULT_HERO_KEY is None:
        return first(hero_types)
    return hero_types[DEFAULT_HERO_KEY]


def _init_player(player_index: int) -> Player:
    player = Player(player_index)
    exists = database.load_player_data(player)
    if not player.hero:

        # Prior data might still exist, just particular hero has been deleted
        if player.heroes:
            player.hero = first(player.heroes)

        # Give one hero by default
        else:
            hero = Hero(_get_default_hero_type())
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


player_dict: Dict[str, Player] = PlayerDictionary(_init_player)
