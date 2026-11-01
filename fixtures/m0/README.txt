Nessa v1.2 - M0 contract fixtures

All personas, training prices, course outcomes and regulatory records in this
pack are synthetic. IDs with fixture: are not real ESCO or regulator IDs.
The planning date is hypothetical, not a claim about current availability.

Contents:
- personas/P01-P05.json: sure/unsure, employed/unemployed, low-budget,
  regulated-target and returner scenarios with expected domain behaviour.
- worked_trace.json: profile -> requirements -> conditional outcomes ->
  five routes -> economic costs -> three Pareto fronts -> selected print data.
- source_corpus_manifest.json: the real extraction corpus still required.
- validate_fixtures.py: standard-library-only arithmetic/contract checks.

Run from any working directory:
    python3 /path/to/Nessa_M0_Fixtures/validate_fixtures.py

This script does not implement or end-to-end test the application, test live
providers, verify regulation, or establish model quality. It validates internal
fixture consistency and a few important mathematical counterexamples.

The implementation must connect these fixtures to API/UI tests, use a separate
small-instance exhaustive oracle for solver correctness, and collect permitted,
labelled real source cases. Do not replace real providers with fixture prices.

Application LLM tests should assert grounding and allowed semantic outcomes,
not exact prose. No API keys or other secrets belong in fixtures.
