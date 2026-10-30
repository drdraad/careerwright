# Fonts (ruling R8)

Two self-hosted families, both under the SIL Open Font License 1.1. Each licence text sits
beside its font file. The files are the upstream binaries, unmodified: no subsetting,
renaming of internal names or format conversion. That keeps clear of Source Sans 3's
Reserved Font Name ("Source"), which a modified version could not use. Outfit has no
Reserved Font Name.

| Role | Family | File | Upstream source (pinned commit) | Version | SHA-256 |
|---|---|---|---|---|---|
| Body and interface: humanist sans | Source Sans 3 (variable, `wght` 200–900) | `source-sans-3/SourceSans3-Variable.ttf` | `google/fonts` @ `914ec116571b1162d886aa402e715552221f0b77`, `ofl/sourcesans3/SourceSans3[wght].ttf` | 3.052 | `042fe2cc0b933e328410d7acbd0aa6a1873dca5aef81875f4bc214b08825c7b9` |
| Display: bold geometric sans | Outfit (variable, `wght` 100–900) | `outfit/Outfit-Variable.ttf` | `google/fonts` @ `8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5` (committed 2026-03-12, 232 days old when taken on 2026-10-30), `ofl/outfit/Outfit[wght].ttf` (from `Outfitio/Outfit-Fonts` @ `902773808eb372f70fb34e8946dd1ffe604efc79`) | 1.100 | `fc7287273e66929776e2ba54f144fe699080bec29f61bf649d70d871468aeade` |

| Licence file | SHA-256 | Copyright line |
|---|---|---|
| `source-sans-3/OFL.txt` | `09746787287a289323b0ec3cff4d1a4a801331b82b7207c1e186f5d26619a392` | Copyright 2010-2020 Adobe, with Reserved Font Name 'Source' |
| `outfit/OFL.txt` | `c676351bf8576b9aba743cd5eaa8c0e7ee0d51f805d720447b4df4ddb6a2e416` | Copyright 2021 The Outfit Project Authors (https://github.com/Outfitio/Outfit-Fonts) |

Only the file names were shortened (the brackets in the upstream names are awkward in
URLs). Renaming a file does not change the font.

Newsreader, the Sprint 0 display serif, retired with the calm observatory (plan section 4,
ADR 0014). Its files are in git history before Sprint W.

## Why these two

- **Outfit** is the product owner's choice at session W1 ("Keep Outfit"), after the world
  spike compared it with Sora and Unbounded. It is a round geometric sans, the closest of the
  three to the bold white type in their reference image (`../reference/luminous-path-forward.png`),
  and the narrowest on long job names. It is used for headings, the world's names and the
  current question, at weight 650, never for numbers in tables. It has 416 glyphs covering
  `£ – — ’ … × ·` (not `≤ ≥`, which body text carries) and a `tnum` feature.
- **Source Sans 3** stays the body face: a highly readable sans at 16 px and up, as plan
  section 4 asks. Its default figures are tabular: all ten digits share one advance width
  (472 units, measured with fontTools 4.60.1), so money and months align without a feature
  switch. It has a slashed zero (`zero`) and about 2,500 glyphs. The spike set its words in
  Atkinson Hyperlegible Next; session W1 chose only the heading lettering. Keeping Source
  Sans 3 is **provisional, to confirm with the product owner at session W2** (ADR 0014,
  decision 6).

## Verified

- Both families load in the references and the app: `document.fonts.check()` passes for
  every capture in `../screenshots/checks.md` and the web app's visual checks.
- Glyph, version and feature inspection used `uv run --no-project --with fonttools==4.60.1`
  on the downloaded files (Source Sans 3 on 2026-10-27, Outfit on 2026-10-30).

## For the web app

`apps/web/src/design/fonts/` holds byte-identical copies, licence files included
(`apps/web/src/lib/designMirror.test.ts`). The variable TTFs are about 1.0 MB together.
