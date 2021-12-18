# Python imports
from collections import OrderedDict
from importlib import import_module
from typing import Any, Callable, Dict, Tuple
from translations.strings import TranslationStrings

# Site-Package imports
import yaml

# Source.Python imports
from path import Path

# Hero-Wars imports
from . import config
from .entities.type_objects import HeroType, SkillType
from .utils import dicts_to_translation_strings


def _build_callbacks(obj: Any) -> Tuple[Callable, Callable]:
    init_callback = None
    event_callbacks = {}
    for name, attr in vars(obj).items():
        if name == 'init':
            init_callback = attr
        elif not name.startswith('_'):
            event_callbacks[name] = attr
    return init_callback, event_callbacks


def _build_hero_types(root: Path) -> Dict[str, HeroType]:
    hero_types = []
    for path in root.dirs():
        hero_type = _build_hero_type(path)
        hero_types.append(hero_type)
    hero_types.sort(key=lambda hero: hero.required_level)
    return OrderedDict((hero_type.key, hero_type) for hero_type in hero_types)


def _build_hero_type(path: Path) -> HeroType:
    # Load data.yml
    with open(path / 'data.yml', encoding='utf-8') as data_file:
        hero_data = yaml.safe_load(data_file)

    # Load code.py
    code_module = import_module(f'herowars.heroes.{path.name}.code')

    # Load strings.yml
    with open(path / 'strings.yml', encoding='utf-8') as strings_file:
        strings = yaml.safe_load(strings_file)

    # Separate skills's data from hero's data
    skill_defaults = hero_data.pop('skill_defaults', {})
    skills_data = hero_data.pop('skills')
    skills_strings = strings.pop('skills')

    # Convert strings to TranslationStrings
    skills_translations = {
        skill_name: dicts_to_translation_strings(skill_strings)
        for skill_name, skill_strings in skills_strings.items()
    } 
    hero_translations = dicts_to_translation_strings(strings)

    # Create skill types
    skill_types = []
    for name, attr in vars(code_module).items():
        if not name in skills_strings:
            if isinstance(attr, type) and attr.__module__ == code_module.__name__ and not name.startswith('_'):
                print(f'Skipping class {path.name}.{name}, missing record in strings.py')
            continue
        skill_init, skill_events = _build_callbacks(attr)
        skill_data = {**skill_defaults, **skills_data.get(name, {})}
        skill_types.append(SkillType(
            key=skill_data.pop('key', f'{path.name}.{name}'),
            variables=skill_data.pop('variables', {}),
            strings=skills_translations.pop(name, TranslationStrings()),
            init_callback=skill_init,
            event_callbacks=skill_events,
            **skill_data,
        ))


    # Create HeroType
    if 'key' not in hero_data:
        hero_data['key'] = path.name
    hero_init, hero_events = _build_callbacks(code_module)
    return HeroType(
        strings=hero_translations,
        skill_types=skill_types,
        init_callback=hero_init,
        event_callbacks=hero_events,
        **hero_data,
    )


hero_types: Dict[str, HeroType] = _build_hero_types(Path(config.heroes_dir.get_string()))
