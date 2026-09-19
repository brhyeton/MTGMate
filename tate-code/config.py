from pathlib import Path

BASE_URL = "https://www.mtgmate.com.au"
LOGIN_URL = BASE_URL + "/users/sign_in"

# The buylist page for a set is client-side rendered (React); the actual
# card data comes from this JSON endpoint underneath it, discovered via
# browser DevTools -> Network -> XHR.
SET_DATA_PATH = "/buylist/magic_sets/{slug}/data"

COOKIE_JAR_PATH = Path("mtgmate_cookies.json")

REQUEST_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 0.3
USER_AGENT = (
    "Mozilla/5.0 (compatible; mtgmate-buylist-checker/1.0; personal want-list tool)"
)