# Python imports
from collections import OrderedDict
from functools import partialmethod
from typing import Any, Dict

# Source.Python imports
from messages import HintText, SayText2, TextMsg

# Custom package imports
import easyplayer

# Hero-Wars imports
from .entities import Hero


class Player(easyplayer.Player):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heroes: OrderedDict[str, Hero] = OrderedDict()
        self._hero: Hero = None

    @property
    def hero(self) -> Hero:
        return self._hero

    @hero.setter
    def hero(self, value: Hero):
        if value.key not in self.heroes:
            raise ValueError(f'Hero {value.name} not owned by player {self.name}')
        self._hero = value

    def total_level(self) -> int:
        return sum(hero.level for hero in self.heroes.values())

    def _message(self, type_: type, message: str, **tokens: Dict[str, Any]):
        type_(message).send(self.index, **tokens)

    def _init_hero(self):
        if self.hero.type_object.init_callback is not None:
            self.hero.type_object.init_callback(self, self.hero)
        for skill in self.hero.skills:
            if skill.type_object.init_callback is not None:
                skill.type_object.init_callback(self, self.hero, skill)

    chat = partialmethod(_message, SayText2)
    info = partialmethod(_message, HintText)
    warn = partialmethod(_message, TextMsg)
