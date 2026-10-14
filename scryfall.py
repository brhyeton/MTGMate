import requests
import config
import time

def fetch_scryfall_data(session: requests.Session, scryfall_id: str) -> dict:
    """Fetch and parse the JSON data for one card from Scryfall."""
    url = f"https://api.scryfall.com/cards/{scryfall_id}"

    resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()

    if resp.headers.get("content-type", "").startswith("text/html"):
        raise RuntimeError("Got HTML instead of JSON data from Scryfall.")

    time.sleep(config.REQUEST_DELAY_SECONDS)

    return parse_scryfall_data(resp.json())

def parse_scryfall_data(data: dict) -> dict:
    """Extract relevant fields from Scryfall card data."""
    return {
        "name": data.get("name"),
        "set_code": data.get("set"),
        "collector_number": data.get("collector_number"),
        
        "borderless": True if data.get("border_color") == "borderless" else False,
        "full_art": True if data.get("full_art") else False,
        "retroframe": True if data.get("frame") == "1993" else False,
        "promo": True if data.get("promo") else False,
        "extended_art": True if data.get("frame_effects") and "extendedart" in data.get("frame_effects") else False,
        "showcase": True if data.get("frame_effects") and "showcase" in data.get("frame_effects") else False,
        "textured": True if data.get("promo_types") and "textured" in data.get("promo_types") else False,
        "galaxy": True if data.get("promo_types") and "galaxyfoil" in data.get("promo_types") else False,
        "surge": True if data.get("promo_types") and "surgefoil" in data.get("promo_types") else False,
        "halo": True if data.get("promo_types") and "halofoil" in data.get("promo_types") else False,
        "gilded": True if data.get("promo_types") and "gilded" in data.get("promo_types") else False,
        "phyrexian": True if data.get("lang") == "ph" else False,
    }

def correct_card_name(session, card):

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

    return card