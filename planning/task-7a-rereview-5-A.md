# Task 7A, fix round 4: scoped re-review 5, security half (items 1–2)

**Scope.** Range `dcaac22..8eceb3b` (6 commits). Items 1 and 2 are in `5adcbcb`. I checked the rest of the delta only for any weakening of redaction, `apply_link` or `check_url`. Files were read with `git show`, and line numbers are at `8eceb3b`. The implementer's report was treated as unverified.

**What I ran (pure, no network, no page fetched, nothing in the repo modified).**
- `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/redaction_probe_6.py`, on `8eceb3b` sources extracted with `git archive`, using the backend venv's Python 3.12.12. It covers:
  - probe 5 in full: cases 1–17, C-I1's forms and the JavaScript escapes;
  - R4-1's two forms, plus three more split variants;
  - entity-encoded and percent-encoded `mailto:` links;
  - over-match shapes for question 1, using typical kept-class markup written by hand.
- Two short follow-ups: the meta tags separated, and a refined rule.

**Not run.** pytest, `make check` and `make acceptance`. The report says they passed; I have not verified that.

## Per-item verdicts

| Item | Verdict | Evidence |
|---|---|---|
| 1. Entities in attribute values give `attribute_detail` | Fixed | **Code.** `_attribute_shows_detail` (`pages.py:470-478`) reads every attribute value, with entities decoded by the parser, and normalises it before `redact_shown`. A hit sets `ATTRIBUTE_DETAIL` (`:531-532`; `records.py:137`), so the body is not kept. Migration 0025 widens the value CHECK only.<br>**Probe.** `mailto:` written in decimal entities, in hex entities and with named `&commat;`/`&period;`, and `tel:` with `&#160;` spaces, all give `attribute_detail`. The model input stays "Email us".<br>**Tests.** `test_redaction.py:343` (entity-encoded `mailto:`, no visible address) and `:357` (a plain `mailto:` is redacted in place and the body is kept).<br>**ADR.** Decision 4 (`:165`) is updated. A percent-encoded `mailto:` is still undetected (`body_not_kept=None`); it is recorded as a limit (`:175`) and ruled for round 5. |
| 2. R4-1: an email split by inline markup | Fixed (over-match: R5-1) | **Code.** `_SHOWN_EMAIL` and `redact_shown` (`redaction.py:52-55,86-90`) are used by:<br>- the kept-body check (`pages.py:459-468`);<br>- the attribute check;<br>- the model input (`:575`);<br>- the extraction quote check (`extraction.py:454`).<br>**Probe.** Both R4-1 forms, plus "TLD in `<b>`", "dot in a span" and a human-spaced address, give `visible_text_detail` on the kept body and `Write to [email removed] today.` in the model input. "Tickets are £5 @ the door…" is unchanged.<br>**Tests.** `test_redaction.py:324,335` and `test_extraction.py:163,172`. |

## Question 1: is the over-match routine on kept-class pages?

**Probe on typical markup:** only `5adcbcb` changes this, and the results were:

| Shape | Result |
|---|---|
| GOV.UK's footer (OGL licence text, Crown copyright, footer links) | No trigger |
| A "Contact us" block (plain email, phone, opening hours) | Redacted in place; body kept |
| Social links as icons or labelled links | No trigger |
| A bare handle link list (`@GOVUK Facebook`) | No trigger |
| A handle mid-sentence ("Follow @GOVUK on X") | No trigger |
| A handle with an underscore (`@NCS_Careers.`) | No trigger |
| `<meta name="twitter:site" content="@GOVUK">` | No trigger |
| Retina `logo@2x.png` | Already redacted in place by the text pass |
| A handle that ends a sentence before another ("Follow us on X @NCScareers. Find out more", "Follow @GOVUK. Sign up") | Triggers |
| A handle link followed by a "." text node | Triggers |
| "@" used for "at" before a new sentence ("Drop in @ 10am. Bring…", "Meet us @ Leeds. Doors…") | Triggers |
| A description, `og:description` or `alt` attribute holding a handle at a sentence end | Triggers, because the attribute check uses the same rule |

Each trigger costs the body, and "[email removed]" swallows the next sentence's first word in the model input. Nothing leaks.

**Judgement: not routine.** Standard GOV.UK and National Careers Service chrome does not trigger. GOV.UK's style guide also tells writers not to use "@" for "at". It will recur on news, campaign and social-prompt pages and in their meta descriptions.

**Tightest rule that still catches R4-1.** Treat a sentence boundary as never continuing a domain:
- After a dot that has whitespace after it, the next label must start with a lowercase letter (or, for a middle label, a digit).
- The TLD must not be followed by a letter, digit or hyphen.

As a regex:

```
DOT = (?:\.|\s+\.|\s*\.\s+(?=[a-z0-9]))   # TLD position: (?=[a-z])
[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9-]+(?:DOT[A-Za-z0-9-]+)*DOT[A-Za-z]{2,}(?![A-Za-z0-9-])
```

Probe results for this rule:
- It catches 7 of 7 splits: R4-1's two forms, TLD in `<b>`, dot in a span, human-spaced, an uppercase domain split by `<b>`, and a subdomain split.
- It over-matches none of the sentence shapes above.
- It still over-matches "@GOVUK. or email us": a lowercase sentence start, which edited prose rarely has.

## Question 2: where percent-decoding belongs

**For attributes:** in `pages._attribute_shows_detail` (`pages.py:470-478`). Apply `urllib.parse.unquote` to each value after the parser has decoded its entities and before `normalised_text`. This is for detection only: a hit means `attribute_detail`, and nothing is rewritten.

**Not in:**
- `redaction.redact_text` or `redact_shown`, which also run on JSON values and pasted text, where `%40` is not an address;
- `addresses` (`check_url`, `apply_link`), which must keep judging URLs as written.

**Also, for consistency (R5-2):** the JSON side's URL values (`NOT_TEXT`: `url`, `sameAs`, `image`, `logo`) need the same detection-only decode. Today they are not looked at at all: `redact_value` keeps them verbatim by design.

## Delta check (`dcaac22..8eceb3b`)

**No weakening found.**

| Area | What I checked |
|---|---|
| Redaction | Only `5adcbcb` touched `redaction.py` and `pages.py`. Every earlier probe result (cases 1–17, C-I1's forms, the escapes, the N-2 hosts) is unchanged on `8eceb3b`. |
| Extraction quote check | Now stricter: it uses `redact_shown`. |
| `apply_link`, `check_url` | `addresses.py` is untouched in the range. |
| Other code | `fetcher.py`, `acquire.py`, `adzuna.py`, `sources.py`, compose and the worker endpoint are untouched. The `extraction.py`, `extraction_runs.py` and `acquisition.py` changes (`033cc8e`, `b554df6`, `8d4e875`, `e6b8f66`) are pay, the spend ceiling, locks, the cancel answer and work mode. They make no URL write, change no redaction, and keep no new text. |
| Migrations | 0025 drops and re-adds only `body_not_kept`'s value CHECK. 0014's URL CHECKs and 0020's excerpts-only CHECK stay. |

## New issues

### Critical
None.

### Important
None.

### Minor

**R5-1. The spaced-email rule reads a sentence boundary as part of a domain.**
- **Where:** `redaction.py:52-55`, used at `pages.py:459-478,575` and `extraction.py:454`.
- **What:** The shapes listed in question 1 trigger it, and each costs a kept body and a word of the model input.
  - It is recorded in ADR decision 4 (`:180`) as a known over-match.
  - It is fail-safe: retention is lost, but nothing leaks.
- **Fix:** Adopt the refined rule in question 1. Test its two non-matches ("Follow @GOVUK. Sign up", "Drop in @ 10am. Bring photo ID.") beside R4-1's forms.

**R5-2. JSON values are looked at only as decoded JSON; this was already so, and item 1 now makes it inconsistent.**
- **Where:** `redaction.py:43-49` (`NOT_TEXT`), the `redact_value` string branch, `pages.py:491-534`.
- **What (probe):**
  - JSON-LD `"url": "mailto:jane@recruit.example"` is kept verbatim. The body is kept with the plain address, `body_not_kept=None`, while the same `mailto:` in an `href` is redacted.
  - An entity-encoded email inside a JSON-LD string (`"<p>Email jane&#64;recruit.example…</p>"`) stays in the kept body. It also stays in the description claim's excerpt, which is kept for every class.
- **Fix:**
  - In `redact_value`, also redact each string's `html.unescape` form. JSON is re-serialised whenever it changes, so spans stay consistent.
  - For `NOT_TEXT` URL values, detect only: entity- and percent-decode, then on a hit keep no body.
  - Add both cases to `test_redaction.py`.

**Counts:** 2 fixed, 0 partly fixed, 0 not fixed. Delta: no weakening of redaction, `apply_link` or `check_url`. New issues: 0 Critical, 0 Important, 2 Minor.
