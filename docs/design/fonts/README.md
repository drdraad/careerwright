# Fonts (ruling R8)

Two self-hosted families, both under the SIL Open Font License 1.1. Each licence text sits
beside its font file. The files are the upstream binaries, unmodified: no subsetting,
renaming of internal names or format conversion. That keeps clear of Source Sans 3's
Reserved Font Name ("Source"), which a modified version could not use.

| Role | Family | File | Upstream source (pinned commit) | Version | SHA-256 |
|---|---|---|---|---|---|
| Body and interface: humanist sans | Source Sans 3 (variable, `wght` 200–900) | `source-sans-3/SourceSans3-Variable.ttf` | `google/fonts` @ `914ec116571b1162d886aa402e715552221f0b77`, `ofl/sourcesans3/SourceSans3[wght].ttf` | 3.052 | `042fe2cc0b933e328410d7acbd0aa6a1873dca5aef81875f4bc214b08825c7b9` |
| Display: restrained serif | Newsreader (variable, `wght` 200–800, `opsz` 6–72) | `newsreader/Newsreader-Variable.ttf` | `google/fonts` @ `8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5`, `ofl/newsreader/Newsreader[opsz,wght].ttf` | 1.003 | `8a08d13f8a6c0d51be379a60af84f945f65369a67e509ee3c3bdcc421254d7c1` |

| Licence file | SHA-256 | Copyright line |
|---|---|---|
| `source-sans-3/OFL.txt` | `09746787287a289323b0ec3cff4d1a4a801331b82b7207c1e186f5d26619a392` | Copyright 2010-2020 Adobe, with Reserved Font Name 'Source' |
| `newsreader/OFL.txt` | `fdfad38143ec470553cae82a1e45320bdd1b9ec70415d37bd0171051d8a4ded8` | Copyright 2020 The Newsreader Project Authors |

Only the file names were shortened (the brackets in the upstream names are awkward in
URLs). Renaming a file does not change the font.

## Why these two

- **Source Sans 3** is a humanist sans, as spec section 14 asks. Its default figures are
  tabular: all ten digits share one advance width (472 units, measured with fontTools
  4.60.1). Money and months therefore align in tables without a feature switch, and
  `font-variant-numeric: tabular-nums` is harmless. It has a slashed zero (`zero`), ten
  stylistic sets and about 2,500 glyphs. That covers `£ – — ’ … × ≤ ≥ ·` and leaves room
  for later locales.
- **Newsreader** is a quiet editorial serif with an optical-size axis. At display sizes
  and light weights (about 340), its fine strokes echo the thin branches of the map and
  the route chart. It is used only for questions, page titles and card titles, never for
  numbers in tables.

Atkinson Hyperlegible Next (OFL) was also inspected. Its legibility is excellent, but its
design brief places it in the grotesque tradition rather than the humanist one, so it was
not chosen for body text.

## Verified

- Both families load in the compositions: `document.fonts.check()` passes for every
  capture in `../screenshots/checks.md`.
- Feature and glyph inspection used `uv run --no-project --with fonttools==4.60.1` on the
  downloaded files (2026-10-27).

## For the web app (Task 4)

Copy both directories, licence files included, into the app's public assets. The variable
TTFs are about 1.1 MB together. If load time matters, use the WOFF2 builds from the
upstream projects' own releases, rather than converting the files here.
