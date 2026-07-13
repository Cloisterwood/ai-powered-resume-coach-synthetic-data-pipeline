"""Normalize skill names before calculating overlap metrics."""

import re

_VERSION = re.compile(r"\s*v?\d+(\.\d+)*\s*$")
_SUFFIXES = (
    ".js",
    " js",
    " developer",
    " engineer",
    " development",
    " programming",
)


def normalize_skill(raw: str) -> str:
    """Return a canonical form for an individual skill name."""
    normalized = _VERSION.sub("", raw.strip().lower())
    for suffix in _SUFFIXES:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    return normalized.strip(" .,-")


def normalize_set(skills: list[str]) -> set[str]:
    """Normalize skill names and remove empty or duplicate values."""
    return {skill for raw in skills if (skill := normalize_skill(raw))}


def jaccard(first: set[str], second: set[str]) -> float:
    """Return Jaccard similarity, treating any empty input as no overlap."""
    if not first or not second:
        return 0.0
    return len(first & second) / len(first | second)
