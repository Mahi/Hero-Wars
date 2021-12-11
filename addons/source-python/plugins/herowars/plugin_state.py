# Python imports
from dataclasses import dataclass
from typing import Dict

# Source.Python imports
from players.dictionary import PlayerDictionary

# Hero-Wars imports
from .entities.type_objects import HeroType


@dataclass
class PluginState:
    hero_types: Dict[str, HeroType]
    players: PlayerDictionary
