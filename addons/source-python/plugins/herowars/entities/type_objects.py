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
    """Type object for Hero-Wars entities.

    The type object holds the common data for entities of the same type,
    ensuring that things like translation strings or entity names
    aren't duplicated for every instance of a particular entity.

    All type object attributes are documented in the code.
    """

    # Unique key to identify the entity with. Used for database storage etc.
    key: str

    # Author of the entity. NOT the player using the entity, but the original creator.
    author: Optional[str] = None

    # Minimum level required to access the entity.
    required_level: int = 0

    # Maximum level the entity is allowed to reach.
    max_level: int = math.inf

    # TranslationStrings used by the entity.
    strings: Dict[str, TranslationStrings] = field(default_factory=dict)

    # Callback to invoke when the entity is first equipped.
    init_callback: Optional[Callable] = None

    # Callbacks to invoke on any game event.
    event_callbacks: Dict[str, Callable] = field(default_factory=dict)

    # Data variables the entity uses for its callbacks.
    variables: Dict[str, Any] = field(default_factory=dict)

    # Data for visual effects the entity might create.
    effects: Dict[str, Any] = field(default_factory=dict)

    # Internal cache for the temp entity objects for visual effects.
    _temp_entities: Dict[str, TempEntity] = field(default_factory=dict)

    @property
    def name(self) -> TranslationStrings:
        return self.strings['name']

    @property
    def description(self) -> TranslationStrings:
        self.strings['description'].tokens.update({
            variable: self._variable_range_string(variable)
            for variable in self.variables.keys()
        })
        return self.strings['description']

    def _variable_range_string(self, key: str) -> str:
        """Get a string of a data variable's range.

        Essentially a string of format "{min_value} - {max_value}".
        """
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

    def get_temp_entity(self, key: str) -> TempEntity:
        """Get a temp entity for an effect.

        Does NOT call create() on the temp entity.
        """
        if key not in self._temp_entities:
            params = self.effects[key].copy()
            del params['model']
            name = params.pop('temp_entity')
            self._temp_entities[key] = TempEntity(name, **params)
        temp_entity = self._temp_entities[key]
        temp_entity.model = temp_entity.halo = get_model(self.effects[key]['model'])
        return temp_entity


@dataclass
class SkillType(EntityType):
    """Skill type object for Hero-Wars skills."""

    # Is a passive - doesn't require levels, and is always enabled.
    passive: bool = False

    # Hero's required level for the skill to be leveled.
    required_level: int = 1

    # Maximum level of the skill.
    max_level: int = 8

    # Interval between hero levels required to level up the skill again.
    # Level interval of 2 means the skill can be leveled at levels 1, 3, 5, etc.
    level_interval: int = 2


@dataclass
class HeroType(EntityType):
    """Hero type obejct for Hero-Wars heroes."""

    # List of skill type objects the hero should possess.
    skill_types: List[SkillType] = field(default_factory=list)
