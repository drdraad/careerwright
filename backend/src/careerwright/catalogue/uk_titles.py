"""The UK job titles of the pinned ONS SOC 2020 coding index, as the role space reads them
(ADR 0015 decisions 1 and 2; spec section 4, DIV-1, and section 5, TAX-1).

The index is an authoritative occupational source: a title it lists is a UK job title, with
ONS's own SOC 2020 unit groups and ISCO-08 groups, every one kept and none picked. A title is
listed when it is exactly one of the index's normalised titles (`normalise_label`). The index
is read only once it is imported: without it, nothing can be said to be listed or not, so a
read is refused (`REFERENCE_DATA_UNAVAILABLE`), never answered as "not listed".
"""

from collections.abc import Iterable, Sequence

from careerwright.catalogue import reference_store
from careerwright.catalogue.esco import normalise_label
from careerwright.catalogue.records import UkTitle
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage

DATASET = "soc_index"  # its name among the reference datasets (`catalogue.reference.DATASETS`)


def held_index(tx: Tx) -> None:
    if reference_store.held(tx, DATASET) is None:
        raise CareerwrightError(
            ErrorCode.REFERENCE_DATA_UNAVAILABLE,
            "The UK job-title index has not been imported. Run `make setup`, then start "
            "Careerwright.",
            stage=ErrorStage.CATALOGUE,
        )


def listed(tx: Tx, titles: Iterable[str]) -> dict[str, UkTitle]:
    """Each of `titles` the index lists, by the title as given."""
    held_index(tx)
    wanted = {title: normalise_label(title) for title in titles}
    found = reference_store.uk_titles(tx, wanted.values())
    return {title: found[n] for title, n in wanted.items() if n in found}


def matching(tx: Tx, words: Sequence[str], typed: str, limit: int) -> tuple[list[UkTitle], int]:
    """The type-ahead's UK job titles (`reference_store.uk_title_matches`)."""
    held_index(tx)
    return reference_store.uk_title_matches(tx, words, normalise_label(typed), limit)
