# Python imports
import collections
import math
from typing import Any, Callable, Dict, Optional, Tuple

# Source.Python imports
from effects.base import TempEntity
from listeners.tick import Repeat
from messages.base import HudMsg
from messages.colors.saytext2 import GREEN, ORANGE, WHITE
from messages import SayText2
from players.entity import Player
from translations.strings import TranslationStrings

# Hero-Wars imports
from ..utils import Cooldown, create_translation_string
from .type_objects import EntityType


def type_object_property(attr_name: str) -> property:
    """Property that fetches the attribute from a type object."""
    def fget(self):
        return getattr(self._type_object, attr_name)
    return property(fget)


class Entity:
    """Base class for all Hero-Wars entities.

    Implements leveling mechanics, type_object support,
    event callbacks, visual effects, and more.

    Requires an entity type object to function.
    """

    def __init__(self, type_object: EntityType, level: int=0, *, db_id: Optional[int]=None):
        self._type_object = type_object
        self._level = level
        self._db_id = db_id
        self._temp_entities: Dict[str, Tuple[TempEntity, str]] = {}
        self._cooldowns = collections.defaultdict(Cooldown)

    key: str = type_object_property('key')
    author: Optional[str] = type_object_property('author')
    required_level: int = type_object_property('required_level')
    max_level: int = type_object_property('max_level')
    name: TranslationStrings = type_object_property('name')
    description: TranslationStrings = type_object_property('description')

    strings: Dict[str, TranslationStrings] = type_object_property('strings')
    init_callback: Optional[Callable] = type_object_property('init_callback')
    event_callbacks: Dict[str, Callable] = type_object_property('event_callbacks')
    effects: Dict[str, Any] = type_object_property('effects')
    temp_entities: Dict[str, TempEntity] = type_object_property('temp_entities')
    variables: Dict[str, Any] = type_object_property('variables')

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, value: int):
        if value < 0:
            raise ValueError('level must be non-negative')
        if value > self.max_level:
            raise ValueError('level must not exceed max_level')
        self._level = value

    def __repr__(self) -> str:
        return f'{type(self).__name__}(name="{self.name["en"]}", level={self.level}, db_id={self._db_id})'

    def invoke_callback(self, event_name: str, eargs: Dict[str, Any]):
        """Invoke the event callback for an event, if any."""
        if event_name in self.event_callbacks:
            self.event_callbacks[event_name](**eargs)

    def effect(self, key: str='effect', recipients: Tuple[int]=(), **kwargs):
        """Create a temp entity effect from an effect key.

        Fetches the data from the temp_entities dictionary,
        which in turn is populated from the effects dictionary.
        """
        temp_entity = self._type_object.get_temp_entity(key)
        for name, attr in kwargs.items():
            setattr(temp_entity, name, attr)
        temp_entity.create(*recipients)

    def current(self, key: str) -> Any:
        """Fetch a variable's value for the entity's current level."""
        raw = self.variables[key]
        if isinstance(raw, dict):
            if 'per_level' in raw:
                base = raw.get('base', 0)
                return base + self.level * raw['per_level']
        elif isinstance(raw, (list, tuple)):
            index = min(self.level, len(raw)) - 1
            return raw[index]
        return raw

    def off_cooldown(self, key: str='cooldown', auto_reserve=True) -> bool:
        """Check if the skill's cooldown is off.

        If set to `auto_reserve`, the cooldown will be reserved
        automatically if it's off-cooldown.
        """
        cooldown = self._cooldowns[key]
        off = cooldown.remaining <= 0
        if off and auto_reserve:
            cooldown.reserve()
        return off

    def start_cooldown(self, key: str='cooldown') -> Cooldown:
        """Start a cooldown for an entity.

        Returns the started cooldown.
        """
        duration = self.current(key)
        cooldown = self._cooldowns[key]
        cooldown.start(duration)
        return cooldown

    def send_cooldown(self, player: Player, key: str='cooldown'):
        """Send a cooldown HudMsg to a player."""
        hud_msg = HudMsg('{remaining}', y=0.9, hold_time=1)
        repeat = Repeat(self._send_cooldown_tick, cancel_on_level_end=True)
        repeat.args = (hud_msg, player.index, key, repeat)
        repeat.start(1)

    def _send_cooldown_tick(self, hud_msg: HudMsg, player_index: int, key: str, repeat: Repeat):
        """Send one tick of the cooldown to a player."""
        remaining = math.ceil(self._cooldowns[key].remaining)
        if remaining > 0:
            hud_msg.send(player_index, remaining=remaining)
        else:
            hud_msg.send(player_index, remaining='')  # Empty message clears the HudMsg
            repeat.stop()

    def send_message(self, player: Player, string: TranslationStrings, **tokens: Dict[str, Any]):
        """Send a message to a player with the entity name as a prefix.

        Also replace all the tokens with orange values.
        """
        color_tokens = {
            key: f'{ORANGE}{value}{WHITE}'
            for key, value in tokens.items()
        }
        SayText2(create_translation_string(
            f'[{GREEN}{{name}}{WHITE}] {{message}}',
            name=self.name,
            message=string.tokenized(**color_tokens),
        )).send(player.index)

    def send_string(self, player: Player, key: str, **tokens: Dict[str, Any]):
        """Fetch and send a string from the entity's strings dictionary.

        Calls send_message() with the fetched string.
        """
        self.send_message(player, self.strings[key], **tokens)
