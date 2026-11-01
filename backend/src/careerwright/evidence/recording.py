"""Recording a source's job copies with their claims, each attached to a canonical job
(JOB-02, PROP-02; ADR 0009 decisions 5 and 6): the one path for the copies an acquisition
parsed and for those a page extraction's model read.

The caller holds the workspace's recording lock (`store.lock_workspace_records`) from before
the candidates are read until the merge, so a merge never deletes a job another run is
recording onto (review B N2).
"""

import uuid
from datetime import datetime

from careerwright.db import Tx
from careerwright.evidence import store
from careerwright.evidence.jobs import canonical_facts, facts_from_json, facts_json, jobs_joined
from careerwright.evidence.records import JobCopy


def record_copies(
    tx: Tx,
    *,
    workspace_id: uuid.UUID,
    attempt_id: uuid.UUID,
    provider: str,
    copies: list[JobCopy],
    at: datetime,
) -> None:
    """Each copy and its claims; a copy with an extraction error belongs to no job (it is
    never published). `at` is when the source was retrieved."""
    for copy in copies:
        facts = canonical_facts(copy, provider=provider)
        job_id: uuid.UUID | None = None
        if copy.extraction_error is None:
            # The grouping rule the property tests cover, over the candidates: a copy that
            # bridges stored jobs makes them one job, the oldest (JOB-02, PROP-02).
            candidates = store.candidate_copies(
                tx,
                workspace_id,
                provider=provider,
                source_job_id=copy.source_job_id,
                title_key=facts.title_key,
            )
            joined = jobs_joined([(job, facts_from_json(f)) for job, f in candidates], facts)
            if not joined:
                job_id = uuid.uuid4()
                store.insert_job(
                    tx, job_id=job_id, workspace_id=workspace_id, exemplar=False, at=at
                )
            else:
                job_id = joined[0]
                store.merge_jobs(tx, workspace_id, keep=job_id, merged=joined[1:])
                store.job_verified(tx, job_id, at)
        copy_id = uuid.uuid4()
        store.insert_copy(
            tx,
            copy_id=copy_id,
            workspace_id=workspace_id,
            job_id=job_id,
            attempt_id=attempt_id,
            provider=provider,
            copy=copy,
            facts=facts_json(facts),
        )
        store.insert_claims(
            tx,
            workspace_id=workspace_id,
            attempt_id=attempt_id,
            copy_id=copy_id,
            copy=copy,
            retrieved_at=at,
        )
