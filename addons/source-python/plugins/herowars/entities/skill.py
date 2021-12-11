# Python imports
from typing import Any, Dict, Tuple
from effects.base import TempEntity

# Source.Python imports
from messages.base import SayText2
from messages.colors.saytext2 import GREEN, ORANGE, WHITE
from translations.strings import TranslationStrings

# Custom package imports
from easyplayer import Player

# Hero-Wars imports
from .entity import Entity, type_object_property
from ..strings import common
from ..utils import CooldownDict, create_translation_string


class Skill(Entity):

    passive: bool = type_object_property('passive')
    level_interval: bool = type_object_property('level_interval')
    variables: Dict[str, Any] = type_object_property('variables')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cooldowns = CooldownDict()
        self._temp_entities: Dict[str, Tuple[TempEntity, str]] = {}

    @property
    def next_required_level(self) -> int:
        return self.required_level + self.level_interval * self.level

    @Entity.description.getter
    def description(self) -> TranslationStrings:
        return self.strings['description'].tokenized(**{
            variable: self._variable_range(variable)
            for variable in self.variables.keys()
        })

    def current(self, key: str) -> Any:
        raw = self.variables[key]
        if isinstance(raw, dict):
            if 'per_level' in raw:
                base = raw.get('base', 0)
                return base + self.level * raw['per_level']
        elif isinstance(raw, (list, tuple)):
            if len(raw) == self.max_level:
                return raw[self.level - 1]
        return raw

    def _variable_range(self, key: str) -> str:
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

    def cooldown(self, key: str='cooldown') -> int:
        value = self._cooldowns[key]
        if value <= 0:
            self._cooldowns[key] = self.current(key)
        return value

    def effect(self, key: str='effect', recipients: Tuple[int]=(), **kwargs):
        temp_entity = self.type_object.get_temp_entity(key)
        for name, attr in kwargs.items():
            setattr(temp_entity, name, attr)
        temp_entity.create(*recipients)

    def trigger(self, key: str, args: Dict[str, Any]):
        callback = self.type_object.event_callbacks.get(key)
        if callback is not None:
            callback(skill=self, **args)

    def message(self, player: Player, string: TranslationStrings, **tokens: Dict[str, Any]):
        color_tokens = {
            key: f'{ORANGE}{value}{WHITE}'
            for key, value in tokens.items()
        }
        SayText2(create_translation_string(
            f'[{GREEN}{{skill_name}}{WHITE}] {{message}}',
            skill_name=self.name,
            message=string,
        )).send(player.index, **color_tokens)

    def chat(self, player: Player, string_key: str, **tokens: Dict[str, Any]):
        self.message(player, self.strings[string_key], **tokens)

    def chat_cooldown(self, player: Player, key: str='cooldown'):
        self.message(
            player,
            create_translation_string(
                f'{{cooldown_str}}: {ORANGE}{{duration}}',
                cooldown_str=common['Cooldown'],
            ),
            duration=round(self._cooldowns[key], 1),
        )
