import json
import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

import helper.config as config

class SessionExpiredError(RuntimeError):
    """The saved cookies no longer log us in; run `login` again."""

@dataclass
class BuylistRow:
    name: str
    set_code: str
    set_name: str
    finish: str       # "Nonfoil", "Foil", or "Etched"
    cash: float        # dollars
    credit: float       # dollars
    wanted: int        # quantity mtgmate wants to buy
    uuid: str = ""  # mtgmate uuid for the card

def load_session() -> requests.Session:
    """Build a requests.Session carrying the cookies from the saved browser login."""
    if not config.COOKIE_JAR_PATH.exists():
        raise SessionExpiredError(
            f"No saved login found at {config.COOKIE_JAR_PATH}. "
            f"Run the `login` command first."
        )

    with open(config.COOKIE_JAR_PATH, encoding="utf-8") as f:
        cookies = json.load(f)

    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    retry = Retry(
        total=config.REQUEST_RETRIES,
        backoff_factor=config.REQUEST_BACKOFF_SECONDS,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    for c in cookies:
        session.cookies.set(
            c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/")
        )

    search_url = f"{config.BASE_URL}/cards/buylist_search?q=Forest"
    resp = session.get(search_url, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()

    if "sign_in" in resp.url or (resp.headers.get("content-type", "").startswith("text/html") and "sign_in" in resp.text):
        raise SessionExpiredError("Saved cookies have likely expired. Run `login` again.")

    soup = BeautifulSoup(resp.text, 'html.parser')
    token_meta = soup.find("meta", {"name": "csrf-token"})
    
    if token_meta and token_meta.get("content"):
        session.auth_token = token_meta["content"]
    else:
        token_input = soup.find("input", {"name": "authenticity_token"})
        if token_input and token_input.get("value"):
            session.auth_token = token_input["value"]
        else:
            raise RuntimeError("Could not find authenticity_token during session load.")
    return session

def check_logged_in(session: requests.Session) -> bool:
    resp = session.get(config.BASE_URL + config.LOGIN_CHECK_PATH,
                       timeout=config.REQUEST_TIMEOUT, allow_redirects=True)
    return "sign_in" not in resp.url

def fetch_set_data(session: requests.Session, set_code: str) -> list[BuylistRow]:
    """Fetch and parse the JSON buylist data for one set code (e.g. 'clb')."""
    slug = set_code.lower().strip()
    url = config.BASE_URL + config.SET_DATA_PATH.format(slug=slug)

    resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()

    if "sign_in" in resp.url or resp.headers.get("content-type", "").startswith("text/html"):
        raise SessionExpiredError("Got redirected to login instead of JSON data -- "
                                  "saved cookies have likely expired. Run `login` again.")

    time.sleep(config.REQUEST_DELAY_SECONDS)

    return parse_set_data(resp.json())

def parse_set_data(data: dict) -> list[BuylistRow]:
    """Turn the endpoint's JSON into rows. Entries with an unexpected shape are skipped."""
    rows = []
    for e in data.get("uuid_data", {}).values():
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
                    uuid=e["uuid"],
                )
            )
        except (KeyError, TypeError):
            continue  # skip anything with an unexpected shape rather than crash the whole run
    return rows

def debug_dump(rows: list[BuylistRow], limit: int = 15) -> None:
    print(f"Parsed {len(rows)} card entries. First {min(limit, len(rows))}:")
    for r in rows[:limit]:
        print(f"  {r.name} [{r.finish}] ({r.set_code}) -- "
              f"cash ${r.cash:.2f} / credit ${r.credit:.2f} / wanted {r.wanted}")

def add_item_to_buylist(session: requests.Session, uuid: str, quantity: int) -> dict:
    url = f"{config.BASE_URL}/buylist/cart/add_item_json"
    
    form_data = {
        "card_sku[id]": uuid,
        "card_sku[quantity]": str(quantity),
        "authenticity_token": session.auth_token
    }
    
    resp = session.post(url, data=form_data, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    
    if "sign_in" in resp.url or resp.headers.get("content-type", "").startswith("text/html"):
        raise SessionExpiredError("Session expired while trying to add item to buylist. Run `login` again.")
        
    time.sleep(config.REQUEST_DELAY_SECONDS)
    
    try:
        return resp.json()
    except ValueError:
        return {"status": "success", "text": resp.text}
