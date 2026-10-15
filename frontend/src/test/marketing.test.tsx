import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { demoAdvice } from "../lib/demo";
import { DemoPanel, MarketingPage } from "../pages/MarketingPage";

describe("marketing", () => {
  it("sends the main call to action into the app", () => {
    render(
      <MemoryRouter>
        <MarketingPage />
      </MemoryRouter>,
    );
    const links = screen.getAllByRole("link", { name: "Open Shutters" });
    expect(links[0].getAttribute("href")).toBe("/app");
  });

  it("updates the sample forecast when the horizon changes", async () => {
    const user = userEvent.setup();
    render(<DemoPanel />);
    expect(screen.getByRole("rowheader", { name: /Example demand over 14 days/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "7 days" }));
    expect(screen.getByRole("rowheader", { name: /Example demand over 7 days/i })).toBeInTheDocument();
  });
});

describe("demo math", () => {
  it("repeats the weekday pattern", () => {
    const advice = demoAdvice([1, 2, 3, 4, 5, 6, 7], 7);
    expect(advice.forecast).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });
});
