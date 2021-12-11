# Python impors
import math
from typing import Any, Dict, List

# Hero-Wars imports
from ..constants import BASE_XP, XP_PER_LEVEL
from .entity import Entity
from .skill import Skill


class Hero(Entity):

    def __init__(self, *args, xp: int=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._xp = xp
        self.skills = self._create_skills()

    def _create_skills(self) -> List[Skill]:
        return [Skill(skill_type) for skill_type in self.type_object.skill_types]

    @property
    def required_xp(self) -> int:
        if self.level >= self.max_level:
            return math.inf
        if self.level <= 0:
            return BASE_XP
        return BASE_XP + self.level * XP_PER_LEVEL

    @property
    def xp(self) -> int:
        return self._xp

    @xp.setter
    def xp(self, value: int):
        self._xp = value
        try:
            while self.xp < 0:
                self.level -= 1
                self._xp += self.required_xp

            while self.xp >= self.required_xp:
                self._xp -= self.required_xp
                self.level += 1

        except ValueError: # Invalid level value (<0 or >max_level)
            self._xp = 0

    @Entity.level.setter
    def level(self, value: int):
        self._level = value
        if self.xp >= self.required_xp:
            self._xp = 0

    @property
    def skill_points(self) -> int:
        used_points = sum(skill.level for skill in self.skills)
        return self.level - used_points

    def can_upgrade_skill(self, skill: Skill) -> bool:
        return (
            self.skill_points > 0
            and skill.level < skill.max_level
            and skill.next_required_level <= self.level
            and not skill.passive
            and skill in self.skills
        )

    def can_downgrade_skill(self, skill: Skill) -> bool:
        return skill.level > 0 and not skill.passive and skill in self.skills

    def reset_skills(self):
        for skill in self.skills:
            skill.level = 0

    def trigger_skills(self, key: str, args: Dict[str, Any]):
        for skill in self.skills:
            if skill.level > 0 or skill.passive:
                skill.trigger(key, args)
