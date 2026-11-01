"""The finite list of English cities a work area can name (spec section 3; L0 is England).

Source: GOV.UK, "List of cities", England section (Cabinet Office; Open Government Licence
v3.0), https://www.gov.uk/government/publications/list-of-cities/list-of-cities-html,
retrieved 2026-10-28 (page SHA-256 7da9d661...7afe), 55 cities, including the Platinum
Jubilee awards. Each city keeps the list's own name. The region is its ONS region (E12
code); the assignment was made by the implementing agent and is recorded for review in
`docs/adr/0006-taxonomy-and-interview-contract.md`.

A city is geography only: resolving one says where work could be, never where a person
lives or whether they may work there (BND1-04). Unknown names are refused, never guessed,
and no alias maps a name to two cities.
"""

import re
from dataclasses import dataclass

COUNTRY_CODE = "GB"
SUBDIVISION_CODE = "GB-ENG"  # ISO 3166-2
TIMEZONE = "Europe/London"
LIST_SOURCE_URL = "https://www.gov.uk/government/publications/list-of-cities/list-of-cities-html"
LIST_RETRIEVED = "2026-10-28"
LIST_SHA256 = "7da9d66117dc3cc23dbb8e1614d1229adab5cac7b045140d96fb3cb3b7d05afe"
LIST_LICENCE = "Open Government Licence v3.0"

_REGIONS = {
    "E12000001": "North East",
    "E12000002": "North West",
    "E12000003": "Yorkshire and The Humber",
    "E12000004": "East Midlands",
    "E12000005": "West Midlands",
    "E12000006": "East of England",
    "E12000007": "London",
    "E12000008": "South East",
    "E12000009": "South West",
}


@dataclass(frozen=True)
class Place:
    place_id: str
    label: str
    region_code: str
    aliases: tuple[str, ...] = ()
    country_code: str = COUNTRY_CODE
    subdivision_code: str = SUBDIVISION_CODE
    timezone: str = TIMEZONE

    @property
    def region(self) -> str:
        return region_name(self.region_code)


def region_name(region_code: str) -> str:
    """An English ONS region's name (E12 code)."""
    return _REGIONS[region_code]


def _place(label: str, region: str, *aliases: str) -> Place:
    slug = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
    return Place(f"gb-eng-{slug}", label, region, aliases)


NE, NW, YH, EM, WM, EE, LDN, SE, SW = sorted(_REGIONS)
ENGLISH_CITIES: tuple[Place, ...] = (
    _place("Bath", SW),
    _place("Birmingham", WM),
    _place("Bradford", YH),
    _place("Brighton & Hove", SE, "Brighton and Hove", "Brighton", "Hove"),
    _place("Bristol", SW),
    _place("Cambridge", EE),
    _place("Canterbury", SE),
    _place("Carlisle", NW),
    _place("Chelmsford", EE),
    _place("Chester", NW),
    _place("Chichester", SE),
    _place("Colchester", EE),
    _place("Coventry", WM),
    _place("Derby", EM),
    _place("Doncaster", YH),
    _place("Durham", NE),
    _place("Ely", EE),
    _place("Exeter", SW),
    _place("Gloucester", SW),
    _place("Hereford", WM),
    _place("Kingston-upon-Hull", YH, "Kingston upon Hull", "Hull"),
    _place("Lancaster", NW),
    _place("Leeds", YH),
    _place("Leicester", EM),
    _place("Lichfield", WM),
    _place("Lincoln", EM),
    _place("Liverpool", NW),
    _place("London", LDN, "City of London"),
    _place("Manchester", NW),
    _place("Milton Keynes", SE),
    # Not plain "Newcastle": it also names Newcastle-under-Lyme, which is not a listed city.
    _place("Newcastle-upon-Tyne", NE, "Newcastle upon Tyne"),
    _place("Norwich", EE),
    _place("Nottingham", EM),
    _place("Oxford", SE),
    _place("Peterborough", EE),
    _place("Plymouth", SW),
    _place("Portsmouth", SE),
    _place("Preston", NW),
    _place("Ripon", YH),
    _place("Salford", NW),
    _place("Salisbury", SW),
    _place("Sheffield", YH),
    _place("Southampton", SE),
    _place("Southend-on-Sea", EE, "Southend on Sea", "Southend"),
    _place("St Albans", EE, "St. Albans", "Saint Albans"),
    _place("Stoke on Trent", WM, "Stoke-on-Trent"),
    _place("Sunderland", NE),
    _place("Truro", SW),
    _place("Wakefield", YH),
    _place("Wells", SW),
    _place("Westminster", LDN, "City of Westminster"),
    _place("Winchester", SE),
    _place("Wolverhampton", WM),
    _place("Worcester", WM),
    _place("York", YH),
)


def _key(name: str) -> str:
    return " ".join(name.casefold().replace("-", " ").split())


def _index(places: tuple[Place, ...]) -> dict[str, Place]:
    index: dict[str, Place] = {}
    for place in places:
        for name in (place.label, *place.aliases):
            key = _key(name)
            if key in index and index[key] != place:
                raise ValueError(f"{name!r} would name two cities")
            index[key] = place
    return index


_BY_NAME = _index(ENGLISH_CITIES)


def resolve_city(name: str) -> Place | None:
    """The listed English city this name (or a recorded alias) means, or None."""
    return _BY_NAME.get(_key(name))
