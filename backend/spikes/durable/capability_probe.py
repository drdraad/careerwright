"""Negative control: what Pydantic AI's DBOSDurability capability journals by itself.

Runs the naive composition (agent with `DBOSDurability`, `agent.run()` inside a DBOS
workflow, DBOS's default serializer) on a synthetic private prompt with the fake model, in
its own process and DBOS application. The leak scan must find the private model output in
the journal; if it did not, the scan would not be evidence of anything.
"""

import asyncio
import os
from pathlib import Path

from dbos import DBOS, DBOSConfig
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.durable_exec.dbos import DBOSDurability

from spikes.durable.models import fake_model_builder
from spikes.durable.store import AppStore
from spikes.durable.worker import keyring_from_file
from spikes.durable.workflow import ProfileProposal

PROBE_APP_NAME = "nessa-spike-capability-probe"


def main() -> None:
    store = AppStore(
        os.environ["NESSA_SPIKE_APP_URL"],
        keyring_from_file(Path(os.environ["NESSA_SPIKE_MASTER_KEY_FILE"])),
    )
    run_id = os.environ["NESSA_SPIKE_PROBE_RUN_ID"]
    config: DBOSConfig = {
        "name": PROBE_APP_NAME,
        "system_database_url": os.environ["NESSA_SPIKE_DBOS_URL"],
        "application_version": "probe-1",
    }
    DBOS(config=config)
    inputs = store.resolve_activity_inputs(run_id)
    agent = Agent(
        fake_model_builder()(inputs.api_key),
        name="nessa_spike_probe_agent",
        output_type=NativeOutput(ProfileProposal),
        capabilities=[DBOSDurability()],
    )

    @DBOS.workflow(name="nessa_spike.capability_probe")
    async def probe_workflow(probe_run_id: str) -> str:
        # Deliberately naive: private text enters the agent inside the workflow.
        result = await agent.run(store.resolve_activity_inputs(probe_run_id).private_text)
        return result.output.proposed_title

    DBOS.launch()

    async def run() -> None:
        handle = await DBOS.start_workflow_async(probe_workflow, run_id)
        print("probe result:", await handle.get_result(), flush=True)

    asyncio.run(run())
    DBOS.destroy()


if __name__ == "__main__":
    main()
