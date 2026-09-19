"""
Fetch + parse mtgmate's per-set buylist JSON data.

The buylist page itself is client-side rendered (React), but it's backed by
a JSON endpoint at /buylist/magic_sets/<set_code>/data -- found via browser
DevTools Network tab. This talks to that endpoint directly: no HTML
parsing, no guessing markup, just structured data.

Prices in the API are in cents (e.g. credit_price: 1250 == $12.50).
"""

import json
import time
from dataclasses import dataclass
from typing import List

import requests

from . import config


@dataclass
class BuylistRow:
    name: str
    set_code: str
    set_name: str
    finish: str       # "Nonfoil", "Foil", or "Etched"
    cash: float        # dollars
    credit: float       # dollars
    wanted: int        # quantity mtgmate wants to buy


def load_session() -> requests.Session:
    """Build a requests.Session carrying the cookies from the saved browser login."""
    if not config.COOKIE_JAR_PATH.exists():
        raise RuntimeError(
            f"No saved login found at {config.COOKIE_JAR_PATH}. "
            f"Run the `login` command first."
        )

    with open(config.COOKIE_JAR_PATH, encoding="utf-8") as f:
        cookies = json.load(f)

    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    for c in cookies:
        session.cookies.set(
            c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/")
        )
    return session


def check_logged_in(session: requests.Session) -> bool:
    resp = session.get(config.BASE_URL + "/buylist", timeout=config.REQUEST_TIMEOUT,
                        allow_redirects=True)
    return "sign_in" not in resp.url


def fetch_set_data(session: requests.Session, set_code: str) -> List[BuylistRow]:
    """Fetch and parse the JSON buylist data for one set code (e.g. 'clb')."""
    slug = set_code.lower().strip()
    url = config.BASE_URL + config.SET_DATA_PATH.format(slug=slug)

    resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()

    if "sign_in" in resp.url or resp.headers.get("content-type", "").startswith("text/html"):
        raise RuntimeError("Got redirected to login instead of JSON data -- "
                            "saved cookies have likely expired. Run `login` again.")

    time.sleep(config.REQUEST_DELAY_SECONDS)

    data = resp.json()
    entries = data.get("uuid_data", {}).values()

    rows = []
    for e in entries:
        try:
            rows.append(
                BuylistRow(
                    name=e["name"],
                    set_code=e["set_code"],
                    set_name=e["set_name"],
                    finish=e["finish"],
                    cash=e["buy_price"] / 100,
                    credit=e["credit_price"] / 100,
                    wanted=e["quantity"],
                )
            )
        except (KeyError, TypeError):
            continue  # skip anything with an unexpected shape rather than crash the whole run
    return rows


def debug_dump(rows: List[BuylistRow], limit: int = 15) -> None:
    print(f"Parsed {len(rows)} card entries. First {min(limit, len(rows))}:")
    for r in rows[:limit]:
        print(f"  {r.name} [{r.finish}] ({r.set_code}) -- "
              f"cash ${r.cash:.2f} / credit ${r.credit:.2f} / wanted {r.wanted}")