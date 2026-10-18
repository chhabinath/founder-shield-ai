import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the landing screen with a Start Interview action", () => {
    render(<App />);
    expect(
      screen.getByRole("button", { name: /start interview/i })
    ).toBeInTheDocument();
  });

  it("advances past the landing screen when starting", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /start interview/i }));
    expect(screen.queryByText(/turn a vague problem/i)).not.toBeInTheDocument();
  });
});
