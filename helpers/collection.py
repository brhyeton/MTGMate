import csv
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import List
import helpers.buylist as buylist

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

@dataclass()
class SellingCard:
    name: str
    set_code: str    # lowercased
    finish: str       # "Nonfoil" / "Foil" / "Etched" -- matches mtgmate's values
    owned_quantity: int
    scryfall_id: str = ""


def _normalize_finish(raw: str) -> str:
    return _FOIL_MAP.get(raw.strip().lower(), raw.strip().title())


def load_selling_cards(csv_path: Path, log_update: callable) -> List[SellingCard]:
    selling = []

    log_update(f"Loading selling cards from {csv_path}")
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            log_update(
                f"CSV is missing expected column(s): {', '.join(missing)}. Found columns: {reader.fieldnames}"
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

            selling.append(
                SellingCard(
                    name=name,
                    set_code=set_code,
                    finish=_normalize_finish(foil_raw),
                    owned_quantity=qty,
                    scryfall_id=row.get("Scryfall ID", "").strip(),
                )
            )
    log_update(f"Loaded {len(selling)} selling cards from {csv_path}")
    return selling