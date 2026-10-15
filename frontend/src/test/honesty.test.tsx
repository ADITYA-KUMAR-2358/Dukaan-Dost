import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { isHostedHost } from "../components/ServerWake";
import { ProvenanceTag, forecastProvenance } from "../components/ProvenanceTag";
import { DataLocationChip, SampleBanner } from "../components/SampleBanner";
import { displayQuantity } from "../lib/display";

describe("provenance", () => {
  it("names the engine and version", () => {
    const tag = forecastProvenance("tabpfn-2.5", null);
    render(<ProvenanceTag label={tag.label} />);
    expect(screen.getByText("TabPFN v2.5")).toBeInTheDocument();
  });

  it("labels a fallback and a missing engine", () => {
    expect(forecastProvenance("moving_average_7", "thin").label).toBe("Fallback: moving average");
    expect(forecastProvenance(null, null).label).toBe("Engine not recorded");
  });
});

describe("missing quantities", () => {
  it("keeps a real zero and labels an unknown quantity", () => {
    expect(displayQuantity(null, "packets")).toBe("Not set");
    expect(displayQuantity(0, "packets")).toBe("0 packets");
  });
});

describe("hosted server notice", () => {
  it("stays off on this computer and on for a public host", () => {
    expect(isHostedHost("localhost")).toBe(false);
    expect(isHostedHost("127.0.0.1")).toBe(false);
    expect(isHostedHost("dukaandost.onrender.com")).toBe(true);
  });
});

describe("sample shop", () => {
  it("shows the sample banner and where the data lives", () => {
    render(
      <>
        <SampleBanner onUseMine={vi.fn()} />
        <DataLocationChip />
      </>,
    );
    expect(screen.getByText("Sample shop. Fictional data.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use my shop" })).toBeInTheDocument();
    expect(screen.getByText("On this computer")).toBeInTheDocument();
  });
});
