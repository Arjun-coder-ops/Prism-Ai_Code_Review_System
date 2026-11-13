import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("presents the PRISM foundation state", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "PRISM is ready for foundation work" }),
    ).toBeInTheDocument();
  });
});
