"""Deterministic seed data: two invited demo identities and the M0 persona workspaces.

Identities match the Auth emulator seed (`docker/auth/seed`). The third emulator account,
`uninvited@careerwright.test`, is deliberately absent here: it can sign in but is not invited.
Each fixture workspace is built from its supplied persona file and labelled synthetic.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from careerwright.money import Money
from careerwright.planning.inputs import PlanningInputsDocument, PlanningInputsIn, stamped
from careerwright.profile.document import (
    FieldState,
    ProfileDocument,
    ProfileInput,
    apply_profile_input,
)
from careerwright.profile.document import empty_profile as empty_profile_document

SEED_NAMESPACE = uuid.UUID("6f1d3c2a-6b5e-4b8f-9a77-0d6c1e2f4a10")
FIXTURE_KEY = "p01"
FIXTURE_PERSONA = Path("personas/P01.json")


def seed_id(name: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, name)


@dataclass(frozen=True)
class SeedActor:
    actor_id: uuid.UUID
    email: str
    display_name: str


INVITED_ACTORS = (
    SeedActor(seed_id("actor:ada"), "ada@careerwright.test", "Ada Demo"),
    SeedActor(seed_id("actor:ben"), "ben@careerwright.test", "Ben Demo"),
)
FIXTURE_OWNER = INVITED_ACTORS[0]
FIXTURE_WORKSPACE_ID = seed_id("workspace:fixture:p01")
FIXTURE_SOURCE_ID = seed_id("source:fixture:p01")
FIXTURE_WORKSPACE_NAME = "P01 · Data quality while employed (synthetic demo)"


@dataclass(frozen=True)
class FixturePersona:
    key: str
    path: Path
    workspace_id: uuid.UUID
    source_id: uuid.UUID
    workspace_name: str


_SCENARIOS = (
    "Data quality while employed",
    "Explore practical careers",
    "IT support on a tight budget",
    "Nursing registration gate",
    "Bookkeeping returner",
)

FIXTURE_PERSONAS = tuple(
    FixturePersona(
        key=f"p{number:02d}",
        path=Path(f"personas/P{number:02d}.json"),
        workspace_id=seed_id(f"workspace:fixture:p{number:02d}"),
        source_id=seed_id(f"source:fixture:p{number:02d}"),
        workspace_name=f"P{number:02d} · {_SCENARIOS[number - 1]} (synthetic demo)",
    )
    for number in range(1, 6)
)


@dataclass(frozen=True)
class FixtureProfile:
    document: ProfileDocument
    planning_inputs: PlanningInputsDocument | None
    persona_sha256: str
    persona_locator: str
    observed_at: datetime


def _provided(value: object) -> dict[str, object]:
    return {"state": FieldState.PROVIDED, "value": value}


def fixture_profile(
    fixtures_dir: Path, persona_spec: FixturePersona = FIXTURE_PERSONAS[0]
) -> FixtureProfile:
    """Profile answers stated in a persona file; absent answers stay unasked."""
    raw = (fixtures_dir / persona_spec.path).read_bytes()
    persona = json.loads(raw)
    if (
        persona.get("synthetic") is not True
        or persona.get("currency") != "GBP"
        or persona.get("id", "").lower() != persona_spec.key
    ):
        raise ValueError("the fixture persona must be synthetic GBP data")
    unasked: dict[str, object] = {"state": FieldState.UNASKED}

    def stated(key: str) -> dict[str, object]:
        return _provided(persona[key]) if key in persona else unasked

    def money(key: str) -> dict[str, object]:
        return (
            _provided(Money(minor_units=persona[key], currency="GBP").model_dump())
            if key in persona
            else unasked
        )

    preferences = persona.get("personality_optional", {})

    def amount(key: str) -> Money | None:
        return Money(minor_units=persona[key], currency="GBP") if key in persona else None

    planning_facts: dict[str, object] = {}
    for source, destination in (
        ("opening_cash_minor", "opening_cash"),
        ("living_outgoings_minor", "living_costs"),
        ("reserve_minor", "reserve"),
    ):
        if (value := amount(source)) is not None:
            planning_facts[destination] = value
    if "weekly_total_availability_hours" in persona:
        planning_facts["weekly_availability"] = persona["weekly_total_availability_hours"]
    if (
        persona.get("income_baseline_status") != "unconfirmed"
        and (income := amount("current_net_income_minor")) is not None
    ):
        planning_facts["baseline"] = {"kind": "current_role", "net_income": income}
        planning_facts["objective_basis"] = "economic"

    new = ProfileInput.model_validate(
        {
            "preferred_name": unasked,
            "current_role": unasked,
            "cities": stated("cities"),
            "target_titles": stated("target_titles"),
            "weekly_study_hours": stated("weekly_study_hours"),
            "direct_spend_cap": money("direct_spend_cap_minor"),
            "monthly_payment_cap": money("monthly_payment_cap_minor"),
            "enjoyed_tasks": (
                _provided(preferences["enjoyed_tasks"])
                if "enjoyed_tasks" in preferences
                else unasked
            ),
            "confident_tasks": unasked,
            "evidenced_tasks": unasked,
            "work_style": (
                _provided(preferences["preferred_environment"])
                if "preferred_environment" in preferences
                else unasked
            ),
            "minimum_salary": unasked,
            "work_status": unasked,
            "qualifications": unasked,
            "disliked_tasks": unasked,
        }
    )
    return FixtureProfile(
        document=apply_profile_input(empty_profile_document(), new, persona_spec.source_id),
        planning_inputs=(
            stamped(
                PlanningInputsIn.model_validate(planning_facts),
                previous=None,
                by=FIXTURE_OWNER.actor_id,
                at=datetime.fromisoformat(persona["data_as_of"]).replace(tzinfo=UTC),
            )
            if planning_facts
            else None
        ),
        persona_sha256=hashlib.sha256(raw).hexdigest(),
        persona_locator=f"fixtures/m0/{persona_spec.path}",
        observed_at=datetime.fromisoformat(persona["data_as_of"]).replace(tzinfo=UTC),
    )
