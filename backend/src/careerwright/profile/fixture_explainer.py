"""The deterministic demo explainer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture keeps the live adapter's contract, labelled synthetic).

It reads the same prompt a live model reads and answers the same schema: for each occupation,
one claim, labelled synthetic, quoting the first of the person's answers that shares a word
with ESCO's record of that occupation, and the essential skill or title holding the word (or
from the description, the word where it is a whole word there, else the whole token holding
it: "children's", not "children"); with no shared word, the first answer and the title.
Every quotation it writes is first read back as the check reads it (`accepted_quotation`),
so its output passes the same check; it is stored with origin `fixture`. It exercises the
product offline; it does not evaluate explanations.
"""

from careerwright.profile.slate_explanation import (
    CONTEXT_MARKER,
    ExplanationOutput,
    ModelClaim,
    ModelExplanation,
    ModelQuote,
    PromptExplanationContext,
    PromptOccupation,
    QuoteSource,
    accepted_quotation,
    content_words,
)

_AROUND_WORDS = '()[]{},.;:!?"“”«»'  # punctuation a word of the description may carry

CLAIM = (
    "Demo explainer (synthetic): Careerwright links one of your answers to ESCO's record of "
    "this work."
)


def prompt_context(prompt: str) -> PromptExplanationContext:
    if not prompt.startswith(CONTEXT_MARKER):
        raise ValueError("the prompt has no explanation context")
    return PromptExplanationContext.model_validate_json(prompt[len(CONTEXT_MARKER) :])


def _quote_from(source: str, words: set[str]) -> str | None:
    """A quotation of the source holding one of the words that the check accepts: the word
    where it is a whole word there, else the whole token holding it (a possessive kept)."""
    tokens = [token.strip(_AROUND_WORDS) for token in source.split()]
    for word in sorted(words):
        for candidate in (word, *(t for t in tokens if word in content_words(t))):
            if accepted_quotation(candidate, source):
                return candidate
    return None


def _link(answers: list[str], occupation: PromptOccupation) -> tuple[str, str]:
    """An answer and the part of the record it shares a content word with; else the first
    answer and the title, or a word of the description if the title has none."""
    description = occupation.description
    for answer in answers:
        shared = content_words(answer)
        for part in (*occupation.essential_skills, occupation.title):
            if shared & content_words(part) and accepted_quotation(part, part):
                return answer, part
        quoted = _quote_from(description, shared & content_words(description))
        if quoted is not None:
            return answer, quoted
    if accepted_quotation(occupation.title, occupation.title):
        return answers[0], occupation.title
    return answers[0], _quote_from(description, content_words(description)) or occupation.title


def fixture_explanation(context: PromptExplanationContext) -> ExplanationOutput:
    answers = [
        text
        for texts in context.answers.values()
        for text in texts
        if accepted_quotation(text, text)
    ]
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
