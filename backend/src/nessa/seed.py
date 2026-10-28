"""Deterministic seed data: two invited demo identities and the named fixture workspace.

Identities match the Auth emulator seed (`docker/auth/seed`). The third emulator account,
`uninvited@nessa.test`, is deliberately absent here: it can sign in but is not invited.
The fixture workspace is built from the supplied P01 persona file, never from values typed
into code, and is labelled synthetic for good (Global Constraint 5).
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nessa.money import Money
from nessa.profile.document import FieldState, ProfileDocument, ProfileInput, apply_profile_input
from nessa.profile.document import empty_profile as empty_profile_document

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
    SeedActor(seed_id("actor:ada"), "ada@nessa.test", "Ada Demo"),
    SeedActor(seed_id("actor:ben"), "ben@nessa.test", "Ben Demo"),
)
FIXTURE_OWNER = INVITED_ACTORS[0]
FIXTURE_WORKSPACE_ID = seed_id("workspace:fixture:p01")
FIXTURE_SOURCE_ID = seed_id("source:fixture:p01")
FIXTURE_WORKSPACE_NAME = "P01 demo (synthetic)"


@dataclass(frozen=True)
class FixtureProfile:
    document: ProfileDocument
    persona_sha256: str
    persona_locator: str
    observed_at: datetime


def _provided(value: object) -> dict[str, object]:
    return {"state": FieldState.PROVIDED, "value": value}


def fixture_profile(fixtures_dir: Path) -> FixtureProfile:
    """The P01 practical inputs that the Sprint 1 profile holds; everything else stays unasked."""
    raw = (fixtures_dir / FIXTURE_PERSONA).read_bytes()
    persona = json.loads(raw)
    if persona.get("synthetic") is not True or persona.get("currency") != "GBP":
        raise ValueError("the fixture persona must be synthetic GBP data")
    unasked = {"state": FieldState.UNASKED}

    def money(key: str) -> dict[str, object]:
        return _provided(Money(minor_units=persona[key], currency="GBP").model_dump())

    new = ProfileInput.model_validate(
        {
            "preferred_name": unasked,
            "current_role": unasked,
            "cities": _provided(persona["cities"]),
            "target_titles": _provided(persona["target_titles"]),
            "weekly_study_hours": unasked,
            "direct_spend_cap": money("direct_spend_cap_minor"),
            "monthly_payment_cap": money("monthly_payment_cap_minor"),
            "enjoyed_tasks": unasked,
            "confident_tasks": unasked,
            "evidenced_tasks": unasked,
        }
    )
    return FixtureProfile(
        document=apply_profile_input(empty_profile_document(), new, FIXTURE_SOURCE_ID),
        persona_sha256=hashlib.sha256(raw).hexdigest(),
        persona_locator=f"fixtures/m0/{FIXTURE_PERSONA}",
        observed_at=datetime.fromisoformat(persona["data_as_of"]).replace(tzinfo=UTC),
    )
