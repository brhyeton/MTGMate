import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

import helpers.buylist as buylist
from helpers.auth import login_and_save_cookies
from helpers.match import match_owned_cards
from helpers.collection import load_selling_cards


def run_login(headless: bool = False) -> None:
    login_and_save_cookies(headless=headless)

def run_check(
    csv_path: Path = Path("wants.csv"),
    output: Path = Path("card_results.csv"),
    debug: bool = False,
    log_update: callable = print,
    progress_update: callable = print,
    speed_update: callable = print
) -> None:
    start_time = time.perf_counter()

    session = buylist.load_session(log_update)

    if session is None:
        return None

    if not buylist.check_logged_in(session, log_update):
        return None

    owned = load_selling_cards(csv_path, log_update)
    by_set = defaultdict(list)
    for card in owned:
        by_set[card.set_code].append(card)

    log_update(f"{len(owned)} card entries across {len(by_set)} sets.")

    all_matches = []
    total_checked = 0
    with open(output, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(
            [
                "card_name",
                "set_code",
                "finish",
                "credit_offered",
                "mtgmate_wants",
                "you_own",
            ]
        )

        for set_code, cards_in_set in sorted(by_set.items()):
            log_update(f"\nChecking set: {set_code}")
            try:
                rows = buylist.fetch_set_data(session, set_code)
            except Exception as e:
                log_update(f"  Failed to fetch: {e}")
                continue

            if debug:
                buylist.debug_dump(rows)

            matches = match_owned_cards(session, cards_in_set, rows, log_update)
            for m in matches:
                log_update(
                    f"  Found: {m.card_name} [{m.finish}] - ${m.credit:.2f} - MTGMate wants {m.mtgmate_wants}, you have {m.you_own}"
                )
                writer.writerow(
                    [
                        m.card_name,
                        m.set_code,
                        m.finish,
                        f"{m.credit:.2f}",
                        m.mtgmate_wants,
                        m.you_own,
                        m.uuid,
                    ]
                )
                out_f.flush()
                all_matches.append(m)
                
                try:
                    buylist.add_item_to_buylist(session, m.uuid, min(m.you_own, m.mtgmate_wants))
                except:
                    log_update(f"  Failed to add {m.card_name} to buylist.")
                    continue
            total_checked += len(cards_in_set)
            elapsed = time.perf_counter() - start_time
            rate = len(owned) / elapsed if elapsed > 0 else 0
            speed_update(rate)
            print(total_checked)
            print(total_checked/len(owned) * 100)
            progress_update(int(total_checked/len(owned) * 100))

    total_credit = sum(
        m.credit * min(m.you_own, m.mtgmate_wants) for m in all_matches
    )

    log_update(f"\nDone. {len(all_matches)} matches saved to '{output}'")
    log_update(
        f"Estimated total credit if selling everything matched: ${total_credit:.2f}"
    )
    log_update(
        f"Processed {len(owned)} card entries ({len(by_set)} sets) in "
        f"{elapsed:.2f}s ({rate:.1f} cards/sec)"
    )
