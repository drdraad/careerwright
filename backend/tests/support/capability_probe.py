"""Negative control (ported from the Sprint 0 spike): what Pydantic AI's DBOSDurability
capability journals by itself.

Runs the naive composition (an agent with `DBOSDurability`, `agent.run()` inside a DBOS
workflow, DBOS's default serializer) with the fake model, in its own process and DBOS
application, against the real system database. The leak scan must find the model's output
in the journal; if it did not, a clean scan elsewhere would prove nothing.
"""

import asyncio
import os

from dbos import DBOS, DBOSConfig
from pydantic import SecretStr
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.durable_exec.dbos import DBOSDurability

from nessa.config import WorkerSettings
from nessa.db import url_with_password
from nessa.identity.connection_check import ConnectionCheckResult
from tests.support.fake_models import fake_model_builder

PROBE_APP_NAME = "nessa-capability-probe"


def main() -> None:
    settings = WorkerSettings()
    config: DBOSConfig = {
        "name": PROBE_APP_NAME,
        "system_database_url": url_with_password(settings.dbos_database),
        "application_version": "probe-1",
        "run_migrations": False,
    }
    DBOS(config=config)
    build = fake_model_builder(output_sentinel=os.environ["NESSA_TEST_OUTPUT_SENTINEL"])
    agent = Agent(
        build("muse-spark-1.3-contributor", SecretStr(os.environ["NESSA_TEST_PROBE_KEY"])),
        name="nessa_probe_agent",
        output_type=NativeOutput(ConnectionCheckResult),
        capabilities=[DBOSDurability()],
    )

    @DBOS.workflow(name="nessa.capability_probe")
    async def probe_workflow(prompt: str) -> str:
        # Deliberately naive: the agent runs inside the workflow, so its steps journal.
        result = await agent.run(prompt)
        return result.output.suggested_title

    DBOS.launch()

    async def run() -> None:
        handle = await DBOS.start_workflow_async(probe_workflow, "Synthetic persona.")
        print("probe result received:", bool(await handle.get_result()), flush=True)

    asyncio.run(run())
    DBOS.destroy()


if __name__ == "__main__":
    main()
