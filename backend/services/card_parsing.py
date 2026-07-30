"""Round-tripping between validated card-string schema fields and poker/'s
actual Card objects. Schemas already guarantee each string parses (see
schemas/card.py's CardStr validator) -- this is just the conversion step,
kept in one place so it isn't repeated inline in every router.
"""

from poker.cards import Card


def parse_cards(card_strings):
    return [Card.from_str(text) for text in card_strings]
