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

    def invoke_callback(self, event_name: str, eargs: Dict[str, Any]):
        """Invoke event callback for the skill.
        
        Ensures the skill can be invoked in the first place,
        i.e. that the skill is a passive or has levels in it.
        """
        if self.level > 0 or self.passive:
            super().invoke_callback(event_name, eargs)
