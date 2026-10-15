import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import gsap from "gsap";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NotFoundPage } from "../pages/PublicPages";

function renderMissing() {
  const router = createMemoryRouter([{ path: "*", element: <NotFoundPage /> }], { initialEntries: ["/no-such-shelf"] });
  render(<RouterProvider router={router} />);
}

function matchMedia(reduce: boolean) {
  window.matchMedia = (query: string) =>
    ({
      matches: reduce && query.includes("reduce"),
      media: query,
      addEventListener() {},
      removeEventListener() {},
      addListener() {},
      removeListener() {},
      dispatchEvent() {
        return false;
      },
      onchange: null,
    }) as MediaQueryList;
}

describe("not found", () => {
  const previousTitle = document.title;

  afterEach(() => {
    document.title = previousTitle;
    matchMedia(false);
  });

  it("renders an unknown route with both ways back", () => {
    renderMissing();
    expect(document.title).toBe("Page not found | DukaanDost");
    expect(screen.getByRole("heading", { level: 1 })).toHaveFocus();
    expect(screen.getByRole("link", { name: "Back to Shop" }).getAttribute("href")).toBe("/");
    expect(screen.getAllByRole("link", { name: "Open Shutters" })[0].getAttribute("href")).toBe("/app");
  });

  it("rattles from a click and again from the keyboard", async () => {
    const user = userEvent.setup();
    const tween = vi.spyOn(gsap, "to");
    renderMissing();
    const shutter = screen.getByRole("button", { name: "Rattle the closed shop shutter" });
    await user.click(shutter);
    expect(await screen.findByText("Sorry! Come back tomorrow!")).toBeInTheDocument();
    const afterClick = tween.mock.calls.length;
    shutter.focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByText("Sorry! Come back tomorrow!")).toBeInTheDocument();
    expect(tween.mock.calls.length).toBeGreaterThan(afterClick);
    tween.mockRestore();
  });

  it("shows the message without animating when motion is reduced", async () => {
    const user = userEvent.setup();
    matchMedia(true);
    const tween = vi.spyOn(gsap, "to");
    renderMissing();
    await user.click(screen.getByRole("button", { name: "Rattle the closed shop shutter" }));
    expect(await screen.findByText("Sorry! Come back tomorrow!")).toBeInTheDocument();
    expect(tween).not.toHaveBeenCalled();
    tween.mockRestore();
  });
});
