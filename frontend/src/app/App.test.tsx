import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits a pull request and renders its asynchronous status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ id: "review-1", status: "queued", head_sha: "abc123" }),
          { status: 202 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "review-1",
            status: "completed",
            head_sha: "abc123",
            findings: [],
          }),
          { status: 200 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.change(screen.getByLabelText("Public GitHub pull request URL"), {
      target: { value: "https://github.com/octocat/Hello-World/pull/1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review pull request" }));

    await waitFor(() => {
      expect(screen.getByText("Review status: completed")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/v1/reviews",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/reviews/review-1");
    expect(
      screen.getByText("No deterministic, evidence-backed findings were identified."),
    ).toBeInTheDocument();
  });
});
