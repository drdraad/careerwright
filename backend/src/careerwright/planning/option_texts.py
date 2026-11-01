"""The text of a course or funding page the person pastes for an option they add (S5.7, Task
12b), kept as their own input exactly as Task 7 keeps a pasted posting: its own route
(`pasted_text`), never fetched, third parties' contact details removed before anything is
hashed or sealed, the body sealed in the workspace, and a source address only as a checked
link. Spans of an option are chosen in this kept text (`planning.own_options`).

A pasted text is not a job example: it joins no job, no target's examples and no coverage
count.
"""

import hashlib
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import store as evidence_store
from careerwright.evidence.acquisition import (
    MAX_PASTED_CHARS,
    PASTED_RIGHTS,
    document_context,
    reference_url,
)
from careerwright.evidence.redaction import redact_text
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.workspaces import visible_workspace
from careerwright.planning.own_options import PastedText


class PasteOptionText(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: Annotated[str, StringConstraints(min_length=1, max_length=MAX_PASTED_CHARS)]
    source_url: Annotated[str, StringConstraints(min_length=1, max_length=2_048)] | None = Field(
        default=None, description="Where the person copied it from, as a reference only."
    )


@dataclass(frozen=True)
class OptionText:
    text_id: uuid.UUID
    text: str  # as kept: third parties' contact details removed
    sha256: str
    source_url: str | None


def paste_option_text(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: PasteOptionText, *, keyring: Keyring
) -> uuid.UUID:
    """Keep the pasted text; its ID. Nothing is fetched."""
    visible_workspace(tx, workspace_id, lock=True)
    source_url = reference_url(command.source_url) if command.source_url else None
    body = redact_text(command.text).encode()
    if not body.strip():
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Paste the page's words, or type the option's details instead.",
            stage=ErrorStage.REQUEST,
            details={"field": "text", "reason": "no_words"},
        )
    sha256 = hashlib.sha256(body).hexdigest()
    text_id = uuid.uuid4()
    evidence_store.insert_pasted_attempt(
        tx,
        attempt_id=text_id,
        workspace_id=workspace_id,
        created_by=actor.actor_id,
        requested_url=source_url,
        sha256=sha256,
        byte_count=len(body),
        rights_status=PASTED_RIGHTS,
    )
    evidence_store.insert_document(
        tx,
        attempt_id=text_id,
        workspace_id=workspace_id,
        sha256=sha256,
        sealed=keyring.seal(body, document_context(workspace_id, text_id)),
    )
    return text_id


def option_text(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, text_id: uuid.UUID
) -> OptionText | None:
    """A text pasted in this workspace, as kept; None for any other."""
    found = evidence_store.workspace_pasted_document(tx, workspace_id, text_id)
    if found is None:
        return None
    sha256, source_url, sealed = found
    text = keyring.open(sealed, document_context(workspace_id, text_id)).decode()
    return OptionText(text_id, text, sha256, source_url)


def pasted_texts(
    tx: Tx, keyring: Keyring, workspace_id: uuid.UUID, text_ids: Iterable[uuid.UUID]
) -> dict[uuid.UUID, PastedText]:
    """Each named text pasted in this workspace, as an own option reads it; one not found is
    left out (an option citing it is refused when written)."""
    found = {}
    for text_id in sorted(set(text_ids)):
        text = option_text(tx, keyring, workspace_id, text_id)
        if text is not None:
            found[text_id] = PastedText(text.text, text.sha256)
    return found
