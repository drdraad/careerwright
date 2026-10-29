"""Build the committed ESCO test sample from the full pinned release (ruling R7).

The test suite runs without the network, so it imports a small, labelled subset of the
official ESCO v1.2.1 English CSV package instead of the release itself: the occupations
whose preferred label is in `SELECTED`, their ISCO-08 groups with every ancestor, their
broader occupations, a bounded number of their skills and the relations among what is
kept. Every kept row is value-for-value the release's row (all columns; the CSV is written
again, so quoting and line endings may differ). The output is deterministic (sorted, fixed
timestamps), so rebuilding gives the same SHA-256.

The sample is a modified (reduced) version of ESCO and says so (ESCO's reuse condition 2).
It is for tests only: the product imports the full release (`nessa.catalogue.esco`).

Run from `backend/` after `make setup` fetched the release:
`uv run --locked python -m tools.esco_sample`.
"""

import argparse
import csv
import hashlib
import io
import zipfile
from pathlib import Path

from nessa.catalogue.esco import ESCO_RELEASE
from nessa.catalogue.releases import read_verified
from tools.datasets import DATASETS_DIR
from tools.localenv import REPO_ROOT

SAMPLE_DIR = REPO_ROOT / "fixtures" / "esco-sample"
SAMPLE_FILE = "esco-v1.2.1-en-csv-sample.zip"
FIXED_TIME = (2025, 12, 16, 0, 0, 0)
ESSENTIAL_PER_OCCUPATION = 6
OPTIONAL_PER_OCCUPATION = 2
# Occupations the persona fixtures, the interview contract and the retrieval tests need:
# specialists sharing one ISCO-08 group (TAX1-01), two occupations sharing an alternative
# label ("bus operator": bus driver, trolley bus driver) and one with hidden labels
# (general practitioner).
SELECTED = (
    "bus driver",
    "trolley bus driver",
    "general practitioner",
    "data analyst",
    "data quality specialist",
    "statistical assistant",
    "ICT help desk agent",
    "ICT help desk manager",
    "nurse responsible for general care",
    "specialist nurse",
    "bookkeeper",
    "accounting assistant",
    "warehouse manager",
    "warehouse worker",
    "corporate trainer",
    "human resources officer",
    "plumber",
    "electrician",
    "bicycle mechanic",
    "landscape gardener",
    "garden labourer",
    "chemistry technician",
    "furniture restorer",
    "carpenter",
    "software developer",
    "ICT system analyst",
    "home care aide",
    "social care worker",
    "cook",
)


def _rows(archive: zipfile.ZipFile, name: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(archive.read(name).decode("utf-8"), newline=""))
    return list(reader.fieldnames or ()), list(reader)


def _csv(fields: list[str], rows: list[dict[str, str]]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def build(release: bytes) -> bytes:
    archive = zipfile.ZipFile(io.BytesIO(release))
    occ_fields, occupations = _rows(archive, "occupations_en.csv")
    by_label = {row["preferredLabel"]: row for row in occupations}
    missing = [label for label in SELECTED if label not in by_label]
    if missing:
        raise SystemExit(f"not in the release: {missing}")
    chosen = {by_label[label]["conceptUri"] for label in SELECTED}

    broader_fields, broader = _rows(archive, "broaderRelationsOccPillar_en.csv")
    parent = {r["conceptUri"]: r["broaderUri"] for r in broader if r["conceptType"] == "Occupation"}
    for uri in list(chosen):  # keep each chosen occupation's chain of broader occupations
        while (up := parent.get(uri)) and "/occupation/" in up:
            chosen.add(up)
            uri = up
    kept_occupations = [row for row in occupations if row["conceptUri"] in chosen]

    isco_fields, isco = _rows(archive, "ISCOGroups_en.csv")
    codes = {row["iscoGroup"][:n] for row in kept_occupations for n in range(1, 5)}
    kept_isco = [row for row in isco if row["code"] in codes]

    rel_fields, relations = _rows(archive, "occupationSkillRelations_en.csv")
    kept_relations = []
    for uri in sorted(chosen):
        mine = [r for r in relations if r["occupationUri"] == uri]
        kept_relations += [r for r in mine if r["relationType"] == "essential"][
            :ESSENTIAL_PER_OCCUPATION
        ]
        kept_relations += [r for r in mine if r["relationType"] == "optional"][
            :OPTIONAL_PER_OCCUPATION
        ]
    skill_uris = {r["skillUri"] for r in kept_relations}
    skill_fields, skills = _rows(archive, "skills_en.csv")
    kept_skills = [row for row in skills if row["conceptUri"] in skill_uris]
    ss_fields, skill_skill = _rows(archive, "skillSkillRelations_en.csv")
    kept_ss = [
        r
        for r in skill_skill
        if r["originalSkillUri"] in skill_uris and r["relatedSkillUri"] in skill_uris
    ]
    kept_broader = [
        r
        for r in broader
        if (r["conceptType"] == "Occupation" and r["conceptUri"] in chosen)
        or (r["conceptType"] == "ISCOGroup" and r["conceptUri"].rsplit("C", 1)[-1] in codes)
    ]
    files = {
        "ISCOGroups_en.csv": _csv(isco_fields, kept_isco),
        "broaderRelationsOccPillar_en.csv": _csv(broader_fields, kept_broader),
        "occupationSkillRelations_en.csv": _csv(rel_fields, kept_relations),
        "occupations_en.csv": _csv(occ_fields, kept_occupations),
        "skillSkillRelations_en.csv": _csv(ss_fields, kept_ss),
        "skills_en.csv": _csv(skill_fields, kept_skills),
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as sample:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            sample.writestr(info, files[name])
    return out.getvalue()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=SAMPLE_DIR / SAMPLE_FILE)
    args = parser.parse_args(argv)
    sample = build(read_verified(DATASETS_DIR / ESCO_RELEASE.file_name, ESCO_RELEASE))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(sample)
    print(f"{args.out}: {len(sample)} bytes, SHA-256 {hashlib.sha256(sample).hexdigest()}")


if __name__ == "__main__":
    main()
