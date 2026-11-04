import type { OptionResearchEstimateOut, OptionResearchOut, RunOut } from "@/generated/api";

export const optionEstimate: OptionResearchEstimateOut = {
  model_id: "test-model",
  model_mode: "standard",
  search_maximum_nano_usd: 40_000_000,
  pages_maximum_nano_usd: 100_000_000,
  combined_maximum_nano_usd: 140_000_000,
  hard_maximum_nano_usd: 250_000_000,
  refused_scope: null,
};

export function optionRun(
  runId: string,
  status: RunOut["status"],
  kind: RunOut["kind"] = "source_search",
): RunOut {
  return {
    run_id: runId,
    kind,
    status,
    failure_class: null,
    data_mode: "live_assisted",
    synthetic: false,
    model_id: "test-model",
    model_mode: "standard",
    created_at: "2026-11-03T12:00:00Z",
    started_at: "2026-11-03T12:00:01Z",
    finished_at: status === "complete" ? "2026-11-03T12:00:04Z" : null,
    cancel_requested_at: null,
    attempts: [],
    output: null,
  };
}

export const optionResearch: OptionResearchOut = {
  research_id: "11111111-1111-4111-8111-111111111111",
  target: "Data quality analyst",
  city: "Leeds",
  status: "completed",
  coverage: "complete",
  search: optionRun("22222222-2222-4222-8222-222222222222", "complete"),
  reading: optionRun("33333333-3333-4333-8333-333333333333", "complete", "acquisition"),
  candidates: 2,
  empty_reason: null,
  pages_attempted: 2,
  pages_read: 2,
  pages_blocked: 0,
  pages_failed: 0,
  failure_reason: null,
  records: [
    {
      record_id: "44444444-4444-4444-8444-444444444444",
      kind: "course",
      title: "Evening data course",
      source_url: "https://college.example/course",
      retrieved_on: "2026-11-03T12:00:04Z",
      expires_on: "2026-11-10T12:00:04Z",
      expired: false,
      review_state: "proposed",
      citations: {
        title: {
          basis: "source",
          source_hash: "sha256:test",
          locator: "13:32",
          excerpt: "Evening data course",
          retrieved_on: "2026-11-03",
        },
      },
    },
  ],
};
