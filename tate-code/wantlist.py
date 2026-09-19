"""
Stage 1: load and normalize the want-list CSV (ManaBox export format).

Headers expected:
    Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,
    ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,Condition,
    Language,Purchase price currency

Matched by column name, not position. We use "Set code" (e.g. "CLB") rather
than "Set name" for matching against mtgmate, since mtgmate's API is keyed
by set code directly -- no fuzzy name-matching needed.

ManaBox's "Foil" column uses values like "normal", "foil", "etched" --
normalized here to match mtgmate's "Nonfoil"/"Foil"/"Etched" finish values.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List

NAME_COLUMN = "Name"
SET_CODE_COLUMN = "Set code"
FOIL_COLUMN = "Foil"
QUANTITY_COLUMN = "Quantity"

REQUIRED_COLUMNS = (NAME_COLUMN, SET_CODE_COLUMN, FOIL_COLUMN)

_FOIL_MAP = {
    "normal": "Nonfoil",
    "nonfoil": "Nonfoil",
    "foil": "Foil",
    "etched": "Etched",
}


@dataclass(frozen=True)
class WantedCard:
    name: str
    set_code: str    # lowercased
    finish: str       # "Nonfoil" / "Foil" / "Etched" -- matches mtgmate's values
    owned_quantity: int


def _normalize_finish(raw: str) -> str:
    return _FOIL_MAP.get(raw.strip().lower(), raw.strip().title())


def load_wanted_cards(csv_path: Path) -> List[WantedCard]:
    wanted = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                f"CSV is missing expected column(s): {', '.join(missing)}. "
                f"Found columns: {reader.fieldnames}"
            )

        for row in reader:
            name = (row.get(NAME_COLUMN) or "").strip()
            set_code = (row.get(SET_CODE_COLUMN) or "").strip().lower()
            foil_raw = (row.get(FOIL_COLUMN) or "").strip()
            qty_raw = (row.get(QUANTITY_COLUMN) or "0").strip()

            if not (name and set_code):
                continue

            try:
                qty = int(qty_raw)
            except ValueError:
                qty = 0

            wanted.append(
                WantedCard(
                    name=name,
                    set_code=set_code,
                    finish=_normalize_finish(foil_raw),
                    owned_quantity=qty,
                )
            )

    return wanted