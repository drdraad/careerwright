"""What discovery's searches and matches did, as facts (Task 6d slice A; ruling R11; the
audit's code appendix, findings F3 and F7).

The backend composes no sentence the person reads. Each fact carries what the search or
match did (`Outcome`), a reason code (`reason`, the field the API's unions are told apart by)
and the values its words need; the web words it from `src/lib/vocabulary.ts` with exhaustive
maps, so a new code fails its type check. What each fact reports is what the sentence it
replaces reported (R11 freezes the notes and their matching rules); only where the words
live changed. A title needs no article or plural rule: the web's templates need none.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.profile.discovery import EvidenceItem
from careerwright.profile.interview import ProfileField


class Outcome(StrEnum):
    """What a search or a match did."""

    FOUND_WORK = "found_work"
    FOUND_NONE = "found_none"
    NOT_SEARCHED = "not_searched"
    MATCHED = "matched"
    MATCHED_SEVERAL = "matched_several"
    NOT_MATCHED = "not_matched"


class Fact(BaseModel):
    # A reason and an outcome are fixed per kind, so they have defaults; they are always
    # served, so the published schema requires them.
    model_config = ConfigDict(
        extra="forbid", frozen=True, json_schema_serialization_defaults_required=True
    )


# How the slate was made (`SlateOut.notes`) -------------------------------------------------


class ReleaseChanged(Fact):
    """The searches were chosen when another ESCO release was held."""

    reason: Literal["release_changed"] = "release_changed"
    searched: str = Field(description="The release the searches were chosen for.")
    held: str = Field(description="The release this slate uses.")


class OneWordWorkStyle(Fact):
    """Searches and title ideas resting only on one-word answers about how the person likes to
    work were not run: one word matches too loosely."""

    reason: Literal["one_word_work_style"] = "one_word_work_style"
    outcome: Literal[Outcome.NOT_SEARCHED] = Outcome.NOT_SEARCHED
    answers: list[str]


class SearchDid(StrEnum):
    """What one of an answer's searches did that found no work."""

    # It read the main names of essential skills, and none holds all its words.
    READ_MAIN_NAMES = "read_main_names"
    ONLY_COMMON_WORDS = "only_common_words"  # nothing was read
    # It is one of the person's own titles, joined by shared skills: no other occupation
    # shares enough essential skills with it.
    NO_SHARED_OCCUPATION = "no_shared_occupation"


class AnswerSearch(Fact):
    text: str
    did: SearchDid


class AnswerFoundNoWork(Fact):
    """Every search resting on an answer found nothing."""

    reason: Literal["answer_found_no_work"] = "answer_found_no_work"
    outcome: Literal[Outcome.FOUND_NONE] = Outcome.FOUND_NONE
    answer: str
    own_words: bool = Field(description="Its searches are the answer itself.")
    searches: list[AnswerSearch]
    min_shared: int = Field(description="The essential skills a join needs in common.")


class TooGeneralBy(StrEnum):
    OCCUPATIONS = "occupations"  # it reached too many occupations
    SKILLS = "skills"  # it reached too many different skills, none named by just its words


class TooGeneral(Fact):
    """A search too general to find work on its own: it only adds weight to work another
    search found."""

    reason: Literal["too_general"] = "too_general"
    outcome: Literal[Outcome.FOUND_NONE] = Outcome.FOUND_NONE
    search: str
    answers: list[str] = Field(description="The answers it rests on.")
    own_words: bool = Field(description="The search is its one answer itself.")
    by: TooGeneralBy
    occupations: int = Field(description="Occupations it reached through essential skills.")
    skills: int = Field(description="Different essential skills it reached.")
    narrower_for: list[str] = Field(
        description="Its answers no other search found work from: a narrower search is needed "
        "for them (a model's search only)."
    )


class JoinKeptBest(Fact):
    """A title's skill join reached more than it keeps."""

    reason: Literal["join_kept_best"] = "join_kept_best"
    outcome: Literal[Outcome.FOUND_WORK] = Outcome.FOUND_WORK
    title: str
    found: int = Field(description="Other occupations sharing enough essential skills.")
    kept: int = Field(description="Those kept: the largest share of essential skills in common.")
    min_shared: int


class SmallPool(Fact):
    """A full slate chosen from fewer occupations than Careerwright aims for."""

    reason: Literal["small_pool"] = "small_pool"
    outcome: Literal[Outcome.FOUND_WORK] = Outcome.FOUND_WORK
    pool_size: int
    pool_target: int


class CastingWider(Fact):
    """The broader view: a lower bar for relevance and one suggestion per kind of work."""

    reason: Literal["casting_wider"] = "casting_wider"


class MoreDepth(Fact):
    """The deeper view: more from one kind of work, because the person asked."""

    reason: Literal["more_depth"] = "more_depth"
    family_limit: int


SlateNote = Annotated[
    ReleaseChanged
    | OneWordWorkStyle
    | AnswerFoundNoWork
    | TooGeneral
    | JoinKeptBest
    | SmallPool
    | CastingWider
    | MoreDepth,
    Field(discriminator="reason"),
]


# Why there are fewer than six (`fewer_reasons`) ---------------------------------------------


class NothingFound(Fact):
    reason: Literal["nothing_found"] = "nothing_found"
    outcome: Literal[Outcome.FOUND_NONE] = Outcome.FOUND_NONE


class FewMatched(Fact):
    """Only these matched closely enough to suggest; weaker matches don't fill the rest."""

    reason: Literal["few_matched"] = "few_matched"
    count: int


class KindsOfWorkShown(Fact):
    """These are in kinds of work already shown as often as the view allows."""

    reason: Literal["kinds_of_work_shown"] = "kinds_of_work_shown"
    count: int
    family_limit: int


class ExclusionsRemoved(Fact):
    reason: Literal["exclusions_removed"] = "exclusions_removed"
    count: int


class TitleNotMatched(Fact):
    """A title of the person's own matched no occupation in ESCO, so nothing is joined to it."""

    reason: Literal["title_not_matched"] = "title_not_matched"
    outcome: Literal[Outcome.NOT_MATCHED] = Outcome.NOT_MATCHED
    title: str


class TitleKeptAsOwn(Fact):
    """A title of the person's own that they said none of the closest ESCO occupations is
    ("None of these is my job"): it is kept in their words, names no occupation, and nothing
    is joined to it; nothing asks them to pick another."""

    reason: Literal["title_kept_as_own"] = "title_kept_as_own"
    outcome: Literal[Outcome.NOT_MATCHED] = Outcome.NOT_MATCHED
    title: str


class TitleMatchedSeveral(Fact):
    """A title of the person's own matched several occupations: nothing is joined to it until
    they choose which they mean."""

    reason: Literal["title_matched_several"] = "title_matched_several"
    outcome: Literal[Outcome.MATCHED_SEVERAL] = Outcome.MATCHED_SEVERAL
    title: str
    occupations: int


class NoSharedOccupation(Fact):
    """The role's join found no other occupation sharing enough essential skills."""

    reason: Literal["no_shared_occupation"] = "no_shared_occupation"
    outcome: Literal[Outcome.FOUND_NONE] = Outcome.FOUND_NONE
    title: str = Field(description="The role, as ESCO titles it.")
    min_shared: int


FewerReason = Annotated[
    NothingFound
    | FewMatched
    | KindsOfWorkShown
    | ExclusionsRemoved
    | TitleNotMatched
    | TitleKeptAsOwn
    | TitleMatchedSeveral
    | NoSharedOccupation,
    Field(discriminator="reason"),
]


# Why a suggestion could suit you (`SuggestionOut.reasons`) ---------------------------------


class JoinedBySharedSkills(Fact):
    reason: Literal["joined_by_shared_skills"] = "joined_by_shared_skills"
    outcome: Literal[Outcome.FOUND_WORK] = Outcome.FOUND_WORK
    field: ProfileField
    answer: str
    shared: int = Field(description="Essential skills ESCO lists for both.")


class SearchedThroughSkill(Fact):
    reason: Literal["searched_through_skill"] = "searched_through_skill"
    outcome: Literal[Outcome.FOUND_WORK] = Outcome.FOUND_WORK
    field: ProfileField
    answer: str
    search: str
    skill: str = Field(description="The essential skill whose main name holds its words.")


class TitleIdeaMatched(Fact):
    """A title Careerwright thought of from the answer, matched to this occupation."""

    reason: Literal["title_idea_matched"] = "title_idea_matched"
    outcome: Literal[Outcome.MATCHED] = Outcome.MATCHED
    field: ProfileField
    answer: str
    title: str


class OwnTitleMatched(Fact):
    """The person's own title, matched to this occupation."""

    reason: Literal["own_title_matched"] = "own_title_matched"
    outcome: Literal[Outcome.MATCHED] = Outcome.MATCHED
    field: ProfileField
    answer: str


SuggestionReason = Annotated[
    JoinedBySharedSkills | SearchedThroughSkill | TitleIdeaMatched | OwnTitleMatched,
    Field(discriminator="reason"),
]


class TitleIdeaReason(StrEnum):
    """What Careerwright did with a title it thought of (ADR 0015 decision 2)."""

    # ESCO holds it as a label: its occupation (or each of several) joins the slate's pool.
    IN_ESCO = "in_esco"
    # ESCO doesn't, and the UK job-title index lists it exactly: a suggestion in its own short
    # list beside the slate, never in the slate's pool.
    IN_UK_TITLE_INDEX = "in_uk_title_index"
    NOT_YET_FOUND = "not_yet_found"  # neither: shown as not yet found, never a suggestion
    # It rests only on one-word answers about how the person likes to work: not looked up.
    NOT_SEARCHED = "not_searched"


class TitleIdea(Fact):
    """A title Careerwright thought of, and what it did with it: only an idea ESCO holds or the
    UK job-title index lists is a suggestion."""

    title: str
    based_on: list[EvidenceItem]
    reason: TitleIdeaReason
    outcome: Literal[
        Outcome.MATCHED, Outcome.MATCHED_SEVERAL, Outcome.NOT_MATCHED, Outcome.NOT_SEARCHED
    ] = Field(description="What matching it in ESCO did.")
    occupations: int | None = Field(
        description="Occupations matching it in ESCO; null when it wasn't searched."
    )
