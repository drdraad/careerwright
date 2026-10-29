"""Canonical jobs from source copies (spec section 7, "Search, canonicalisation and
matching"; JOB-01, JOB-02, PROP-02). Pure: deterministic rules, no model."""

import itertools
import uuid

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nessa.evidence.jobs import (
    CanonicalFacts,
    Grouped,
    advertiser_kind,
    canonical_facts,
    city_views,
    description_fingerprints,
    employer_key,
    group_copies,
    jobs_joined,
    same_job,
    title_key,
)
from nessa.evidence.records import AdvertiserKind, DescriptionKind, JobCopy, Location

FULL = (
    "We are looking for a data quality analyst to join our Manchester team. You will "
    "profile datasets, write validation rules and work with engineers to fix issues at "
    "source. Experience with SQL is essential and Python is desirable. Hybrid working."
)
SNIPPET = "We are looking for a data quality analyst to join our Manchester team. You will profile datasets, write validation…"  # noqa: E501
SNIPPET_KIND = DescriptionKind.SNIPPET
APPLY = "https://careers.northwind.example/apply/7781"


def copy(
    title: str = "Data Quality Analyst",
    employer: str | None = "Northwind Analytics Ltd",
    cities: tuple[str, ...] = ("Manchester",),
    *,
    source_job_id: str | None = None,
    apply_url: str | None = None,
    description: str | None = FULL,
    kind: DescriptionKind = DescriptionKind.FULL,
    employment_type: str | None = "FULL_TIME",
    advertiser: AdvertiserKind = AdvertiserKind.EMPLOYER,
) -> JobCopy:
    fingerprint, lead = description_fingerprints(description) if description else (None, None)
    return JobCopy(
        source_job_id=source_job_id,
        title=title,
        employer=employer,
        advertiser=advertiser,
        locations=[Location(label=city, locality=city) for city in cities],
        employment_type=employment_type,
        description_kind=kind if description else None,
        description_fingerprint=fingerprint if kind is DescriptionKind.FULL else None,
        description_lead=lead,
        apply_url=apply_url,
    )


def facts(job: JobCopy, provider: str = "careers.northwind.example") -> CanonicalFacts:
    return canonical_facts(job, provider=provider)


@pytest.mark.req("JOB-02")
def test_a_syndicated_snippet_of_the_same_advert_is_the_same_job() -> None:
    employer_page = facts(copy())
    board = facts(copy(description=SNIPPET, kind=DescriptionKind.SNIPPET), provider="adzuna")

    assert same_job(employer_page, board)


@pytest.mark.req("JOB-02")
def test_the_same_source_id_from_one_provider_is_one_job_even_if_its_text_changed() -> None:
    first = facts(copy(source_job_id="42"), provider="adzuna")
    edited = facts(copy(source_job_id="42", description="Rewritten advert."), provider="adzuna")

    assert same_job(first, edited)


@pytest.mark.req("JOB-02")
def test_the_same_application_url_is_one_job() -> None:
    url = "https://careers.northwind.example/apply/7781"
    a = facts(copy(apply_url=url, description=None))
    b = facts(copy(apply_url=url + "?utm_source=board", description=None), provider="board")

    assert same_job(a, b)


@pytest.mark.req("JOB-02")
@pytest.mark.parametrize(
    "other",
    [
        copy(title="Senior Data Quality Analyst"),  # a different level
        copy(employment_type="PART_TIME"),  # different hours on the same contract dimension
        copy(cities=("Leeds",)),  # a different location
        copy(employer="Southwind Analytics Ltd"),  # a different employer
    ],
    ids=["level", "contract", "location", "employer"],
)
def test_materially_different_levels_contracts_locations_or_employers_never_collapse(
    other: JobCopy,
) -> None:
    assert not same_job(facts(copy()), facts(other))


@pytest.mark.req("JOB-02")
def test_an_unknown_contract_or_location_cannot_prove_two_copies_different() -> None:
    known = facts(copy())
    vague = facts(copy(employment_type=None, cities=()), provider="board")

    assert same_job(known, vague)


@pytest.mark.req("JOB-02")
def test_a_board_listing_one_city_of_a_multi_city_job_is_the_same_job() -> None:
    multi = facts(copy(cities=("Manchester", "Leeds")))
    one_city = facts(copy(cities=("Leeds",), employment_type="FULL_TIME,PERMANENT"), "board")

    assert same_job(multi, one_city)  # shared city; the board adds terms the page omitted


@pytest.mark.req("JOB-02")
def test_two_copies_with_nothing_strong_in_common_stay_separate() -> None:
    a = facts(copy(description=None))
    b = facts(copy(description=None), provider="board")

    assert not same_job(a, b)  # same title and employer alone is not one vacancy


@pytest.mark.req("JOB-02")
def test_a_multi_city_job_counts_once_and_appears_under_each_city() -> None:
    multi = copy(cities=("Manchester", "Leeds"))
    grouped = group_copies([("careers.northwind.example", multi)])

    assert len(grouped) == 1
    views = city_views(grouped)
    assert set(views) == {"manchester", "leeds"}
    assert views["manchester"] == views["leeds"] == [grouped[0].job_key]


@pytest.mark.req("JOB-02")
def test_grouping_keeps_every_source_copy() -> None:
    grouped = group_copies(
        [
            ("careers.northwind.example", copy()),
            ("adzuna", copy(description=SNIPPET, kind=DescriptionKind.SNIPPET)),
            ("careers.northwind.example", copy(title="Senior Data Quality Analyst")),
        ]
    )

    assert sorted(len(g.copies) for g in grouped) == [1, 2]


@pytest.mark.req("JOB-01")
@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("Hays Recruitment", AdvertiserKind.AGENCY),
        ("Brook Street Staffing Ltd", AdvertiserKind.AGENCY),
        ("Acme Resourcing Solutions", AdvertiserKind.AGENCY),
        ("Northwind Analytics Ltd", AdvertiserKind.UNKNOWN),
    ],
)
def test_a_staffing_agency_is_told_apart_from_an_employer(name: str, kind: AdvertiserKind) -> None:
    assert advertiser_kind(name, on_own_site=False) is kind


@pytest.mark.req("JOB-01")
def test_an_employer_advertising_on_its_own_site_is_the_employer() -> None:
    assert advertiser_kind("Northwind Analytics Ltd", on_own_site=True) is AdvertiserKind.EMPLOYER
    assert advertiser_kind("Hays Recruitment", on_own_site=True) is AdvertiserKind.AGENCY
    assert advertiser_kind(None, on_own_site=False) is AdvertiserKind.UNKNOWN


@pytest.mark.req("JOB-01")
def test_an_agency_s_advert_never_makes_the_agency_the_employer() -> None:
    agency = copy(employer="Hays Recruitment", advertiser=AdvertiserKind.AGENCY)

    assert facts(agency).employer_key is None  # the hiring employer stays undisclosed


@pytest.mark.req("JOB-01")
def test_keys_fold_case_punctuation_and_legal_forms_but_keep_levels() -> None:
    assert employer_key("Northwind Analytics Ltd.") == employer_key("NORTHWIND ANALYTICS LIMITED")
    assert title_key("Data Quality Analyst (Hybrid)") == title_key("data-quality analyst")
    assert title_key("Senior Data Analyst") != title_key("Data Analyst")


@pytest.mark.req("PROP-02")
@given(st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=12), st.randoms())
def test_duplicate_source_copies_preserve_the_canonical_job_count(
    picks: list[int], rng: object
) -> None:
    distinct = [
        ("careers.northwind.example", copy(source_job_id=str(n), title=title, cities=cities))
        for n, (title, cities) in enumerate(
            [
                ("Data Quality Analyst", ("Manchester",)),
                ("Senior Data Quality Analyst", ("Manchester",)),
                ("Data Quality Analyst", ("Leeds",)),
                ("Data Engineer", ("Manchester", "Leeds")),
                ("Data Steward", ("Leeds",)),
            ]
        )
    ]
    base = len(group_copies(distinct))
    duplicated = distinct + [distinct[i] for i in picks]
    rng.shuffle(duplicated)  # type: ignore[attr-defined]

    assert len(group_copies(duplicated)) == base == 5


def stored_path(arrivals: list[tuple[str, JobCopy]]) -> list[int]:
    """The stored path's rule, as `_record_copies` applies it, one copy at a time: each
    copy joins the jobs `jobs_joined` names (oldest first), merging them, or starts one.
    Returns each copy's job at the end."""
    stored: list[tuple[int, CanonicalFacts]] = []
    for provider, job in arrivals:
        found = facts(job, provider)
        joined = jobs_joined(stored, found)
        keep = joined[0] if joined else max((j for j, _ in stored), default=-1) + 1
        stored = [(keep if j in joined else j, f) for j, f in stored] + [(keep, found)]
    return [j for j, _ in stored]


BOARD_LEEDS = ("jobs.board.example", copy(employer=None, cities=("Leeds",), apply_url=APPLY))
BOARD_SNIPPET = ("adzuna", copy(cities=("Manchester",), description=SNIPPET, kind=SNIPPET_KIND))
EMPLOYER_PAGE = ("careers.northwind.example", copy(cities=("Leeds", "Manchester"), apply_url=APPLY))


@pytest.mark.req("JOB-02", "PROP-02")
@pytest.mark.parametrize(
    "order", list(itertools.permutations([BOARD_LEEDS, BOARD_SNIPPET, EMPLOYER_PAGE]))
)
def test_the_stored_path_gives_one_job_for_three_copies_in_every_arrival_order(
    order: tuple[tuple[str, JobCopy], ...],
) -> None:
    # Review B I1: the two board copies share nothing (Leeds against Manchester); only the
    # employer's page joins them. Arriving last, it used to leave two jobs.
    assert not same_job(facts(BOARD_LEEDS[1], "x"), facts(BOARD_SNIPPET[1], "adzuna"))

    assert len(set(stored_path(list(order)))) == len(group_copies(list(order))) == 1


@pytest.mark.req("PROP-02")
@given(st.lists(st.integers(min_value=0, max_value=7), min_size=1, max_size=14), st.randoms())
def test_the_stored_path_counts_jobs_as_the_grouping_does_in_any_arrival_order(
    picks: list[int], rng: object
) -> None:
    pool = [
        BOARD_LEEDS,
        BOARD_SNIPPET,
        EMPLOYER_PAGE,
        ("careers.northwind.example", copy(title="Senior Data Quality Analyst")),
        ("careers.northwind.example", copy(cities=("York",), apply_url=f"{APPLY}?city=york")),
        ("jobs.board.example", copy(title="Data Engineer", employer=None, apply_url=APPLY)),
        ("jobs.board.example", copy(employer="Contoso Ltd", cities=("Leeds",))),
        ("adzuna", copy(source_job_id="9", cities=("Leeds",))),
    ]
    arrivals = [pool[i] for i in picks]
    rng.shuffle(arrivals)  # type: ignore[attr-defined]

    assert len(set(stored_path(arrivals))) == len(group_copies(arrivals))


def test_grouping_is_deterministic_and_keys_are_stable() -> None:
    a = group_copies([("x.example", copy()), ("adzuna", copy(description=SNIPPET))])
    b = group_copies([("x.example", copy()), ("adzuna", copy(description=SNIPPET))])

    assert [g.job_key for g in a] == [g.job_key for g in b]
    assert all(isinstance(g, Grouped) and uuid.UUID(g.job_key) for g in a)
