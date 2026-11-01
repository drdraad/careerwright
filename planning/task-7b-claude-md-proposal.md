# Task 7b: proposed CLAUDE.md wording (consolidated and shortened by the controller)

Applies on top of the slice 7B proposal (`task-7-sliceB-claude-md-proposal.md`).

## 1. Layout: extend slice 7B's `nessa/catalogue` description

Append before its closing parenthesis:

> ; and the England option pack, `option_pack.py` and `packs/england_option_pack/`,
> ADR 0011, whose version files, schema and session 2 package only
> `tools.option_pack_files` writes

## 2. Invariants: a new bullet after "Pay and AI evidence"

> - Option pack (ADR 0011): a committed version never changes; a correction or a review is
>   a new version with its own pin in `PINS`, loaded only through `load_pack`. Every field
>   cites a claim (value, span, excerpt) in its field's declared shape, or says why it is
>   unknown; where a page states two disagreeing values, the field stays unknown with both
>   kept. Session 2's question numbers are stable (Task 7c applies answers by number), and a
>   record becomes `reviewed` only when every one of its rows is answered yes. The accuracy
>   read reads development-split pages only.

## 3. Commands: after the live-calls bullet

> - Corpus runs (`tools.corpus`) pace within one process only: leave a host's rate limit
>   between runs.
