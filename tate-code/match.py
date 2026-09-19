"""Stage 3: match your owned cards against mtgmate's buylist data. Pure logic."""

from dataclasses import dataclass
from typing import List

from .buylist import BuylistRow
from .wantlist import WantedCard


@dataclass
class Match:
    card_name: str
    set_code: str
    finish: str
    credit: float
    cash: float
    mtgmate_wants: int
    you_own: int


def match_owned_cards(owned: List[WantedCard], rows: List[BuylistRow]) -> List[Match]:
    """
    Matches on name + set_code + finish (exact). A nonfoil card you own
    won't be matched against a foil-only buylist entry, even if the price
    would be tempting -- that'd be a wrong/unsellable match.
    """
    # Index buylist rows for quick lookup: (name, set_code, finish) -> row
    index = {(r.name, r.set_code, r.finish): r for r in rows}

    matches = []
    for card in owned:
        row = index.get((card.name, card.set_code, card.finish))
        if row and row.wanted > 0:
            matches.append(
                Match(
                    card_name=card.name,
                    set_code=card.set_code,
                    finish=card.finish,
                    credit=row.credit,
                    cash=row.cash,
                    mtgmate_wants=row.wanted,
                    you_own=card.owned_quantity,
                )
            )
    return matches