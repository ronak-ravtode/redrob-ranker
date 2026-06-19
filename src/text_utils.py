from __future__ import annotations

import re
from collections.abc import Iterable

_SPACE_RE = re.compile(r"\s+")


def normalize(value: object) -> str:
    return _SPACE_RE.sub(" ", str(value or "").lower()).strip()


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def count_distinct(text: str, phrases: Iterable[str]) -> int:
    return sum(1 for phrase in phrases if phrase in text)


def clipped(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def candidate_id_suffix(value: object) -> int:
    text = str(value or "")
    prefix = "CAND_"
    if text.startswith(prefix) and text[len(prefix):].isdigit():
        return int(text[len(prefix):])
    return 10**12
