# Python imports
from typing import Any, Dict

# Hero-Wars imports
from .entity import Entity, type_object_property


class Skill(Entity):

    passive: bool = type_object_property('passive')
    level_interval: bool = type_object_property('level_interval')

    @property
    def next_required_level(self) -> int:
        return self.required_level + self.level_interval * self.level

    def invoke_callbacks(self, key: str, args: Dict[str, Any]):
        args['skill'] = self
        if self.level > 0 or self.passive:
            super().invoke_callbacks(key, args)
