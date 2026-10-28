"""Container health check: `python -m nessa.api.health http://127.0.0.1:8000/readyz`."""

import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def main() -> None:
    url = sys.argv[1]
    request = urllib.request.Request(url, headers={"Host": urlsplit(url).netloc})  # noqa: S310 - fixed local URL
    try:
        with urllib.request.urlopen(request, timeout=2) as response:  # noqa: S310
            sys.exit(0 if response.status == 200 else 1)
    except (urllib.error.URLError, OSError):
        sys.exit(1)


if __name__ == "__main__":
    main()
