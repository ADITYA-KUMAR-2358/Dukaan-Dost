export function ProvenanceTag({ label, detail }: { label: string; detail?: string }) {
  return (
    <span className="prov-tag" title={detail} tabIndex={0}>
      {label}
    </span>
  );
}

export function forecastProvenance(modelId: string | null, fallbackReason: string | null) {
  if (!modelId) {
    if (fallbackReason === "fewer_than_7_observed_days") {
      return { label: "Not enough history", detail: "Fewer than 7 observed days." };
    }
    return { label: "Engine not recorded", detail: fallbackReason?.replaceAll("_", " ") ?? "This run did not record an engine." };
  }
  if (modelId.startsWith("tabpfn")) {
    const version = modelId.slice("tabpfn-".length);
    return { label: version ? `TabPFN v${version}` : "TabPFN", detail: "This run used TabPFN." };
  }
  const named: Record<string, string> = {
    seasonal_naive_7: "Fallback: seasonal pattern",
    moving_average_7: "Fallback: moving average",
    croston: "Fallback: intermittent demand",
  };
  return {
    label: named[modelId] ?? `Fallback: ${modelId.replaceAll("_", " ")}`,
    detail: fallbackReason ? fallbackReason.replaceAll("_", " ") : "A named baseline ran. This is not a TabPFN result.",
  };
}

export function explanationProvenance(source: string) {
  if (source === "gemma") return { label: "Explained by Gemma (local)", detail: "The wording came from the local model. The numbers were not changed." };
  return { label: "Plain explanation (local AI not running)", detail: "Template wording from the same calculated numbers." };
}
