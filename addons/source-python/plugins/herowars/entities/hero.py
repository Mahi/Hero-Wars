# Python impors
import math
from typing import Any, Dict, List

# Hero-Wars imports
from .. import config
from .entity import Entity
from .skill import Skill


class Hero(Entity):
    """Hero entity manages skills and XP."""

    def __init__(self, *args, xp: int=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._xp = xp
        self.skills = []

    def _create_skills(self) -> List[Skill]:
        """Create the skill entities from their type objects."""
        self.skills.extend([Skill(skill_type) for skill_type in self._type_object.skill_types])

    @property
    def required_xp(self) -> int:
        if self.level >= self.max_level:
            return math.inf
        base = config.xp_formula_base.get_int()
        if self.level <= 0:
            return base
        per_level = config.xp_formula_per_level.get_int()
        return base + self.level * per_level

    @property
    def xp(self) -> int:
        return self._xp

    @xp.setter
    def xp(self, value: int):
        self._xp = value
        try:
            while self.xp < 0:
                self._level -= 1
                self._xp += self.required_xp

            while self.xp >= self.required_xp:
                self._xp -= self.required_xp
                self._level += 1

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
        """Check if the hero can upgrade a particular skill."""
        return (
            self.skill_points > 0
            and skill.level < skill.max_level
            and skill.next_required_level <= self.level
            and not skill.passive
            and skill in self.skills
        )

    def can_downgrade_skill(self, skill: Skill) -> bool:
        """Check if the hero can downgrade a particular skill."""
        return skill.level > 0 and not skill.passive and skill in self.skills

    def reset_skills(self):
        """Reset all hero's skills to level 0."""
        for skill in self.skills:
            skill.level = 0
