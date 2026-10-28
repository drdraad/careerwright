"""The deterministic demo explainer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture keeps the live adapter's contract, labelled synthetic).

It reads the same prompt a live model reads and answers the same schema: for each occupation,
one claim, labelled synthetic, quoting the first of the person's answers that shares a word
with ESCO's record of that occupation, and the essential skill or title holding the word (or
the word itself, from the description); with no shared word, the first answer and the title.
Its output passes the same check and is stored with origin `fixture`. It exercises the
product offline; it does not evaluate explanations.
"""

import re

from nessa.profile.slate_explanation import (
    CONTEXT_MARKER,
    QUOTE_CHARS,
    ExplanationOutput,
    ModelClaim,
    ModelExplanation,
    ModelQuote,
    PromptExplanationContext,
    PromptOccupation,
    QuoteSource,
)

CLAIM = "Demo explainer (synthetic): Nessa links one of your answers to ESCO's record of this work."
_WORD = re.compile(r"\b[^\W\d_]{4,}\b")  # whole words of four letters or more
_COMMON = frozenset(
    {"also", "from", "have", "into", "such", "that", "their", "them", "they", "this", "with"}
    | {"work", "works", "working", "other", "these", "those", "which", "will", "using"}
)


def prompt_context(prompt: str) -> PromptExplanationContext:
    if not prompt.startswith(CONTEXT_MARKER):
        raise ValueError("the prompt has no explanation context")
    return PromptExplanationContext.model_validate_json(prompt[len(CONTEXT_MARKER) :])


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.casefold())) - _COMMON


def _quotable(text: str) -> bool:
    return QUOTE_CHARS[0] <= len(text) <= QUOTE_CHARS[1] and any(c.isalpha() for c in text)


def _link(answers: list[str], occupation: PromptOccupation) -> tuple[str, str]:
    """An answer and the part of the record it shares a word with."""
    for answer in answers:
        shared = _words(answer)
        for part in (*occupation.essential_skills, occupation.title):
            if shared & _words(part) and _quotable(part):
                return answer, part
        common = sorted(shared & _words(occupation.description))
        if common:
            return answer, common[0]
    return answers[0], occupation.title


def fixture_explanation(context: PromptExplanationContext) -> ExplanationOutput:
    answers = [text for texts in context.answers.values() for text in texts if _quotable(text)]
    explanations: list[ModelExplanation] = []
    for occupation in context.occupations:
        answer, part = _link(answers, occupation) if answers else ("", occupation.title)
        quotes = [
            ModelQuote(source=QuoteSource.ANSWER, text=answer),
            ModelQuote(source=QuoteSource.ESCO, text=part),
        ]
        explanations.append(
            ModelExplanation(
                occupation=occupation.ref, claims=[ModelClaim(text=CLAIM, quotes=quotes)]
            )
        )
    return ExplanationOutput(explanations=explanations)
