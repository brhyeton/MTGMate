"""
One-time browser login. Solves the CAPTCHA interactively, then saves the
resulting session cookies to disk -- after this, `requests` can reuse those
cookies for every future run, so the browser is only needed here, not for
the actual scraping.

Run this again whenever `check` starts failing with login-wall redirects,
i.e. whenever the saved cookies have expired.
"""

import getpass
import json
import os

from playwright.sync_api import sync_playwright

import config

# Plain text file, two lines:
#   email@example.com
#   yourpassword
# Not committed to git, not shared when you hand this script to others --
# each person makes their own.
CREDENTIALS_FILE = config.CREDENTIALS_FILE


def _read_credentials_file():
    if not CREDENTIALS_FILE.exists():
        return None, None
    lines = CREDENTIALS_FILE.read_text(encoding="utf-8").splitlines()
    lines = [line.strip() for line in lines if line.strip()]  # drop blank lines
    if len(lines) < 2:
        print(f"Warning: {CREDENTIALS_FILE} exists but doesn't have two lines "
              f"(email, then password) -- ignoring it.")
        return None, None
    return lines[0], lines[1]


def get_credentials():
    file_email, file_password = _read_credentials_file()

    email = file_email or os.environ.get("MTGMATE_EMAIL") or input("mtgmate email: ").strip()
    password = (
        file_password
        or os.environ.get("MTGMATE_PASSWORD")
        or getpass.getpass("mtgmate password: ")
    )
    return email, password


def _context_is_logged_in(context) -> bool:
    """
    Load a login-only page in a fresh tab of this context. Tabs share cookies,
    so this reflects the login whichever tab it happened in. (A real page load
    is needed: Cloudflare 403s Playwright's `context.request` client.)
    """
    probe = context.new_page()
    try:
        resp = probe.goto(config.BASE_URL + config.LOGIN_CHECK_PATH,
                          wait_until="domcontentloaded")
        # Logged out -> redirected to /users/sign_in. Anything but a clean
        # load (e.g. a 403 challenge) is treated as "can't confirm".
        return resp is not None and resp.ok and "sign_in" not in probe.url
    finally:
        probe.close()


def login_and_save_cookies(headless: bool = False) -> None:
    email, password = get_credentials()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(config.LOGIN_URL)

        page.fill("#user_email", email)
        page.fill("#user_password", password)

        # We don't try to guess/click mtgmate's submit button -- its selector
        # isn't something this script can verify from outside a real browser.
        # Solve the CAPTCHA and click "Sign In" yourself; the script just
        # waits for you to confirm it's done.
        input("Solve the CAPTCHA (if shown) and click Sign In in the browser window, "
              "then press Enter here once you're logged in...")

        # Confirm we're actually logged in before saving -- if the login
        # failed silently we'd otherwise save a useless cookie jar.
        #
        # Don't judge this from a tab's URL: the login can finish in a
        # different tab/window than `page`, and `context.pages[-1]` isn't
        # reliably that one, so we'd read a stale sign-in page. Instead ask the
        # server directly with the context's cookies, which every tab shares.
        if not _context_is_logged_in(context):
            open_tabs = ", ".join(p.url for p in context.pages) or "none"
            print("mtgmate says this browser session is not logged in -- "
                  "Cookies were NOT saved. Make sure you clicked Sign In and "
                  f"try again. (Open tabs: {open_tabs})")
            browser.close()
            return

        cookies = context.cookies()
        browser.close()

    with open(config.COOKIE_JAR_PATH, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)

    print(f"Logged in. Cookies saved to {config.COOKIE_JAR_PATH} -- "
          f"`check` will reuse these until they expire, no browser needed.")