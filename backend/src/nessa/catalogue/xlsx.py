"""Rows of one worksheet of an Office Open XML workbook (`.xlsx`), standard library only.

The pinned ONS and ILO tables are workbooks. Their bytes are verified against the pin
before this reads them (`releases.read_verified`), and it refuses what a workbook of
published tables never needs: a document type declaration (entity expansion) or a member
larger than `MAX_MEMBER_BYTES` once inflated. Every cell value is returned as text, exactly
as stored (a number as its decimal text), or None for an empty cell; nothing is converted
here, so no float ever reaches a money value.
"""

import io
import re
import zipfile
from collections.abc import Iterator
from xml.etree import ElementTree

from nessa.catalogue.releases import ReleaseIntegrityError

MAX_MEMBER_BYTES = 64 * 1024 * 1024
_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
_PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
_CELL_REF = re.compile(r"^([A-Z]{1,3})[0-9]+$")
_PROLOG_BYTES = 2048

Row = list[str | None]


def _xml(archive: zipfile.ZipFile, name: str) -> ElementTree.Element:
    """A member parsed, after its size bound and the refusal of a document type declaration:
    without one there is no entity to expand and no external entity to fetch, and the
    bytes were verified against the pin before this reads them."""
    try:
        info = archive.getinfo(name)
    except KeyError:
        raise ReleaseIntegrityError(f"the workbook has no {name}") from None
    if info.file_size > MAX_MEMBER_BYTES:
        raise ReleaseIntegrityError(f"{name} inflates past {MAX_MEMBER_BYTES} bytes")
    data = archive.read(name)
    if b"<!DOCTYPE" in data[:_PROLOG_BYTES]:
        raise ReleaseIntegrityError(f"{name} declares a document type")
    try:
        return ElementTree.fromstring(data)  # noqa: S314 - pinned, verified, no DTD (above)
    except ElementTree.ParseError:
        raise ReleaseIntegrityError(f"{name} is not well-formed XML") from None


def _column(reference: str) -> int:
    match = _CELL_REF.match(reference)
    if match is None:
        raise ReleaseIntegrityError(f"unexpected cell reference {reference[:12]!r}")
    index = 0
    for letter in match.group(1):
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def _text(element: ElementTree.Element) -> str:
    return "".join(t.text or "" for t in element.iter(f"{_MAIN}t"))


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = _xml(archive, "xl/sharedStrings.xml")
    return [_text(item) for item in root.iter(f"{_MAIN}si")]


def sheet_names(data: bytes) -> list[str]:
    with _open(data) as archive:
        return list(_sheet_targets(archive))


def _open(data: bytes) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ReleaseIntegrityError("the workbook is not a zip archive") from None


def _sheet_targets(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = _xml(archive, "xl/workbook.xml")
    relations = _xml(archive, "xl/_rels/workbook.xml.rels")
    targets = {r.get("Id"): r.get("Target", "") for r in relations.iter(_PACKAGE_REL)}
    sheets: dict[str, str] = {}
    for sheet in workbook.iter(f"{_MAIN}sheet"):
        target = targets.get(sheet.get(_REL_ID))
        if not target:
            raise ReleaseIntegrityError(f"sheet {sheet.get('name')!r} has no part")
        sheets[sheet.get("name", "")] = (
            target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        )
    return sheets


def _value(cell: ElementTree.Element, shared: list[str]) -> str | None:
    kind = cell.get("t", "n")
    if kind == "inlineStr":
        found = cell.find(f"{_MAIN}is")
        return None if found is None else _text(found)
    value = cell.find(f"{_MAIN}v")
    if value is None or value.text is None:
        return None
    if kind == "s":
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            raise ReleaseIntegrityError("a cell names a missing shared string") from None
    return value.text


def sheet_rows(data: bytes, sheet: str) -> Iterator[Row]:
    """Every row of `sheet`, in order, each cell at its column (None where a row skips one).
    Rows the sheet leaves out entirely are not invented."""
    with _open(data) as archive:
        targets = _sheet_targets(archive)
        if sheet not in targets:
            raise ReleaseIntegrityError(f"the workbook has no sheet {sheet!r}")
        shared = _shared_strings(archive)
        root = _xml(archive, targets[sheet])
    for row in root.iter(f"{_MAIN}row"):
        cells: dict[int, str | None] = {}
        for cell in row.iter(f"{_MAIN}c"):
            cells[_column(cell.get("r", ""))] = _value(cell, shared)
        yield [cells.get(i) for i in range(max(cells) + 1)] if cells else []
