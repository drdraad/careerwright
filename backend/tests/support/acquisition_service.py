"""The restricted acquisition worker in the test process, in front of a controlled source
server (plan section 7: deterministic failure servers). Names resolve through a scripted
DNS to the server's loopback address, and that one origin is the fetcher's only extra
allowance; every other check is the production one. Pacing never sleeps, so tests do not
wait out real rate limits (the pacer is tested on its own)."""

import ipaddress
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from pydantic import SecretStr

from careerwright.acquisition import AcquisitionService, make_server
from careerwright.evidence import adzuna
from careerwright.evidence.acquire import Pacer
from careerwright.evidence.addresses import IPAddress
from careerwright.evidence.fetcher import Fetcher, FetchLimits, HostNotFoundError
from tests.support.source_server import SourceServer

LOOPBACK = ipaddress.ip_address("127.0.0.1")
TEST_LIMITS = FetchLimits(total_s=5.0, connect_s=2.0, read_s=5.0)


def scripted_resolver(names: dict[str, list[IPAddress]]) -> Callable[[str, int], list[IPAddress]]:
    def resolve(host: str, port: int) -> list[IPAddress]:
        try:
            return [ipaddress.ip_address(host)]
        except ValueError:
            pass
        if host not in names:
            raise HostNotFoundError
        return names[host]

    return resolve


@contextmanager
def acquisition_service(
    sources: SourceServer,
    *,
    names: dict[str, list[IPAddress]],
    credentials: tuple[SecretStr, SecretStr] | None = None,
    adzuna_host: str | None = None,
) -> Iterator[str]:
    """Yields the worker's base URL. `adzuna_host` serves Adzuna's search path from the
    source server under that (scripted) name."""
    fetcher = Fetcher(
        resolve=scripted_resolver(names),
        limits=TEST_LIMITS,
        user_agent="CareerwrightL0/test",
        extra_allowed=frozenset({("127.0.0.1", sources.port)}),
    )
    search_url = (
        f"http://{adzuna_host}:{sources.port}/v1/api/jobs/gb/search/{{page}}"
        if adzuna_host
        else adzuna.SEARCH_URL
    )
    service = AcquisitionService(
        fetcher,
        credentials=credentials,
        pacer=Pacer(sleep=lambda seconds: None),
        adzuna_search_url=search_url,
    )
    server = make_server(service, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, args=(0.05,), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
