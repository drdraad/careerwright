"""The real Compose stack in demo mode, in its own project, ports and CAREERWRIGHT_HOME."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from tools.localenv import ensure_local_home
from tools.stack import CORE_SERVICES, Ports, Stack

STACK_PORTS = Ports(api=57100, auth=57199, postgres=57532, web=57400)


@pytest.fixture(scope="session")
def demo_stack(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Stack]:
    home = Path(tmp_path_factory.mktemp("careerwright-stack-home"))
    ensure_local_home(home)
    stack = Stack(project="careerwright-l0-stacktest", home=home, ports=STACK_PORTS, live=False)
    stack.down()
    stack.build()  # the containers must run this checkout's code, not a stale image
    try:
        stack.up(*CORE_SERVICES)
        yield stack
    finally:
        stack.down()
