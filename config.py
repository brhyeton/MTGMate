from pathlib import Path

BASE_URL = "https://www.mtgmate.com.au"
LOGIN_URL = BASE_URL + "/users/sign_in"

# The buylist page for a set is client-side rendered (React); the actual
# card data comes from this JSON endpoint underneath it, discovered via
# browser DevTools -> Network -> XHR.
SET_DATA_PATH = "/buylist/magic_sets/{slug}/data"

# A page that redirects to /users/sign_in when logged out. (/buylist does NOT
# -- it's public, so it can't tell whether a session is valid.)
LOGIN_CHECK_PATH = "/users/edit"

# Anchored to this folder so the saved login is found no matter which
# directory the scripts are launched from. Both files are gitignored.
_HERE = Path(__file__).resolve().parent
COOKIE_JAR_PATH = _HERE / "mtgmate_cookies.json"
CREDENTIALS_FILE = _HERE / "mtgmate_credentials.txt"

REQUEST_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 0.3
# Retries for transient failures (429 / 5xx / dropped connections).
REQUEST_RETRIES = 3
REQUEST_BACKOFF_SECONDS = 1.0
USER_AGENT = (
    "Mozilla/5.0 (compatible; mtgmate-buylist-checker/1.0; personal want-list tool)"
)
