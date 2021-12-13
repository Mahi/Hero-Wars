# Python imports
from typing import Any, Dict, Optional

# Source.Python imports
from translations.strings import TranslationStrings

# Hero-Wars imports
from .type_objects import EntityType


def type_object_property(attr_name: str) -> property:
    def fget(self):
        return getattr(self.type_object, attr_name)
    return property(fget)


class Entity:

    def __init__(self, type_object: EntityType, level: int=0, *, db_id: Optional[int]=None):
        self.type_object = type_object
        self._level = level
        self._db_id = db_id

    key: str = type_object_property('key')
    author: Optional[str] = type_object_property('author')
    required_level: int = type_object_property('required_level')
    max_level: int = type_object_property('max_level')
    strings: Dict[str, TranslationStrings] = type_object_property('strings')
    name: TranslationStrings = type_object_property('name')
    description: TranslationStrings = type_object_property('description')

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
        return f'{type(self).__name__}(name={self.name["en"]}, level={self.level}, db_id={self._db_id})'

    def invoke_callbacks(self, key: str, args: Dict[str, Any]):
        if key in self.type_object.event_callbacks:
            self.type_object.event_callbacks[key](**args)
