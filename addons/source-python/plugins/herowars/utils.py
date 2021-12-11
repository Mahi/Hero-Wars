# Python imports
import collections
import random
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar

# Source.Python imports
from translations.manager import language_manager
from translations.strings import TranslationStrings



T = TypeVar('T')


def first(dict: Dict[Any, T], default: Optional[T]=None) -> T:
    try:
        return next(iter(dict.values()))
    except StopIteration:
        return default


def flatten(iterable: Iterable[Iterable[T]]) -> Iterable[T]:
    for x in iterable:
        for y in x:
            yield y


def dict_to_translation_strings(dict_: Dict[str, Any]) -> TranslationStrings:
    translation_strings = TranslationStrings()
    for language, string in dict_.items():
        translation_strings[language] = string
    return translation_strings


def dicts_to_translation_strings(dict_: Dict[str, Dict[str, Any]]) -> Dict[str, TranslationStrings]:
    return {
        key: dict_to_translation_strings(value)
        for key, value in dict_.items()
    }


def create_translation_string(*messages: Tuple[str], **tokens: Dict[str, Any]) -> TranslationStrings:
    message = ''.join(messages)
    trs = TranslationStrings()
    for lang in language_manager.values():
        trs[lang] = message
    trs.tokens.update(tokens)
    return trs


def split_translation_string(translation_string: TranslationStrings, separator: str='\n') -> List[TranslationStrings]:
    result = []
    for lang, string in translation_string.items():
        parts = string.split(separator)
        if len(result) < len(parts):
            result.extend([
                TranslationStrings()
                for _ in range(len(parts) - len(result))
            ])
        for i, part in enumerate(parts):
            result[i][lang] = part
            result[i].tokens.update(translation_string.tokens)
    return result


def chance(percentage: int) -> bool:
    return random.random() * 100 < percentage


class CooldownDict(collections.defaultdict):

    def __init__(self, default_factory=int, *args, **kwargs):
        super().__init__(default_factory, *args, **kwargs)

    def __getitem__(self, key):
        return super().__getitem__(key) - time.time()

    def __setitem__(self, key, value):
        return super().__setitem__(key, value + time.time())
