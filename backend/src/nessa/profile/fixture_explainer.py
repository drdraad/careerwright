"""The deterministic demo explainer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture keeps the live adapter's contract, labelled synthetic).

It reads the same prompt a live model reads and answers the same schema: for each occupation,
one claim, labelled synthetic, quoting the first of the person's answers that shares a word
with ESCO's record of that occupation, and the essential skill or title holding the word (or
the word itself, from the description); with no shared word, the first answer and the title.
Its output passes the same check and is stored with origin `fixture`. It exercises the
product offline; it does not evaluate explanations.
"""

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
    content_words,
)

CLAIM = "Demo explainer (synthetic): Nessa links one of your answers to ESCO's record of this work."


def prompt_context(prompt: str) -> PromptExplanationContext:
    if not prompt.startswith(CONTEXT_MARKER):
        raise ValueError("the prompt has no explanation context")
    return PromptExplanationContext.model_validate_json(prompt[len(CONTEXT_MARKER) :])


def _quotable(text: str) -> bool:
    return QUOTE_CHARS[0] <= len(text) <= QUOTE_CHARS[1] and bool(content_words(text))


def _link(answers: list[str], occupation: PromptOccupation) -> tuple[str, str]:
    """An answer and the part of the record it shares a content word with; else the first
    answer and the title, or the description's first content word if the title has none."""
    for answer in answers:
        shared = content_words(answer)
        for part in (*occupation.essential_skills, occupation.title):
            if shared & content_words(part) and _quotable(part):
                return answer, part
        common = sorted(shared & content_words(occupation.description))
        if common:
            return answer, common[0]
    if _quotable(occupation.title):
        return answers[0], occupation.title
    return answers[0], min(content_words(occupation.description), default=occupation.title)


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
