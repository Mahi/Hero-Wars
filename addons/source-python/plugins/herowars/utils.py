# Python imports
import math
import random
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar

# Source.Python imports
from translations.manager import language_manager
from translations.strings import TranslationStrings



T = TypeVar('T')


def first(dict: Dict[Any, T], default: Optional[T]=None) -> T:
    """Fetch the first value from a dictionary."""
    try:
        return next(iter(dict.values()))
    except StopIteration:
        return default


def flatten(iterable: Iterable[Iterable[T]]) -> Iterable[T]:
    """Flatten an iterable by one level."""
    for x in iterable:
        for y in x:
            yield y


def dict_to_translation_strings(dict_: Dict[str, Any]) -> TranslationStrings:
    """Convert a dict of strings to a dict of translation strings."""
    translation_strings = TranslationStrings()
    for language, string in dict_.items():
        translation_strings[language] = string
    return translation_strings


def dicts_to_translation_strings(dict_: Dict[str, Dict[str, Any]]) -> Dict[str, TranslationStrings]:
    """Convert nested dicts of strings to nested dicts of translation strings."""
    return {
        key: dict_to_translation_strings(value)
        for key, value in dict_.items()
    }


def create_translation_string(*messages: Tuple[str], **tokens: Dict[str, Any]) -> TranslationStrings:
    """Create a new translation string.

    Makes it easier to create translation strings on-the-fly with f-strings.
    """
    message = ''.join(messages)
    trs = TranslationStrings()
    for lang in language_manager.values():
        trs[lang] = message
    trs.tokens.update(tokens)
    return trs


def split_translation_string(translation_string: TranslationStrings, separator: str='\n') -> List[TranslationStrings]:
    """Split a TranslationString to multiple TranslationStrings."""
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
    """Compare a random chance to the given percentage."""
    return random.random() * 100 < percentage


class Cooldown:
    """A cooldown whose value lowers with time."""

    def __init__(self, value: float=0.0):
        self._value = value + time.time()
        self._reserved = False

    @property
    def remaining(self) -> float:
        if self._reserved:
            return math.inf
        return max(self._value - time.time(), 0)

    @remaining.setter
    def remaining(self, value: float):
        self._value = value + time.time()

    def reserve(self):
        """Flag the cooldown as 'reserved'.

        The cooldown will be flagged as if it were already on-cooldown,
        without actually starting the cooldown.
        """
        self._reserved = True

    def start(self, duration: float):
        """Start the cooldown."""
        self._reserved = False
        self.remaining = duration
