"""The guarded fetcher's proxy mode for the controller's tools (ADR 0009, 2026-11-01
amendment): `--proxy URL --proxy-ca PATH`, given together or not at all. Without them a tool
fetches as the product does. With them every request is a CONNECT tunnel through that proxy,
TLS verified against that bundle (never turned off), and every check but the resolved-address
one still runs; the tool's output says so (`route_fields`), so no evidence claims an address
check that did not run. The product never uses this module.

The controller in a cloud session passes the session proxy without printing it:
`--proxy "$HTTPS_PROXY" --proxy-ca /root/.ccr/ca-bundle.crt`.
"""

import argparse
from pathlib import Path

from careerwright.evidence.fetcher import Fetcher, ProxyConfigError, fetch_proxy
from careerwright.evidence.sources import load_manifest


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--proxy",
        default=None,
        metavar="URL",
        help="proxy mode: fetch through this http://host:port HTTPS proxy (CONNECT only)",
    )
    parser.add_argument(
        "--proxy-ca",
        type=Path,
        default=None,
        metavar="PATH",
        help="proxy mode: the CA bundle TLS through the proxy is verified against (required)",
    )


def fetcher_from(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Fetcher:
    """The tool's fetcher: the product's (no proxy) unless both flags are given."""
    user_agent = load_manifest().user_agent
    if args.proxy is None and args.proxy_ca is None:
        return Fetcher(user_agent=user_agent)
    if args.proxy is None or args.proxy_ca is None:
        parser.error("--proxy and --proxy-ca go together")
    try:
        proxy = fetch_proxy(args.proxy, args.proxy_ca)
    except ProxyConfigError as error:  # its message never repeats the URL
        parser.error(str(error))
    return Fetcher(user_agent=user_agent, proxy=proxy)


def route_fields(fetcher: object) -> dict[str, bool]:
    """How the pages were fetched, as fields for the tool's output: in proxy mode the proxy
    chose each address, so Careerwright checked none. No fetcher (the tool's own default)
    and a test's stand-in are not proxy mode."""
    via_proxy = isinstance(fetcher, Fetcher) and fetcher.via_proxy
    return {"via_proxy": via_proxy, "address_checked": not via_proxy}
