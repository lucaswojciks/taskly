"""Shared schema building blocks."""

from typing import Annotated

from pydantic import BeforeValidator


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


# A string that is trimmed before any length constraint is checked, so that a
# value of only whitespace fails ``min_length`` validation.
TrimmedStr = Annotated[str, BeforeValidator(_strip)]
