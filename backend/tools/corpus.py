"""The corpus pipeline: run one real page through the acquisition pipeline for the corpus
manifest (`corpus/manifest.json`; Task 7A for X01 and X02, Task 7b for the option pack's
pages).

The page goes through exactly what the product uses: the URL and address checks, the source
permission manifest, robots.txt, the bounded fetch and the structured parser. The session 1
rights policy decides what is kept: the body is written under the gitignored
`var/evidence/corpus/<slot>/` only for a class that may keep it privately (lines A1 to A5);
otherwise only its hash. `--rights-class` and `--terms` record an agent's classification of
a page the manifest does not list (the terms quoted and dated, `corpus/README.md` step 3);
class `other` is never named and stays "pending human rights review".

It prints the manifest record (URL, retrieval time, HTTP status, content type, SHA-256, the
attempt's status and reason, rights status, retention, and each posting's claims as field,
offsets and a minimal excerpt) for the person curating to place in the manifest. It never
edits the manifest itself.

Run from `backend/`: `uv run --locked python -m tools.corpus --slot J12 --url https://...`.
"""

import argparse
import base64
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from nessa.evidence.acquire import AcquisitionResult, Pacer, acquire_page
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.records import Retention, RightsClass
from nessa.evidence.sources import load_manifest, retention
from tools.localenv import REPO_ROOT

EVIDENCE_DIR = REPO_ROOT / "var" / "evidence" / "corpus"


def classified(
    result: AcquisitionResult, rights_class: RightsClass | None, terms: str | None
) -> AcquisitionResult:
    """An agent's classification of a page outside the manifest replaces the default; a
    page the manifest lists keeps its own class."""
    if rights_class is None or result.rights_class not in (None, RightsClass.OTHER):
        return result
    if rights_class is RightsClass.OTHER or not terms:
        raise SystemExit("a class other than `other` needs --terms (quoted and dated)")
    kept = retention(rights_class)
    return result.model_copy(
        update={
            "rights_class": rights_class,
            "rights_status": f"{rights_class.value}: {terms}",
            "retention": kept,
            "body_b64": result.body_b64 if kept is Retention.BODY else None,
        }
    )


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
        "issues": result.issues,
        "postings": [
            {
                "title": copy.title,
                "extraction_error": copy.extraction_error,
                "claims": [
                    {
                        "field": c.field.value,
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


def acquire_for_corpus(
    slot: str,
    url: str,
    *,
    fetcher: Fetcher,
    rights_class: RightsClass | None = None,
    terms: str | None = None,
    evidence_dir: Path = EVIDENCE_DIR,
) -> dict[str, object]:
    result = classified(
        acquire_page(fetcher, Pacer(), url, now=datetime.now(UTC)), rights_class, terms
    )
    body_path = None
    if result.body_b64 is not None and result.retention is Retention.BODY:
        directory = evidence_dir / slot
        directory.mkdir(parents=True, exist_ok=True)
        body_path = directory / f"{result.content_sha256}.html"
        body_path.write_bytes(base64.b64decode(result.body_b64))
    out = record(result)
    shown = body_path and (
        body_path.relative_to(REPO_ROOT) if body_path.is_relative_to(REPO_ROOT) else body_path
    )
    out["kept_body"] = str(shown) if shown else None
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", required=True, help="the manifest slot, e.g. J12 or X01")
    parser.add_argument("--url", required=True)
    parser.add_argument("--rights-class", type=RightsClass, default=None)
    parser.add_argument("--terms", default=None, help="the terms relied on, quoted and dated")
    args = parser.parse_args(argv)
    fetcher = Fetcher(user_agent=load_manifest().user_agent)
    out = acquire_for_corpus(
        args.slot, args.url, fetcher=fetcher, rights_class=args.rights_class, terms=args.terms
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
