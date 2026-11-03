"""The deterministic demo query proposer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture keeps the live adapter's contract, labelled synthetic).

It reads the same prompt a live model reads and answers the same discovery schema: each
answer text becomes a query in the channel its field implies (enjoyed tasks: tasks;
confident and evidenced tasks and the current role: transferable; a target title: the same
work elsewhere; work style: environment, which the slate does not run for a one-word
answer, as it would not a model's; a qualification: none, so it is never searched). It
proposes no title hypotheses and no aim higher ideas: it never invents a title. Its output
passes the same check and is stored with origin `fixture`. It exercises the product offline;
it does not evaluate discovery.
"""

from careerwright.profile.discovery import (
    CONTEXT_MARKER,
    MAX_QUERIES,
    QUERY_CHARS,
    DiscoveryOutput,
    ModelQuery,
    PromptDiscoveryContext,
    QueryChannel,
)
from careerwright.profile.interview import ProfileField

_CHANNEL = {
    ProfileField.ENJOYED_TASKS: QueryChannel.TASKS,
    ProfileField.CONFIDENT_TASKS: QueryChannel.TRANSFERABLE,
    ProfileField.EVIDENCED_TASKS: QueryChannel.TRANSFERABLE,
    ProfileField.CURRENT_ROLE: QueryChannel.TRANSFERABLE,
    ProfileField.TARGET_TITLES: QueryChannel.CROSS_INDUSTRY,
    ProfileField.WORK_STYLE: QueryChannel.ENVIRONMENT,
}


def prompt_context(prompt: str) -> PromptDiscoveryContext:
    if not prompt.startswith(CONTEXT_MARKER):
        raise ValueError("the prompt has no discovery context")
    return PromptDiscoveryContext.model_validate_json(prompt[len(CONTEXT_MARKER) :])


def fixture_queries(context: PromptDiscoveryContext) -> DiscoveryOutput:
    queries: list[ModelQuery] = []
    seen: set[str] = set()
    for answer in context.answers:
        channel = _CHANNEL.get(answer.field)
        text = " ".join(answer.text.split())
        key = text.casefold()
        if channel is None or key in seen or not QUERY_CHARS[0] <= len(text) <= QUERY_CHARS[1]:
            continue
        seen.add(key)
        queries.append(ModelQuery(text=text, channel=channel, based_on=[answer.text]))
    return DiscoveryOutput(queries=queries[:MAX_QUERIES], hypotheses=[], aim_higher=[])
