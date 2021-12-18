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
    """Hero-Wars player class for managing player's heroes."""

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
        """Get the total sum of all player's heroes."""
        return sum(hero.level for hero in self.heroes.values())

    def _message(self, type_: type, message: str, **tokens: Dict[str, Any]):
        """Send a message of type to the player."""
        type_(message).send(self.index, **tokens)

    def invoke_init_callbacks(self):
        """Invoke init callbacks for the current hero and its skills."""
        if self.hero._type_object.init_callback is not None:
            self.hero._type_object.init_callback(self, self.hero)
        for skill in self.hero.skills:
            if skill._type_object.init_callback is not None:
                skill._type_object.init_callback(self, self.hero, skill)

    def invoke_callbacks(self, event_name: str, eargs: Dict[str, Any]):
        """Invoke event callbacks for the current hero and its skills."""
        eargs = eargs.copy()  # Avoid accidentally modifying source dict
        eargs.update({'player': self, 'hero': self.hero})
        self.hero.invoke_callback(event_name, eargs)
        for skill in self.hero.skills:
            eargs['skill'] = skill
            skill.invoke_callback(event_name, eargs)

    chat = partialmethod(_message, SayText2)
    info = partialmethod(_message, HintText)
    warn = partialmethod(_message, TextMsg)
