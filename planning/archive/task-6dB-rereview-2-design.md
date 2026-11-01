# Task 6d slice B, fix round 2: scoped re-review, design half (`design`)

Commits 667426e..51ca593 (aa0e66e to 51ca593). I read the fix list and the controller's
rulings, then the implementer's "Fix round 2" section (as unverified claims), then the package.

What I read in full at 51ca593:
- `FirstQuestion.tsx`, `SupportNote.tsx` and `world/settings.ts`;
- the `Conversation.tsx`, `ProfileEditor.tsx`, `WorkspaceShell.tsx` and `vocabulary.ts` hunks;
- the three e2e hunks and the new settings test;
- the `safety.py` hunk.

I skimmed the backend route hunks only where they decide what the web shows. I looked at the
390 × 844 captures `you--title-support` and `you--type-ahead-partial`. Line numbers are at
51ca593. No suite or browser was run, and I wrote no distress text.

### Spec Compliance
- **R-I1, the title panel below the field: addressed.**
  - The panel is now the first thing in the field's block, above the field
    (`FirstQuestion.tsx:247-258`). The status says "Support information is shown above the job
    title field." (`vocabulary.ts:884`).
  - The phone e2e checks the panel's bottom is above the field and its heading is in view at
    390 × 844 (`e2e/role-space.spec.ts`, "phone"). The real keyboard is a human check.
- **R-I2, "None of these is my job" below a phone's first screen: addressed.**
  - The person's own answer is the first option in every list (`FirstQuestion.tsx:144-147`).
    The partial capture shows "None of these is my job" directly under the question.
  - UI-12 now checks both lists at 390 × 844 (`e2e/conversation.spec.ts`).
- **R-M1, the arrowed option kept as an index: addressed.**
  - The option is kept by its key (`FirstQuestion.tsx:126`, `:149`, `:213`).
  - The partial list's own option has its own key (`:63-66`), so own words arrowed to before
    the list arrives never become a refusal, and Enter then keeps the words. Tested.
- **R-M2, the panel taken away undismissed: addressed.**
  - The conversation holds the title panel (`Conversation.tsx:397`). The start shows it after
    each later step (`:271-284`, `:305`, `:335`). Once the start is done, it sits above the
    reply field beside the message panel (`:625`). Tested after another title and after a skip.
- **R-M4, "Skip for now" while fixing: addressed.** It reads "Back to “Which of these is
  closest?”" (`Conversation.tsx:257`; `vocabulary.ts:889`). Tested.
- **Item 3, a real job title that trips the screen: addressed as ruled.**
  - The title isn't kept by itself. "Keep it as my job title" (`vocabulary.ts:886`) is offered
    in the panel while the screened words are in the field (`FirstQuestion.tsx:160-164`,
    `:231-239`). It moves under the field once the panel is dismissed (`:332`).
  - Keeping saves the title exactly as typed through the same command, with `keep_as_typed`
    (`:194-201`). Typing again and skipping stay open.
  - Nothing about the panel is stored (the report's tests; not re-run). The words stay "not yet
    reviewed as built" (`safety.py` `REVIEW_STATUS`).
- **The product owner's decision, What we know's direct entries: addressed.**
  - A save with a listed word is saved as usual and shows the same calm panel above Save
    changes (`ProfileEditor.tsx:317`). It stills the world and announces "Saved. Support
    information is shown above Save changes." (`:39`, `:247`). Dismiss returns focus to Save
    changes.
  - The policy version and status move to `support-policy-9`, and ADR 0007 has the line.
  - The new lines mirror the message panel's pair: "Your answers were saved as usual." and
    "…not saved; the reason is shown with them." (`safety.py:335-342`).
  - These lines (and the title line) keep the accepted first sentence, with "typed" for
    "mentioned". They are calm and non-diagnostic, and never repeat the words.
- **The implementer's concern: the tall title panel at 390 × 844.** My judgement:
  **acceptable, with a small layout fix.**
  - The capture shows the panel's heading, line and two or three services. The field,
    "Keep it as my job title", Dismiss and "Skip for now" are below the first screen.
  - "The decision stays on the first screen" protects the decision path from the world. Here
    what leads is the support panel. When the screen triggers, the policy itself sets the career
    step aside (a message's turn asks no career question), so the panel leading is right.
  - Its line, which is in view, names every way forward.
  - While the person is typing on a real phone, the browser keeps the focused field in view.
    The panel's bottom, where Keep and Dismiss sit, then lands just above it (human check).
  - The defect is smaller: the choice the line names sits after four services. See R2-M1.
- **The rulings:**
  - **Ruling 1, the line reworded to stay true: sound for its first claim.** "Careerwright keeps
    it as your job title only if you choose to" holds in every state. Its last sentence goes
    stale once the question is gone (R2-M2).
  - **Ruling 3, only the screen's own refusal silent: sound.** `calm` requires
    `reason == "support_screen"` (`FirstQuestion.tsx:155-158`). A stale "Keep it" now says why,
    instead of failing silently.
  - **Ruling 4, What we know screens only the entries a save adds: sound.** An old answer doesn't
    re-raise the panel on every later save, and each new entry is screened once, as each new
    message is. Undo restores earlier answers and is fairly left out. The conversation tray's
    typed edits are the implementer's open policy question. I agree it is one for the product
    owner.
  - **Rulings 2 and 7, Keep in the panel and own words first: sound.** Own words first is
    harmless over a UK list: the server decides the title's kind, so the same record results.
- **Panels counted so the world stays still: sound.** `useSupportPanels` counts each mounted
  panel's report (`world/settings.ts:29-35`). `report` is stable (`useCallback`), so each panel
  adds one on mount and removes one on unmount. A panel moving between steps nets zero, and
  React's double effects in development net zero too. The test covers two panels.
- ⚠️ **Cannot verify from diff:**
  - A real phone's keyboard over the title field and its panel; VoiceOver; Safari. Not run,
    requires human.
  - The panels' words (session W2 and the policy review). Not run, requires human.
  - `make check` and `make acceptance` (the implementer's runs).

### Strengths
- Both Important layout items are fixed at their cause. The panel sits where the message panel
  does, relative to its field. The person's own answer leads every list. Each now has a phone
  check that can fail, and the report shows them failing with the old layout.
- The way forward never leaves with the panel: "Keep it as my job title" stays under the field
  after a dismissal, while the screened words are there.
- One panel component, one policy and one count serve three places: the first question, the
  conversation and What we know.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- **R2-M1. Put the title panel's choice next to the line that names it** (`SupportNote.tsx`,
  actions after the services; `FirstQuestion.tsx:256`).
  - At 390 × 844 the panel's line says the person can keep the title. "Keep it as my job title"
    sits after four services, below the first screen. A person whose real job title trips the
    screen must scroll past the services to act.
  - Fix: render the title panel's actions right after its line, with the services below, and
    keep Dismiss where it is if preferred. Add a phone check that the heading, the line and Keep
    are in the first screen.
  - It touches the first ten seconds, so the controller may keep it in the task.
- **R2-M2. The title panel's last sentence outlives its question** (`safety.py:328-331`;
  `Conversation.tsx:625`). After "Skip for now", another title, or the start ending, the panel
  still says the person can "type again or skip this question", above the reply field, where
  neither is possible. These are policy words for session W2 and the policy review. I propose
  no wording.
- **R2-M3. A question for the controller: keeping screened words echoes them**
  (`Conversation.tsx:315`). After "Keep it as my job title", the start's kept-words line
  repeats the title in "Careerwright keeps “…” as your role". Round 1's ruling said the title is
  never echoed as "your role". Round 2's ruling makes keeping the same as "Use my own words"
  without saying whether the echo follows. The person chose to keep it, so this may be
  intended.
- **R2-M4. What we know's refused save shows its panel a form away from its notice**
  (`ProfileEditor.tsx:317`). The stale notice at the top takes focus. The panel sits above Save
  changes after all twelve answers, while its line says "the reason is shown with them". The
  case is rare (a stale save holding a listed word) but announced, and on a phone the panel is
  out of sight. Consider showing it beside the notice for a refused save.
- **R2-M5. Two panels can stack.** The title panel and a message panel can show together
  above the reply field, each with the full list of services (`Conversation.tsx:616-633`).
  Harmless, but heavy on a phone. A question for session W2.

### Assessment
**Task quality:** Approved
**Reasoning:** R-I1, R-I2, R-M1, R-M2, R-M4 and item 3 are addressed with tests that can fail,
and What we know's screen follows the product owner's decision. The rulings and the panel count
are sound. The tall panel at 390 × 844 is acceptable, since the support panel rightly leads.
What remains are Minors: moving its "Keep" choice up to the line that names it, and policy
words for session W2.
