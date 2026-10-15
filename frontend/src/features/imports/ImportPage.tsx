import { FormEvent, useState } from "react";
import { BackLink } from "../../components/BackLink";
import { api } from "../../lib/api";
import { ErrorNote } from "../dashboard/OverviewPage";

type Preview = {
  columns: string[];
  mapping: Record<string, string | null>;
  accepted_rows: number;
  rejected_rows: number;
  duplicate_rows: number;
  assumptions: string[];
  issues: { row_number: number; code: string; message: string }[];
  preview: Record<string, unknown>[];
  encoding: string;
  delimiter: string;
};

const FIELDS = ["date", "product_name", "sku", "quantity", "invoice_number", "selling_price", "unit_cost", "current_stock", "in_stock"];

export function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(confirm: boolean) {
    if (!file) return;
    setBusy(true);
    setError(null);
    const body = new FormData();
    body.set("file", file);
    const mapped = Object.fromEntries(Object.entries(mapping).filter(([, value]) => value));
    if (Object.keys(mapped).length) body.set("mapping", JSON.stringify(mapped));
    try {
      if (confirm) {
        const result = await api<{ accepted_rows: number; rejected_rows: number; duplicate_rows: number }>("/api/imports", {
          method: "POST",
          body,
        });
        setMessage(`Imported ${result.accepted_rows} rows. Rejected ${result.rejected_rows}. Duplicates ${result.duplicate_rows}.`);
      } else {
        const result = await api<Preview>("/api/imports/preview", { method: "POST", body });
        setPreview(result);
        const next: Record<string, string> = {};
        Object.entries(result.mapping).forEach(([key, value]) => {
          if (value) next[key] = value;
        });
        setMapping(next);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed.");
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(false);
  }

  const step = message ? "Result" : preview ? "Confirm" : file ? "Check" : "Choose file";

  return (
    <section className="max-w-3xl">
      <BackLink to="/app">Overview</BackLink>
      <h1 className="text-4xl">Import sales</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        Map the columns, read every problem, then confirm. The same file cannot be imported twice.
      </p>
      <ol className="mt-4 flex flex-wrap gap-2 text-sm" aria-label="Import steps">
        {["Choose file", "Check", "Map", "Confirm", "Result"].map((name) => (
          <li key={name} className={`rounded-full border px-3 py-1 ${name === step ? "border-[var(--ink)] text-[var(--ink)]" : "border-[var(--line)] text-[var(--muted)]"}`} aria-current={name === step ? "step" : undefined}>
            {name}
          </li>
        ))}
      </ol>
      <p className="mt-4 max-w-xl text-sm">This copy keeps the file on this computer. A hosted copy would not stay private to you.</p>
      <a className="mt-3 inline-block text-sm underline" href="/api/imports/template">
        Download the CSV template
      </a>
      <form className="mt-6 grid gap-3" onSubmit={onSubmit}>
        <label className="grid gap-1 text-sm">
          Billing CSV
          <input
            className="field"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button disabled={!file || busy} className="btn w-fit" type="submit">
          Check file
        </button>
      </form>
      {error ? <div className="mt-4"><ErrorNote message={error} /></div> : null}
      {preview ? (
        <div className="mt-6 grid gap-4">
          <p className="text-sm">
            Read as {preview.encoding}, delimiter "{preview.delimiter}".
          </p>
          <dl className="khata khata-plain grid gap-2 text-sm sm:grid-cols-3">
            <div><dt className="text-[var(--muted)]">Can import</dt><dd className="nums text-xl">{preview.accepted_rows}</dd></div>
            <div><dt className="text-[var(--muted)]">Problems</dt><dd className="nums text-xl">{preview.rejected_rows}</dd></div>
            <div><dt className="text-[var(--muted)]">Duplicates</dt><dd className="nums text-xl">{preview.duplicate_rows}</dd></div>
          </dl>
          {preview.duplicate_rows > 0 ? (
            <p role="status">This file repeats {preview.duplicate_rows} rows. Importing the same file again is rejected.</p>
          ) : null}
          <div className="grid gap-3 md:grid-cols-2">
            {FIELDS.map((field) => (
              <label key={field} className="grid gap-1 text-sm">
                <span>{field}</span>
                <span className="text-[var(--muted)]">{mapping[field] ? "Likely match" : "Please check"}</span>
                <select
                  className="field"
                  value={mapping[field] ?? ""}
                  onChange={(event) => setMapping({ ...mapping, [field]: event.target.value })}
                >
                  <option value="">Not mapped</option>
                  {preview.columns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <button type="button" className="btn btn-quiet w-fit" onClick={() => void send(false)}>
            Refresh check
          </button>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="mb-2 text-left">Preview of rows that can be imported</caption>
              <tbody>
                {preview.preview.map((row, index) => (
                  <tr key={index} className="border-t border-[var(--line)]">
                    <td className="py-2">{String(row.sale_date)}</td>
                    <td>{String(row.product_name)}</td>
                    <td>{String(row.quantity)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {preview.issues.length ? (
            <ul className="grid gap-2 text-sm">
              {preview.issues.map((issue) => (
                <li key={`${issue.row_number}-${issue.code}`}>
                  Row {issue.row_number}: {issue.message} Correct the row, then check the file again.
                </li>
              ))}
            </ul>
          ) : null}
          <ul className="text-sm text-[var(--muted)]">
            {preview.assumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <button type="button" disabled={busy || preview.accepted_rows === 0} className="btn w-fit" onClick={() => void send(true)}>
            Import these rows
          </button>
        </div>
      ) : null}
      {message ? <p className="mt-4" role="status">{message}</p> : null}
    </section>
  );
}
