import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ErrorCode } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { NotInvited, RequestFailure } from "./PageState";

function failure(code: ErrorCode, status: number) {
  return new ApiError(status, {
    code,
    message: "never shown",
    retryable: false,
    stage: "request",
    correlation_id: "c1",
    details: {},
  });
}

describe("[STATE-01][API-02] an error code is shown in its state's words and tone", () => {
  it.each([
    ["STORE_UNAVAILABLE", 503, "error"],
    ["STALE_INPUT_VERSION", 409, "stale"],
    ["INSUFFICIENT_EVIDENCE", 422, "unknown"],
    ["SOLVE_LIMIT_REACHED", 422, "neutral"],
  ] as const)("%s reads as %s", (code, status, tone) => {
    const { container } = render(<RequestFailure error={failure(code, status)} />);

    expect(container.querySelector(".alert")).toHaveAttribute("data-tone", tone);
    expect(screen.queryByText("never shown")).not.toBeInTheDocument();
    expect(screen.getByText("Reference c1")).toBeInTheDocument();
  });
});

describe("[SEC-01][UI-06] a refused account says its cause once (V-10)", () => {
  it("has one headline, the recovery as supporting copy in an announced notice", () => {
    render(
      <NotInvited
        error={failure("NOT_INVITED", 403)}
        actions={
          <button type="button" className="btn btn-secondary">
            Sign out
          </button>
        }
      />,
    );

    expect(screen.getAllByText("This account isn't invited")).toHaveLength(1);
    expect(
      screen.getByRole("heading", { level: 1, name: "This account isn't invited" }),
    ).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent("Sign in with an invited account.");
    expect(screen.getByRole("alert")).toHaveTextContent("Reference c1");
    expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
  });
});
