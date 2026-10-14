"""Stage 3: match your owned cards against mtgmate's buylist data. Pure logic."""

from dataclasses import dataclass
import re
from typing import List

import requests

from buylist import BuylistRow, fetch_scryfall_data
from wantlist import WantedCard


@dataclass
class Match:
    card_name: str
    set_code: str
    finish: str
    credit: float
    cash: float
    mtgmate_wants: int
    you_own: int


def match_owned_cards(session: requests.Session, owned: List[WantedCard], rows: List[BuylistRow]) -> List[Match]:
    """
    Matches on name + set_code + finish (exact). A nonfoil card you own
    won't be matched against a foil-only buylist entry, even if the price
    would be tempting -- that'd be a wrong/unsellable match.
    """
    # Index buylist rows for quick lookup: (name, set_code, finish) -> row
    index = {(r.name, r.set_code, r.finish): r for r in rows}

    matches = []
    for card in owned:

        #match the correct print type

            #(Borderless ###)
            #(Full Art ###)
            #(Promo)
            #(Extended Art)
            #(Showcase ###)
            #(Phyrexian)
            #(Surge Foil)
            #(Textured Foil)
            #(Galaxy Foil)
            #(Fracture Foil)
        
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

            scryfall_data = (fetch_scryfall_data(session, card.scryfall_id))

            #frame effects etc
            if scryfall_data['borderless']:
                card.name = card.name + f" (Borderless {scryfall_data['collector_number']})"
            if scryfall_data['full_art']:
                card.name = card.name + f" (Full Art {scryfall_data['collector_number']})"
            if scryfall_data['retroframe']:
                card.name = card.name + " (Retro Frame)"
            if scryfall_data['promo'] == True:
                card.name = card.name + " (Promo)"
            if scryfall_data['showcase']:
                card.name = card.name + f" (Showcase {scryfall_data['collector_number']})"
            if scryfall_data['extended_art']:
                card.name = card.name + " (Extended Art)"
            if scryfall_data['phyrexian']:
                card.name = card.name + " (Phyrexian)"

            #print effects etc
            if scryfall_data['textured']:
                card.name = card.name + " (Textured Foil)"
            if scryfall_data['galaxy']:
                card.name = card.name + " (Galaxy Foil)"
            if scryfall_data['surge']:
                card.name = card.name + " (Surge Foil)"
            if scryfall_data['halo']:  
                card.name = card.name + " (Halo Foil)"
            if scryfall_data['gilded']:
                card.name = card.name + " (Gilded Foil)"

            #check to see if there are multiple bracketed parts
            if card.name.count("(") > 1:
                card.name = re.sub(r'\)\s*\(', ' - ', card.name)

            row = next((r for r in potential_rows if r.name == card.name), None)

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