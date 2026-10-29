"""The early accuracy read (Task 7b; plan v1.2, "real evidence is the next proof of
progress"): the Task 7 pipeline's deterministic path (structured data only, no model call)
run once over the England option pack's development-split pages, scored field by field
against the pack's labels. The labels are unreviewed (H-07 is session 2), so the read is
labelled "unreviewed labels, development split". Holdout pages are never read (OI-09).

How each page is read. A page whose body is kept on this machine (`var/evidence/corpus/`)
is parsed as kept, after its SHA-256 is checked against the pack: exactly the labelled text.
A page kept as its hash and excerpts only is fetched once more through the product's own
pipeline (`acquire_page`): its copy can differ from the labelled one, so values are compared,
never offsets. An Adzuna slot is not scored: its labels are the API's own values, so the
score would only compare the adapter with itself. The deterministic path reads job postings
only (JSON-LD `JobPosting`): a course or funding page's labelled fields are all `missing`,
and a page it reads as a vacancy that is not one is reported.

Outcomes, per field: where the label states a value, `correct`, `incorrect` or `missing`
(the path gave none); where the label says the page leaves it unknown, `kept_unknown` or
`unsupported` (the path asserts a value the page does not support). Raw counts with their
denominators; 33 pages are too few for a rate to mean more (plan section 9).

Run from `backend/`: `uv run --locked python -m tools.accuracy_read`.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from nessa.catalogue.option_pack import Claim, JobPosting, Pack, Split, load_pack
from nessa.evidence.acquire import Pacer, acquire_page
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.pages import parse_page
from nessa.evidence.records import AdvertiserKind, JobCopy
from nessa.evidence.sources import load_manifest
from tools.localenv import REPO_ROOT

EVIDENCE_DIR = REPO_ROOT / "var" / "evidence" / "corpus"
PACK_VERSION = "0.1.0"
JOB_FIELDS = (
    "title",
    "employer",
    "advertiser",
    "location",
    "salary",
    "date_posted",
    "valid_through",
    "employment_type",
    "work_mode",
    "description_kind",
    "source_job_id",
)
# The words a label uses for each JSON-LD employment type the path reports.
EMPLOYMENT_WORDS = {
    "FULL_TIME": ("full-time", "full time"),
    "PART_TIME": ("part-time", "part time"),
    "CONTRACTOR": ("contract", "fixed-term", "fixed term"),
    "TEMPORARY": ("temporary",),
}


class Outcome(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    MISSING = "missing"
    KEPT_UNKNOWN = "kept_unknown"
    UNSUPPORTED = "unsupported"


def _text(value: object) -> str:
    return " ".join(str(value).split()).casefold()


def _same(field: str, read: object, label: object) -> bool:
    if field == "salary" and isinstance(label, dict) and isinstance(read, dict):
        keys = ("minimum_minor_units", "maximum_minor_units", "period", "basis")
        return all(read.get(k) == label.get(k) for k in keys)
    if field == "location" and isinstance(label, dict) and isinstance(read, str):
        return read in _text(label.get("label", "")) or _text(label.get("locality")) in read
    if field == "valid_through":
        return datetime.fromisoformat(str(read)) == datetime.fromisoformat(str(label))
    if field == "employment_type":
        stated = _text(label)
        return all(
            any(w in stated for w in EMPLOYMENT_WORDS.get(t, (t.casefold(),)))
            for t in str(read).split(",")
        )
    return _text(read) == _text(label)


def _read(job: JobCopy) -> dict[str, object]:
    """What the path asserts for each field. The hiring employer is the product's own
    reading (`jobs.canonical_facts`): an agency's name is never the employer."""
    location = job.locations[0] if job.locations else None
    return {
        "title": job.title,
        "employer": job.employer if job.advertiser is not AdvertiserKind.AGENCY else None,
        "advertiser": None if job.advertiser is AdvertiserKind.UNKNOWN else job.advertiser.value,
        "location": _text(location.locality or location.label) if location else None,
        "salary": job.salary.model_dump(mode="json") if job.salary else None,
        "date_posted": job.date_posted.isoformat() if job.date_posted else None,
        "valid_through": job.valid_through.isoformat() if job.valid_through else None,
        "employment_type": job.employment_type,
        "work_mode": job.work_mode.value if job.work_mode else None,
        "description_kind": job.description_kind.value if job.description_kind else None,
        "source_job_id": job.source_job_id,
    }


def score_job(job: JobCopy | None, labels: dict[str, object]) -> dict[str, Outcome]:
    """Each labelled field's outcome. `labels` maps a field to its labelled value: None (or
    "unknown" for the advertiser) when the page leaves it unknown."""
    read = _read(job) if job is not None else {}
    scores = {}
    for field, label in labels.items():
        got = read.get(field)
        unknown = label is None or (field == "advertiser" and label == "unknown")
        if unknown:
            scores[field] = Outcome.KEPT_UNKNOWN if got is None else Outcome.UNSUPPORTED
        elif got is None:
            scores[field] = Outcome.MISSING
        else:
            scores[field] = Outcome.CORRECT if _same(field, got, label) else Outcome.INCORRECT
    return scores


def job_labels(pack: Pack, record: JobPosting) -> dict[str, object]:
    """A posting's labelled value for each scored field; a field the page leaves unknown
    (an `Unknown` reference, or a claim whose value is null) is None."""
    claims = {c.claim_id: c for c in pack.claims}
    labels: dict[str, object] = {}
    for field in JOB_FIELDS:
        if field == "source_job_id":
            ids = [f for f in record.facts if claims[f].field == "source_job_id"]
            labels[field] = claims[ids[0]].value if ids else None
            continue
        ref = getattr(record, field)
        labels[field] = pack.value(ref)
    return labels


def _record_claims(pack: Pack, source_id: str) -> list[Claim]:
    return [c for c in pack.claims if c.source_id == source_id]


def _copies(
    pack: Pack, source_id: str, fetcher: Fetcher, pacer: Pacer, evidence_dir: Path
) -> tuple[list[JobCopy], str]:
    """The path's postings for a page, and how it was read."""
    source = next(s for s in pack.sources if s.source_id == source_id)
    kept = evidence_dir / source_id / f"{source.sha256}.html"
    if kept.is_file():
        body = kept.read_bytes()
        if hashlib.sha256(body).hexdigest() != source.sha256:
            raise SystemExit(f"{source_id}: the kept body is not the labelled text")
        parsed = parse_page(body.decode(), sha256=source.sha256, page_url=source.final_url or "")
        return parsed.postings, "kept body (the labelled text)"
    result = acquire_page(fetcher, pacer, source.url, now=datetime.now(UTC))
    same = "the same text" if result.content_sha256 == source.sha256 else "a different copy"
    how = f"fetched again ({result.status.value} {result.http_status}; {same})"
    return result.copies, how


def read(
    pack: Pack,
    *,
    fetcher: Fetcher | None = None,
    pacer: Pacer | None = None,
    evidence_dir: Path = EVIDENCE_DIR,
) -> dict[str, object]:
    """One fetcher and one pacer for the whole read, so each host's rate limit holds across
    its pages (spec section 6) and its robots.txt is read once. `evidence_dir`: where kept
    bodies are looked for."""
    fetcher = fetcher or Fetcher(user_agent=load_manifest().user_agent)
    pacer = pacer or Pacer()
    pages: list[dict[str, object]] = []
    totals: Counter[tuple[str, str]] = Counter()
    by_field: Counter[tuple[str, str]] = Counter()
    for source in pack.sources:
        if source.split is not Split.DEVELOPMENT:
            continue
        if source.route.value == "adzuna":
            pages.append({"slot": source.source_id, "read": "not scored: Adzuna labels"})
            continue
        copies, how = _copies(pack, source.source_id, fetcher, pacer, evidence_dir)
        entry: dict[str, object] = {"slot": source.source_id, "kind": source.kind.value}
        entry["read"] = how
        entry["postings_read"] = len(copies)
        if source.kind.value == "job_posting":
            record = next(j for j in pack.job_postings if j.source_id == source.source_id)
            scores = score_job(copies[0] if copies else None, job_labels(pack, record))
            entry["fields"] = {f: o.value for f, o in scores.items()}
            for field, outcome in scores.items():
                totals[(source.kind.value, outcome.value)] += 1
                by_field[(field, outcome.value)] += 1
        else:
            labelled = [c for c in _record_claims(pack, source.source_id) if c.value is not None]
            entry["fields"] = {"labelled_values": len(labelled), "read": 0}
            totals[(source.kind.value, Outcome.MISSING.value)] += len(labelled)
            if copies:
                entry["read_as_vacancy"] = copies[0].title
        pages.append(entry)
    return {
        "label": "unreviewed labels, development split",
        "pack_version": pack.pack_version,
        "run_at": datetime.now(UTC).isoformat(),
        "pages": pages,
        "totals": {f"{k[0]}:{k[1]}": n for k, n in sorted(totals.items())},
        "by_field": {f"{k[0]}:{k[1]}": n for k, n in sorted(by_field.items())},
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-version", default=PACK_VERSION)
    parser.add_argument("--out", type=Path, default=None, help="also write the JSON here")
    args = parser.parse_args(argv)
    result = read(load_pack(args.pack_version))
    text = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if args.out:
        args.out.write_text(text + "\n")
    print(text)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
