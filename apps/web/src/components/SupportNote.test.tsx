import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SupportNoteOut, SupportResourceOut } from "@/generated/api";
import { SupportNote } from "./SupportNote";

// The services as the API sends them (support-policy-12; `careerwright.profile.safety`).
const SAMARITANS: SupportResourceOut = {
  name: "Samaritans",
  contact: "Call 116 123 (free, any time, day or night)",
  when: "To talk to someone who will listen",
  source_url: "https://www.samaritans.org/how-we-can-help/contact-samaritan/",
  checked_on: "2026-10-28",
};
const SHOUT: SupportResourceOut = {
  name: "Shout",
  contact: "Text SHOUT to 85258 (free, 24/7)",
  when: "If you would rather text than talk",
  source_url: "https://giveusashout.org/get-help/",
  checked_on: "2026-10-28",
};
const CHILDLINE: SupportResourceOut = {
  name: "Childline",
  contact: "Call 0800 1111 or use the 1-2-1 chat online (free, 24 hours a day, 7 days a week)",
  when: "For children and young people",
  source_url: "https://www.childline.org.uk/get-support/contacting-childline/",
  checked_on: "2026-11-01",
};
const note = (resources: SupportResourceOut[]): SupportNoteOut => ({
  policy_version: "support-policy-12",
  review_status: "not yet reviewed as built",
  message: "If anything you mentioned is about how you are feeling, support is available.",
  resources,
});

describe("SupportNote", () => {
  it("[PROF-15] lists Childline beside the other services, for children and young people", () => {
    render(<SupportNote note={note([SAMARITANS, SHOUT, CHILDLINE])} onDismiss={() => undefined} />);

    const items = screen.getAllByRole("listitem").map((item) => item.textContent);
    expect(items).toEqual([
      "Samaritans: Call 116 123 (free, any time, day or night). To talk to someone who will listen.",
      "Shout: Text SHOUT to 85258 (free, 24/7). If you would rather text than talk.",
      "Childline: Call 0800 1111 or use the 1-2-1 chat online (free, 24 hours a day, 7 days a " +
        "week). For children and young people.",
    ]);
  });

  it("[PROF-15] says when each service was checked, never one date for all", () => {
    render(<SupportNote note={note([SAMARITANS, SHOUT, CHILDLINE])} onDismiss={() => undefined} />);

    expect(
      screen.getByText(/^These services were checked on their own websites/),
    ).toHaveTextContent(
      "These services were checked on their own websites on 28 October 2026, and Childline on " +
        "1 November 2026.",
    );
  });

  it("keeps one date when every service was checked on the same day", () => {
    render(<SupportNote note={note([SAMARITANS, SHOUT])} onDismiss={() => undefined} />);

    expect(
      screen.getByText(/^These services were checked on their own websites/),
    ).toHaveTextContent("These services were checked on their own websites on 28 October 2026.");
  });
});
