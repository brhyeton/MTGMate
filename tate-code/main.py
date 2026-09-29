import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

import buylist
from auth import login_and_save_cookies
from match import match_owned_cards
from wantlist import load_wanted_cards


def run_login(headless: bool = False) -> None:
    login_and_save_cookies(headless=headless)


def run_check(
    csv_path: Path = Path("wants.csv"),
    output: Path = Path("card_results.csv"),
    debug: bool = False,
) -> None:
    start_time = time.perf_counter()

    session = buylist.load_session()

    if not buylist.check_logged_in(session):
        print("Saved login has expired or is invalid. Run `run_login()` first.")
        sys.exit(1)

    owned = load_wanted_cards(csv_path)
    by_set = defaultdict(list)
    for card in owned:
        by_set[card.set_code].append(card)

    print(f"{len(owned)} card entries across {len(by_set)} sets.")

    all_matches = []
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
            print(f"\nChecking set: {set_code}")
            try:
                rows = buylist.fetch_set_data(session, set_code)
            except Exception as e:
                print(f"  Failed to fetch: {e}")
                continue

            if debug:
                buylist.debug_dump(rows)

            matches = match_owned_cards(cards_in_set, rows)
            for m in matches:
                print(
                    f"  Found: {m.card_name} [{m.finish}] - ${m.credit:.2f} "
                    f"(mtgmate wants {m.mtgmate_wants}, you have {m.you_own})"
                )
                writer.writerow(
                    [
                        m.card_name,
                        m.set_code,
                        m.finish,
                        f"{m.credit:.2f}",
                        m.mtgmate_wants,
                        m.you_own,
                    ]
                )
                out_f.flush()
                all_matches.append(m)

    elapsed = time.perf_counter() - start_time
    rate = len(owned) / elapsed if elapsed > 0 else 0
    total_credit = sum(
        m.credit * min(m.you_own, m.mtgmate_wants) for m in all_matches
    )

    print(f"\nDone. {len(all_matches)} matches saved to '{output}'")
    print(
        f"Estimated total credit if selling everything matched: ${total_credit:.2f}"
    )
    print(
        f"Processed {len(owned)} card entries ({len(by_set)} sets) in "
        f"{elapsed:.2f}s ({rate:.1f} cards/sec)"
    )


if __name__ == "__main__":
    try:
        run_login()
        run_check(csv_path=Path("wants.csv"), debug=False)

    except KeyboardInterrupt:
        print("\nInterrupted -- partial results (if any) were already saved.")
        sys.exit(1)