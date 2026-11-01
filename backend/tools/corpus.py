"""The corpus pipeline: run one real page through the acquisition pipeline for the corpus
manifest (`corpus/manifest.json`; Task 7A for X01 and X02, Task 7b for the option pack's
pages).

The page goes through exactly what the product uses: the URL and address checks, the source
permission manifest, robots.txt, the bounded fetch and the structured parser. The session 1
rights policy decides what is kept: the body is written under the gitignored
`var/evidence/corpus/<slot>/` only for a class that may keep it privately (lines A1 to A5);
otherwise only its hash. `--rights-class` and `--terms` record an agent's classification of
the page (the terms quoted, `corpus/README.md` step 3), dated with the run's date. It
replaces the class the pipeline derived in either direction, before anything is kept, except
that it never keeps more of a page whose host the manifest lists than the manifest permits.
Class `other` needs no terms and stays "pending human rights review".

It prints the manifest record (URL, retrieval time, HTTP status, content type, SHA-256, the
attempt's status and reason, rights status, retention, and each posting's claims as field,
value, offsets and a minimal excerpt) for the person curating to place in the manifest. It
never edits the manifest itself. `--locate EXCERPT` (repeatable) gives each of a label's
excerpts its offsets in the text whose hash is recorded, also for a page whose class keeps no
body: the page is held in memory for that only, never written.

`--context N` (at most `MAX_CONTEXT`) also prints each located span with up to N characters
either side, so a minimal excerpt can be cut from a page whose body is not kept.

`--batch PLAN` runs a JSON list of pages instead (each `{slot, url, rights_class?, terms?,
locate?, context?}`, the options of one `--url` run), every entry checked before the first
fetch, in order through one fetcher and one pacer, so each host's rate limit holds across
them. A page that fails is recorded with its failure and the batch goes on.

`--adzuna WHAT WHERE` runs one Adzuna search instead (the option pack's predicted-pay and
snippet slots, Task 7b): through `make live-adzuna`'s own path (`tools.live_adzuna.search`:
the product's adapter, the `live-adzuna` scope's cap, a ledger row at $0, the leak scan), its
class the manifest's job board, so only its hash and the claims' excerpts (JSON pointers).

`--proxy URL --proxy-ca PATH` (every mode; in a batch, for every page) fetch through an
explicit HTTPS proxy (`tools.fetch_proxy`): the proxy then picks each address, so the record
says `via_proxy` true and `address_checked` false; every other check runs as above.

Run from `backend/`: `uv run --locked python -m tools.corpus --slot J12 --url https://...`
or `... --slot J03 --adzuna "bookkeeping assistant" Leeds`, or `... --batch plan.json`.
"""

import argparse
import base64
import hashlib
import json
import re
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, TypeAdapter, model_validator

from careerwright.evidence.acquire import AcquisitionResult, Pacer, acquire_adzuna, acquire_page
from careerwright.evidence.addresses import CheckedUrl, UrlRefusal
from careerwright.evidence.adzuna import AdzunaQuery
from careerwright.evidence.fetcher import Admit, Fetched, Fetcher, FetchFailure
from careerwright.evidence.pages import redact_page
from careerwright.evidence.records import ClaimValue, Retention, RightsClass
from careerwright.evidence.sources import (
    PENDING_REVIEW,
    PageRights,
    classify_page,
    is_listed,
    retention,
)
from tools.fetch_proxy import add_arguments as add_proxy_arguments
from tools.fetch_proxy import fetcher_from, route_fields
from tools.live_adzuna import Acquire, AdzunaSettings, missing_credentials, search
from tools.localenv import REPO_ROOT
from tools.usage_ledger import Ledger

EVIDENCE_DIR = REPO_ROOT / "var" / "evidence" / "corpus"
ADZUNA_RESULTS = 50  # one page of Adzuna's largest size: the fewest requests for a slot
MAX_HITS = 5  # spans listed per excerpt (a label needs one); its count is always the real one
MAX_CONTEXT = 100  # characters either side of a located span, at most


def agent_classification(
    rights_class: RightsClass | None, terms: str | None, on: date, *, requested_host: str
) -> Callable[[str], PageRights]:
    """The page's class from its final host: the agent's dated classification when one is
    given, in either direction, else the manifest's. It never keeps more of a page whose host
    the manifest lists than the manifest permits (a listed board stays reference only), and
    it holds only for the host the agent classified: a page a redirect took elsewhere gets
    the manifest's class, its rights status naming both hosts (re-review A M-6)."""
    if rights_class is None:
        return classify_page
    if rights_class is not RightsClass.OTHER and not terms:
        raise SystemExit("a class other than `other` needs --terms (quoted and dated)")
    kept = retention(rights_class)

    def classify(host: str) -> PageRights:
        listed = classify_page(host)
        if host != requested_host:
            moved = f"{listed.rights_status} [classified {requested_host}; the page is on {host}]"
            return PageRights(listed.rights_class, moved, listed.retention)
        if is_listed(host) and kept is Retention.BODY and listed.retention is not Retention.BODY:
            return listed
        if rights_class is RightsClass.OTHER:
            return PageRights(RightsClass.OTHER, PENDING_REVIEW, Retention.EXCERPTS)
        status = f"{rights_class.value}: {terms} (classified by the curating agent on {on})"
        return PageRights(rights_class, status, kept)

    return classify


def record(result: AcquisitionResult) -> dict[str, object]:
    return {
        "url": result.requested_url,
        "final_url": result.final_url,
        "retrieved_at": result.fetched_at.isoformat(),
        "attempt": {"status": result.status.value, "reason": result.reason},
        "http_status": result.http_status,
        "content_type": result.content_type,
        "sha256": result.content_sha256,
        "byte_count": result.byte_count,
        "rights_status": result.rights_status or "pending human rights review",
        "retention": result.retention.value if result.retention else None,
        "extraction": result.extraction.value if result.extraction else None,
        "postings": [
            {
                "title": copy.title,
                "advertiser": copy.advertiser.value,
                "extraction_error": copy.extraction_error,
                "claims": [
                    {
                        "field": c.field.value,
                        "value": TypeAdapter(ClaimValue).dump_python(c.value, mode="json"),
                        "start": c.span.start,
                        "end": c.span.end,
                        "pointer": c.span.pointer,
                        "excerpt": c.span.excerpt[:120],
                        "validation": c.validation.value,
                        "issue": c.issue,
                    }
                    for c in copy.claims
                ],
            }
            for copy in result.copies
        ],
    }


class _Witness(Fetcher):
    """The fetcher, keeping in memory (never on disk) the last page it fetched, so that a
    label's excerpts can be located in exactly the text that was hashed, also for a page
    whose class keeps no body."""

    def __init__(self, inner: Fetcher) -> None:  # delegates: no state of its own to set up
        self._inner = inner
        self.page: Fetched | None = None

    def check(self, url: str) -> CheckedUrl | UrlRefusal:
        return self._inner.check(url)

    @property
    def via_proxy(self) -> bool:
        return self._inner.via_proxy

    def fetch_page(self, url: str, admit: Admit | None = None) -> Fetched | FetchFailure:
        result = self._inner.fetch_page(url, admit)
        if isinstance(result, Fetched):
            self.page = result
        return result


def locate(text: str, excerpts: Sequence[str], *, context: int = 0) -> list[dict[str, object]]:
    """Each excerpt's occurrences in the hashed text: their real count, and the first few
    (`MAX_HITS`) as character offsets with the exact text there. Whitespace in an excerpt
    matches any run of whitespace, since markup breaks lines where a reader sees one space;
    nothing else is loosened. `context`: also the hit with up to that many characters either
    side, as offsets and text, so a minimal excerpt can be cut from a page whose body is not
    kept (at most `MAX_CONTEXT`: a span's neighbourhood, never the page)."""
    found: list[dict[str, object]] = []
    for excerpt in excerpts:
        words = excerpt.split()
        pattern = re.compile(r"\s+".join(re.escape(w) for w in words)) if words else None
        hits = list(pattern.finditer(text)) if pattern else []
        located: dict[str, object] = {
            "excerpt": excerpt,
            "count": len(hits),
            "offsets": [[m.start(), m.end()] for m in hits[:MAX_HITS]],
            "texts": [m.group() for m in hits[:MAX_HITS]],
        }
        if context:
            around = min(context, MAX_CONTEXT)
            spans = [
                (max(0, m.start() - around), min(len(text), m.end() + around))
                for m in hits[:MAX_HITS]
            ]
            located["contexts"] = [[s, e, text[s:e]] for s, e in spans]
        found.append(located)
    return found


def acquire_for_corpus(
    slot: str,
    url: str,
    *,
    fetcher: Fetcher,
    rights_class: RightsClass | None = None,
    terms: str | None = None,
    evidence_dir: Path = EVIDENCE_DIR,
    excerpts: Sequence[str] = (),
    context: int = 0,
    pacer: Pacer | None = None,
) -> dict[str, object]:
    """`excerpts`: a label's minimal excerpts, each located (`located`) in the text whose
    hash is recorded, which is the pipeline's own redaction of the page it retrieved, with
    `context` characters either side when asked for (`locate`). `pacer`: a batch's own, so
    its rate limits hold across its pages; else this page's alone."""
    now = datetime.now(UTC)
    checked = fetcher.check(url)
    requested_host = checked.host if isinstance(checked, CheckedUrl) else ""
    classify = agent_classification(rights_class, terms, now.date(), requested_host=requested_host)
    witness = _Witness(fetcher)
    result = acquire_page(witness, pacer or Pacer(), url, now=now, classify=classify)
    body_path = None
    if result.body_b64 is not None and result.retention is Retention.BODY:
        directory = evidence_dir / slot
        directory.mkdir(parents=True, exist_ok=True)
        body_path = directory / f"{result.content_sha256}.html"
        body_path.write_bytes(base64.b64decode(result.body_b64))
    out = record(result) | route_fields(fetcher)
    shown = body_path and (
        body_path.relative_to(REPO_ROOT) if body_path.is_relative_to(REPO_ROOT) else body_path
    )
    out["kept_body"] = str(shown) if shown else None
    if excerpts and witness.page is not None and result.content_sha256 is not None:
        hashed = redact_page(witness.page.text).text
        if hashlib.sha256(hashed.encode()).hexdigest() != result.content_sha256:
            raise SystemExit("the located text is not the text whose hash is recorded")
        out["located"] = locate(hashed, excerpts, context=context)
    return out


class BatchEntry(BaseModel):
    """One page of a batch: the options of a single `--url` run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    slot: str = Field(min_length=1)
    url: str = Field(min_length=1)
    rights_class: RightsClass | None = None
    terms: str | None = None
    locate: tuple[str, ...] = ()
    context: int = Field(default=0, ge=0, le=MAX_CONTEXT)

    @model_validator(mode="after")
    def _a_class_names_its_terms(self) -> "BatchEntry":
        if self.rights_class not in (None, RightsClass.OTHER) and not self.terms:
            raise ValueError(f"{self.slot}: a class other than `other` needs terms")
        return self


def load_batch(plan: str | bytes) -> list[BatchEntry]:
    """A batch plan (a JSON list of entries), every entry checked before any page is
    fetched."""
    return TypeAdapter(list[BatchEntry]).validate_json(plan)


def corpus_batch(
    entries: Sequence[BatchEntry],
    *,
    fetcher: Fetcher,
    pacer: Pacer | None = None,
    evidence_dir: Path = EVIDENCE_DIR,
) -> list[dict[str, object]]:
    """Every entry's page through `acquire_for_corpus`, in order, with one fetcher and one
    pacer, so each host's rate limit holds across the batch (Task 7b's capture loops did not).
    A page that fails is recorded with its failure and the batch goes on."""
    pacer = pacer or Pacer()
    return [
        {
            "slot": entry.slot,
            **acquire_for_corpus(
                entry.slot,
                entry.url,
                fetcher=fetcher,
                rights_class=entry.rights_class,
                terms=entry.terms,
                evidence_dir=evidence_dir,
                excerpts=entry.locate,
                context=entry.context,
                pacer=pacer,
            ),
        }
        for entry in entries
    ]


def adzuna_for_corpus(
    slot: str,
    query: AdzunaQuery,
    credentials: tuple[SecretStr, SecretStr],
    ledger: Ledger,
    *,
    acquire: Acquire = acquire_adzuna,
    fetcher: Fetcher | None = None,
) -> dict[str, object]:
    """One Adzuna search for a slot, through `make live-adzuna`'s own capped, ledgered path
    (the product's adapter; the `live-adzuna` scope's cap; the leak scan). Its class is the
    manifest's (`api.adzuna.com`, a job board): the hash and the claims' excerpts, never the
    response. The record fails when the scan finds a credential in it."""
    searched = search(
        credentials, ledger, (query,), acquire=acquire, fetcher=fetcher, purpose=f"corpus {slot}: "
    )
    [result] = searched.results
    out = record(result) | route_fields(fetcher)
    out["total_matching"] = result.total
    out["kept_body"] = None
    out["leak_scan"] = {"cells": searched.cells, "findings": searched.findings}
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", help="the manifest slot, e.g. J12 or X01")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument(
        "--adzuna", nargs=2, metavar=("WHAT", "WHERE"), help="one Adzuna search (50 results)"
    )
    source.add_argument(
        "--batch",
        type=Path,
        metavar="PLAN",
        help="a JSON list of pages ({slot, url, rights_class?, terms?, locate?, context?}), "
        "fetched in order with one pacer",
    )
    parser.add_argument("--rights-class", type=RightsClass, default=None)
    parser.add_argument("--terms", default=None, help="the terms relied on, quoted and dated")
    parser.add_argument(
        "--locate",
        action="append",
        default=[],
        metavar="EXCERPT",
        help="a label's excerpt to locate in the hashed text (repeat for each)",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=0,
        choices=range(MAX_CONTEXT + 1),
        metavar=f"0-{MAX_CONTEXT}",
        help="characters either side of each located excerpt to print",
    )
    add_proxy_arguments(parser)
    args = parser.parse_args(argv)
    fetcher = fetcher_from(args, parser)
    if args.batch:
        if args.slot or args.rights_class or args.terms or args.locate or args.context:
            parser.error("a batch takes each page's options from its plan")
        entries = load_batch(args.batch.read_bytes())
        batch = corpus_batch(entries, fetcher=fetcher)
        print(json.dumps(batch, indent=2, ensure_ascii=False))
        return
    if not args.slot:
        parser.error("--url and --adzuna need --slot")
    if args.adzuna:
        if args.rights_class or args.terms:
            parser.error("an Adzuna search takes the manifest's class: no --rights-class")
        settings = AdzunaSettings()
        if settings.app_id is None or settings.app_key is None:
            print(json.dumps(missing_credentials(settings), indent=2))
            sys.exit(2)
        what, where = args.adzuna
        query = AdzunaQuery(what=what, where=where, results_per_page=ADZUNA_RESULTS)
        out = adzuna_for_corpus(
            args.slot, query, (settings.app_id, settings.app_key), Ledger(), fetcher=fetcher
        )
    else:
        out = acquire_for_corpus(
            args.slot,
            args.url,
            fetcher=fetcher,
            rights_class=args.rights_class,
            terms=args.terms,
            excerpts=args.locate,
            context=args.context,
        )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.stdout.flush()
    leak: Any = out.get("leak_scan")
    if leak and leak["findings"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
