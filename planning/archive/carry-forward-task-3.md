# Carried into Task 3 (from Task 1 review)
- M4: crash after accepted output re-calls the model and loses the first attempt's usage. Check for an existing accepted output before resolving inputs; record usage atomically with accept_output.
- M7: split the Meta model factory and budget policy out of the spike CLI module (spikes/meta/live_spike.py) into identity/execution.
- ADR 0002 decision 7: an app-DB outage during begin_attempt/finish_attempt escapes the step (run stays queued, DBOS ERROR). Production version must keep failures typed and terminal.
- Worker shutdown hang seen 1/19 runs (cause unknown; kill-on-timeout mitigation). `make stop` must be bounded and never hang.
- ADR 0002 decision 2: runtime connects with non-owner roles (owners bypass RLS); migration-owner roles used only by setup.
- Ruling: the Contributor test model (muse-spark-1.3-contributor, Meta may train on traffic) may only be used for workspaces marked synthetic/public. Enforce this in code: refuse the test model for any non-synthetic workspace. Production path uses the non-contributor production model.
