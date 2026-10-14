from dataclasses import dataclass
import re
from typing import List

import requests

from helpers.buylist import BuylistRow
from helpers.scryfall import correct_card_name
from helpers.collection import SellingCard
from helpers.scryfall import fetch_scryfall_data


@dataclass
class Match:
    card_name: str
    set_code: str
    finish: str
    credit: float
    cash: float
    mtgmate_wants: int
    you_own: int
    uuid: str


def match_owned_cards(session: requests.Session, owned: List[SellingCard], rows: List[BuylistRow]) -> List[Match]:
    """
    Matches on name + set_code + finish (exact). A nonfoil card you own
    won't be matched against a foil-only buylist entry, even if the price
    would be tempting -- that'd be a wrong/unsellable match.
    """
    # Index buylist rows for quick lookup: (name, set_code, finish) -> row
    index = {(r.name, r.set_code, r.finish): r for r in rows}

    matches = []
    for card in owned:
        
        potential_rows = [
            r_row for (r_name, r_set, r_finish), r_row in index.items()
            if r_set == card.set_code 
            and r_finish == card.finish 
            and (r_name == card.name or r_name.startswith(card.name + " "))
        ]

        row = None
        if len(potential_rows) == 1:
            row = potential_rows[0]
        elif len(potential_rows) > 1:
            try:
                card = correct_card_name(session, card)
                row = next((r for r in potential_rows if r.name == card.name), None)
            except Exception as e:
                print(f"Error occurred while correcting card name for {card.name}: {e}")
                row = None

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
                    uuid=row.uuid
                )
            )
    return matches