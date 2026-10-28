# ESCO test sample (a reduced copy of ESCO v1.2.1, for tests only)

`esco-v1.2.1-en-csv-sample.zip` is a **modified (reduced) version of ESCO**, marked as such
under ESCO's reuse condition 2. It is real ESCO content, not synthetic data, but it is not
the catalogue: the product imports the full pinned release (`docs/dependencies.md`,
"Reference data"), and the test suite imports this sample so it needs no network. In the
database and the API it is labelled `sample: true`.

This service uses the ESCO classification of the European Commission. Licence: Commission
Decision 2011/833/EU on the reuse of Commission documents.

| | |
|---|---|
| File | `esco-v1.2.1-en-csv-sample.zip`, 76,049 bytes |
| SHA-256 | `747c5638653e0594c0ae4210db1ee0c90eccb5c872f356fdfa36116bb56f955d` (pinned in `backend/tests/support/esco.py`) |
| Built from | `esco-v1.2.1-classification-en-csv.zip`, SHA-256 `f9761b0b…deb3e` |
| Built by | `cd backend && uv run --locked python -m tools.esco_sample` (deterministic: sorted members, fixed timestamps; rebuilding gives the same hash) |
| Contents | 6 of the release's CSV files, every kept row byte-for-byte the release's, all columns |

What it keeps (`SELECTED` in `backend/tools/esco_sample.py`):

- 30 occupations: the named ones, chosen for the persona fixtures, the interview contract
  and the retrieval tests, plus each one's chain of broader occupations. They include two
  specialists in one ISCO-08 unit group (ICT help desk agent and manager, 3512), two
  occupations sharing an alternative label ("bus operator": bus driver, trolley bus driver)
  and one with hidden, search-only labels (general practitioner).
- Their ISCO-08 groups with every ancestor (70 groups) and the ISCO hierarchy rows.
- For each occupation, its first 6 essential and 2 optional skills in the release's order
  (200 distinct skills; one is listed twice by the release with only its modified date
  changed, as in the full release), and the skill-skill relations among them.

Change it only by editing `SELECTED` and rebuilding; then update the pin and the counts the
tests assert.
