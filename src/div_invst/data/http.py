"""HTTP GET with a pause before each call and a back-off on rate-limit and server errors. No caching here: the Store does that."""
import time

import requests

RETRY_STATUS = (429, 500, 502, 503)


def get(url: str, params: dict | None = None, headers: dict | None = None, sleep: float = 0.0, retries: int = 3,
        parse: str = "json"):
    """Parsed body; raises RuntimeError on a non-200 after the retries."""
    last = None
    for attempt in range(retries + 1):
        time.sleep(sleep if attempt == 0 else sleep + 5 * attempt)
        r = requests.get(url, params=params, headers=headers, timeout=60)
        if r.status_code == 200:
            return r.json() if parse == "json" else r.text
        last = r.status_code
        if r.status_code not in RETRY_STATUS:
            break
    raise RuntimeError(f"HTTP {last} from {url}")
