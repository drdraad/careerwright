"""The pinned reference datasets' parsers (ADR 0010; TAX1-02, TAX1-04, TAX1-06, AIR1-11,
TAX1-07): each keeps its publisher's native codes and measures, keeps missingness as
missingness, and refuses a file that does not have its documented structure. Every figure
is synthetic (`tests/support/reference_data.py`); the real files are imported by the
full-release integration test."""

import io
import zipfile
from decimal import Decimal

import pytest

from nessa.catalogue import ai_evidence, ashe, soc, xlsx
from nessa.catalogue.ai_evidence import ExposureGradient, MatchType
from nessa.catalogue.ashe import AshePeriod, Reliability
from nessa.catalogue.releases import ReleaseIntegrityError
from tests.support import reference_data as samples


def _estimate(
    release: ashe.AsheRelease, code: str, region: str, period: AshePeriod
) -> ashe.AsheEstimate:
    return next(
        e
        for e in release.estimates
        if (e.soc_code, e.region_code, e.period) == (code, region, period)
    )


def test_a_workbook_s_cells_are_text_at_their_columns_and_a_dtd_is_refused() -> None:
    data = samples.workbook({"S": [["a", None, "3.5"], [], [None, "b"]]})

    assert list(xlsx.sheet_rows(data, "S")) == [["a", None, "3.5"], [], [None, "b"]]
    assert xlsx.sheet_names(data) == ["S"]
    with pytest.raises(ReleaseIntegrityError, match="no sheet"):
        list(xlsx.sheet_rows(data, "Missing"))

    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(buffer, "w") as target:
        for item in source.infolist():
            body = source.read(item)
            if item.filename == "xl/workbook.xml":
                body = b'<!DOCTYPE x [<!ENTITY a "aaaa">]>' + body
            target.writestr(item, body)
    with pytest.raises(ReleaseIntegrityError, match="document type"):
        list(xlsx.sheet_rows(buffer.getvalue(), "S"))


@pytest.mark.req("TAX1-04", "TAX1-06")
def test_ashe_keeps_codes_regions_periods_pence_and_onss_markers() -> None:
    data = samples.ashe_package()
    release = ashe.parse_release(data, samples.sample_pin(ashe.ASHE_RELEASE, data))

    assert len(release.estimates) == 3 * len(samples.ASHE_ROWS)
    annual = _estimate(release, "3544", samples.NORTH_WEST, AshePeriod.YEAR)
    assert (annual.soc_title, annual.region_name) == ("Data analysts", "North West")
    assert annual.figures["median"] == 3_806_310  # £38,063.10 as integer pence
    assert annual.figures["p90"] == 5_200_000
    assert annual.figures["p10"] is None  # withheld, never 0
    assert annual.markers["p10"] == "x"
    assert annual.median_cv == Decimal("9.6")
    assert annual.jobs_thousands == Decimal("8")
    # A binary-float artefact is read as decimal text and rounded to the penny.
    books = _estimate(release, "4122", samples.NORTH_WEST, AshePeriod.YEAR)
    assert books.figures["p90"] == 2_500_050
    weekly = _estimate(release, "3544", samples.LONDON, AshePeriod.WEEK)
    assert weekly.figures["median"] == 89_000
    assert weekly.region_code == "E12000007"
    hourly = _estimate(release, "3544", samples.NORTH_WEST, AshePeriod.HOUR)
    assert hourly.figures["median"] == 2_054
    unreliable = _estimate(release, "2135", samples.NORTH_WEST, AshePeriod.YEAR)
    assert unreliable.figures["median"] is None
    assert unreliable.markers["median"] == "x"
    assert unreliable.median_cv is None
    assert {e.region_code for e in release.estimates} <= set(ashe.WORK_REGIONS.values())


@pytest.mark.parametrize(
    ("cv", "band"),
    [
        (Decimal("4.8"), Reliability.PRECISE),
        (Decimal("9.6"), Reliability.REASONABLY_PRECISE),
        (Decimal("19.2"), Reliability.ACCEPTABLE),
        (Decimal("20.1"), Reliability.UNRELIABLE),
        (None, Reliability.UNKNOWN),
    ],
)
def test_ashe_reliability_follows_onss_cv_bands(cv: Decimal | None, band: Reliability) -> None:
    assert ashe.reliability(cv) is band


def test_an_ashe_package_without_one_of_its_tables_is_refused() -> None:
    buffer = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(samples.ashe_package())) as source,
        zipfile.ZipFile(buffer, "w") as target,
    ):
        for item in source.infolist():
            if "15.5b" not in item.filename:
                target.writestr(item, source.read(item))

    with pytest.raises(ReleaseIntegrityError, match=r"15\.5b"):
        ashe.parse_release(buffer.getvalue(), ashe.ASHE_RELEASE)


def test_an_ashe_row_naming_an_unknown_region_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        samples, "ASHE_ROWS", [("Atlantis", *samples.ASHE_ROWS[0][1:]), *samples.ASHE_ROWS]
    )

    with pytest.raises(ReleaseIntegrityError, match="Atlantis"):
        ashe.parse_release(samples.ashe_package(), ashe.ASHE_RELEASE)


@pytest.mark.req("TAX1-02")
def test_the_coding_index_keeps_every_title_level_link_and_counts_the_uncoded() -> None:
    data = samples.soc_index_workbook()
    index = soc.parse_index(data, samples.sample_pin(soc.SOC_INDEX_RELEASE, data))

    assert {g.code for g in index.unit_groups} == {code for code, _ in samples.UNIT_GROUPS}
    links = {(e.normalised, e.soc_code, e.isco_code) for e in index.entries}
    assert ("data analyst", "3544", "2511") in links
    assert ("systems analyst", "2135", "2511") in links  # one ISCO group, two SOC groups
    assert index.uncoded == 1  # ONS's "}}}}": no code, never guessed
    with pytest.raises(ReleaseIntegrityError, match="Version 14"):
        soc.parse_index(samples.soc_index_workbook("Version 13"), soc.SOC_INDEX_RELEASE)


@pytest.mark.req("AIR1-11")
def test_ilo_exposure_is_one_native_record_per_isco_group_with_its_own_measures() -> None:
    exposures = {e.isco_code: e for e in ai_evidence.parse_ilo(samples.ilo_workbook())}

    analysts = exposures["2511"]
    assert (analysts.tasks, analysts.mean_score, analysts.sd_score) == (
        2,
        Decimal("0.4900"),
        Decimal("0.1200"),
    )
    assert analysts.gradient is ExposureGradient.GRADIENT_2
    disagreeing = [*samples.ILO_ROWS, ("2511", "Systems Analysts", "0.5", "0.9", "0.1",
                                       "Exposed: Gradient 2")]  # fmt: skip
    with pytest.raises(ReleaseIntegrityError, match="disagree"):
        ai_evidence.parse_ilo(samples.ilo_workbook(disagreeing))


@pytest.mark.req("AIR1-11")
def test_observed_use_keeps_each_task_s_share_and_drops_the_release_s_no_task_row() -> None:
    usage = ai_evidence.parse_task_usage(samples.task_usage_csv())
    tasks = ai_evidence.parse_onet_tasks(samples.onet_tasks_csv())

    assert [(u.task_name, u.share_pct) for u in usage] == [
        ("synthetic task: build dashboards.", Decimal("0.25"))
    ]
    assert {t.onet_code for t in tasks} == {"15-2051.01", "43-3031.00"}


@pytest.mark.req("TAX1-07")
def test_the_crosswalk_states_its_versions_and_keeps_each_match_type() -> None:
    rows = ai_evidence.parse_crosswalk(samples.crosswalk_csv())

    by_pair = {(r.onet_code, r.esco_uri or r.isco_code): r.match_type for r in rows}
    assert by_pair[("15-2051.01", samples.DATA_ANALYST)] is MatchType.CLOSE
    assert by_pair[("15-2041.00", samples.DATA_ANALYST)] is MatchType.BROAD
    assert by_pair[("11-1011.00", "1120")] is MatchType.EXACT_ISCO  # a group, not an occupation
    with pytest.raises(ReleaseIntegrityError, match="Classification 2 Version"):
        ai_evidence.parse_crosswalk(samples.crosswalk_csv(esco_version="v1.2.1"))
