import { FormEvent, useEffect, useState } from "react";
import { api } from "../lib/api";

export function ShopNameForm({
  name,
  onSaved,
}: {
  name: string;
  onSaved: (name: string) => void;
}) {
  const [value, setValue] = useState(name);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setValue(name);
  }, [name]);

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const payload = await api<{ shop: { name: string } }>("/api/workspaces/name", {
        method: "PATCH",
        body: JSON.stringify({ name: value.trim() }),
      });
      setMessage("Shop name saved.");
      window.dispatchEvent(new CustomEvent("dukaan-shop"));
      onSaved(payload.shop.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the shop name.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="mt-4 grid max-w-md gap-2" onSubmit={(event) => void save(event)}>
      <label className="text-sm" htmlFor="shop-name">
        Shop name
        <input
          id="shop-name"
          className="field"
          value={value}
          maxLength={80}
          required
          onChange={(event) => setValue(event.target.value)}
        />
      </label>
      <button type="submit" className="btn w-fit" disabled={busy}>
        {busy ? "Saving..." : "Save name"}
      </button>
      {message ? <p className="text-sm">{message}</p> : null}
      {error ? <p className="text-sm text-[var(--danger)]" role="alert">{error}</p> : null}
    </form>
  );
}
