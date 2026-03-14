import os


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


SUPABASE_URL = _require_env("SUPABASE_URL")
SUPABASE_KEY = _require_env("SUPABASE_KEY")

TABLE_NAME = "logs"
PAGE_SIZE = 1000
REQUEST_TIMEOUT = 30

DERIBIT_EVENT_NAMES = {"deribit_vbi_snapshot", "deribit_vbi_snasphot"}

EXPECTED_TWEET_COUNT = 5
TWEET_MAX_LEN = 260
MAX_NA_PER_TWEET = 6

TWITTER_POST_URL = "https://api.twitter.com/2/tweets"

# By default Twitter posting is stubbed in this project environment.
# Set TWITTER_AUTOPOST_STUB=false to enable real posting.
TWITTER_AUTOPOST_STUB = _env_flag("TWITTER_AUTOPOST_STUB", default=True)
