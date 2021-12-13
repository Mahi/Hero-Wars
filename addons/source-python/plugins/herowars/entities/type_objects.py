# Python imports
import math
from typing import Any, Callable, Dict, List, Optional

# Site-Package imports
from dataclasses import dataclass, field
from effects.base import TempEntity

# Source.Python imports
from translations.strings import TranslationStrings

# Hero-Wars imports
from ..precache import get_model


@dataclass
class EntityType:
    key: str
    author: Optional[str] = None
    required_level: int = 0
    max_level: int = math.inf

    strings: Dict[str, TranslationStrings] = field(default_factory=dict)
    init_callback: Optional[Callable] = None
    event_callbacks: Dict[str, Callable] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    temp_entities: Dict[str, TempEntity] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> TranslationStrings:
        return self.strings['name']

    @property
    def description(self) -> TranslationStrings:
        return self.strings['description']

    def get_temp_entity(self, key: str) -> TempEntity:
        if key not in self.temp_entities:
            params = self.effects[key].copy()
            del params['model']
            name = params.pop('temp_entity')
            self.temp_entities[key] = TempEntity(name, **params)
        temp_entity = self.temp_entities[key]
        temp_entity.model = temp_entity.halo = get_model(self.effects[key]['model'])
        return temp_entity


@dataclass
class SkillType(EntityType):
    passive: bool = False
    required_level: int = 1
    max_level: int = 8
    level_interval: int = 2


@dataclass
class HeroType(EntityType):
    skill_types: List[SkillType] = field(default_factory=list)
