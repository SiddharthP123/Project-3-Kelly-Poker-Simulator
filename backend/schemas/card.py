"""Shared card-string validation for request schemas.

Validating through Card.from_str here means malformed notation (e.g. 'Zx')
fails with a clean 422 at the schema layer, rather than an unhandled
ValueError turning into a 500 once it reaches poker/ code.
"""

from typing import Annotated

from pydantic import AfterValidator

from poker.cards import Card


def _validate_card_string(value: str) -> str:
    Card.from_str(value)
    return value


CardStr = Annotated[str, AfterValidator(_validate_card_string)]
