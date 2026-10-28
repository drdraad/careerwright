# Fixtures

Everything here is **synthetic**. No file is evidence about a real person, course, price,
regulator or vacancy, and no fixture may fill a missing live field (Global Constraint 5).

## `m0/`: the supplied M0 fixture pack (original, unchanged)

Extracted from `Nessa_M0_Fixtures.zip` at the repository root. The files are byte-identical
to the archive members (checked with `shasum -a 256` on 2026-10-27; do not edit them; if the
pack changes, re-extract it and re-run the hand check).

| File | SHA-256 |
|---|---|
| `Nessa_M0_Fixtures.zip` (archive) | `7d166655ed883e5bfe2365437a6a2959df17baafe8f6966af2c970e44c205380` |
| `README.txt` | `bb1af8bd8b693cdd2e58b2e060029bedf1f6f1f23fe91680122427c112e8135c` |
| `personas/P01.json` | `03e72eefa7f975fc50c075a17f2136a0f39385efce25ccdb2834b5f9a5ec518e` |
| `personas/P02.json` | `ae78009ca6b1c85cf1d705f9a6bc046409600a12ef21acacdfb22ddf4b97dd52` |
| `personas/P03.json` | `5fb3c10a1f5bf18fa062c7707954cc52b448540ea4ae25effee7479ee68903a5` |
| `personas/P04.json` | `55e3374d31c086d881a5b79c21f54c2c2658a27b8ce9f6cd2267120d0dbb8e49` |
| `personas/P05.json` | `0de595503c786f42f01fdc2127433e4c37697ea28b541a4f81e2b38b19de0771` |
| `worked_trace.json` (TRACE-01) | `05f72958c99765684156d091c421e822855bb0150f220ad97a3b6c97db1895a5` |
| `source_corpus_manifest.json` | `d6d5f68dbdaf46b65fd75e7df432413fb6415a7bdf3fa1a07c024f08033c5988` |
| `validate_fixtures.py` | `b40e14aa7333de9df1e0fcadc12fdeb92786612595af2be4e84208539eb33e70` |

Run the pack's own validator (standard library only):

```bash
cd backend && uv run python -I ../fixtures/m0/validate_fixtures.py
```

It checks the pack's internal arithmetic and stated invariants. It does not test the
application. The independent hand check is `docs/evidence/fixture-hand-check.md`.

## `reconstructed/`: fixtures rebuilt from the specification

The pack has no A–I direct-spend file. `reconstructed/directai.json` is rebuilt from spec
v1.2 section 12 ("The three Pareto layers") and section 20 (TEST-1), under ruling R1. It
carries `"reconstructed": true`, uses the `DIRECTAI` namespace (route IDs
`fixture:directai:route:A` … `I`) and never shares IDs or economic-cost labels with
TRACE-01 (plan section 8). It holds only what the specification states: months, total
direct cost and expected layer. Schedules, dates and ledgers are listed as not specified
rather than invented.

## `esco-sample/`: a reduced copy of ESCO for tests

Not synthetic: a labelled, hash-pinned subset of the official ESCO v1.2.1 release, so the
test suite imports a taxonomy without the network. The product imports the full release,
which `make setup` fetches (ruling R7). Details, licence and derivation:
`esco-sample/README.md`.

## Rules for using these fixtures

- Namespace the two route fixtures separately: `TRACE-01` routes are economic-cost mode,
  `DIRECTAI` routes are direct-spending mode.
- Tests assert contracts and semantic outcomes, never exact LLM prose (pack README).
- The source corpus is not here. Its manifest is `corpus/manifest.json`; synthetic personas
  never substitute for real-source extraction cases.
