# Python imports
from typing import Any, Callable, Dict, Optional, Tuple, Union

# Source.Python imports
from effects.base import TempEntity
from messages.colors.saytext2 import GREEN, ORANGE, WHITE
from messages import SayText2
from translations.strings import TranslationStrings

# Hero-Wars imports
from ..utils import CooldownDict, create_translation_string
from .type_objects import EntityType


def type_object_property(attr_name: str) -> property:
    def fget(self):
        return getattr(self._type_object, attr_name)
    return property(fget)


class Entity:

    def __init__(self, type_object: EntityType, level: int=0, *, db_id: Optional[int]=None):
        self._type_object = type_object
        self._level = level
        self._db_id = db_id
        self._temp_entities: Dict[str, Tuple[TempEntity, str]] = {}
        self._cooldowns = CooldownDict()

    key: str = type_object_property('key')
    author: Optional[str] = type_object_property('author')
    required_level: int = type_object_property('required_level')
    max_level: int = type_object_property('max_level')
    name: TranslationStrings = type_object_property('name')

    strings: Dict[str, TranslationStrings] = type_object_property('strings')
    init_callback: Optional[Callable] = type_object_property('init_callback')
    event_callbacks: Dict[str, Callable] = type_object_property('event_callbacks')
    effects: Dict[str, Any] = type_object_property('effects')
    temp_entities: Dict[str, TempEntity] = type_object_property('temp_entities')
    variables: Dict[str, Any] = type_object_property('variables')

    @property
    def description(self) -> TranslationStrings:
        return self.strings['description'].tokenized(**{
            variable: self._variable_range_string(variable)
            for variable in self.variables.keys()
        })

    def _variable_range_string(self, key: str) -> str:
        raw = self.variables[key]
        if isinstance(raw, dict):
            if 'per_level' in raw:
                base = raw.get('base', 0)
                start = base + raw['per_level']
                end = base + self.max_level * raw['per_level']
                return f'{start} - {end}'
        elif isinstance(raw, (list, tuple)):
            if len(raw) == self.max_level:
                return f'{raw[0]} - {raw[self.max_level - 1]}' 
        return str(raw)

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

    def invoke_callbacks(self, key: str, args: Dict[str, Any]):
        if key in self.event_callbacks:
            self.event_callbacks[key](**args)

    def effect(self, key: str='effect', recipients: Tuple[int]=(), **kwargs):
        temp_entity = self._type_object.get_temp_entity(key)
        for name, attr in kwargs.items():
            setattr(temp_entity, name, attr)
        temp_entity.create(*recipients)

    def current(self, key: str) -> Any:
        raw = self.variables[key]
        if isinstance(raw, dict):
            if 'per_level' in raw:
                base = raw.get('base', 0)
                return base + self.level * raw['per_level']
        elif isinstance(raw, (list, tuple)):
            index = min(self.level, len(raw)) - 1
            return raw[index]
        return raw

    def cooldown(self, key: str='cooldown') -> int:
        value = self._cooldowns[key]
        if value <= 0:
            self._cooldowns[key] = self.current(key)
        return value

    def send_message(self, player_index: int, string: TranslationStrings, **tokens: Dict[str, Any]):
        color_tokens = {
            key: f'{ORANGE}{value}{WHITE}'
            for key, value in tokens.items()
        }
        SayText2(create_translation_string(
            f'[{GREEN}{{name}}{WHITE}] {{message}}',
            name=self.name,
            message=string.tokenized(**color_tokens),
        )).send(player_index)

    def send_string(self, player_index: int, key: str, **tokens: Dict[str, Any]):
        self.send_message(player_index, self.strings[key], **tokens)
