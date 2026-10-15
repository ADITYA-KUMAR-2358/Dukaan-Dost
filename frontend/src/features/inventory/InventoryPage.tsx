import { FormEvent, useEffect, useState } from "react";
import { BackLink } from "../../components/BackLink";
import { api, type Product } from "../../lib/api";
import { displayQuantity } from "../../lib/display";
import { ErrorNote } from "../dashboard/OverviewPage";

export function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  async function load() {
    try {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      if (category) params.set("category", category);
      const payload = await api<{ products: Product[]; categories: string[] }>(`/api/products?${params.toString()}`);
      setProducts(payload.products);
      setCategories(payload.categories);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load products.");
    }
  }

  useEffect(() => {
    void load();
    // Search runs again only when the form is submitted.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section>
      <BackLink to="/app">Overview</BackLink>
      <h1 className="text-4xl">Inventory</h1>
      <form
        className="mt-4 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void load();
        }}
      >
        <label className="min-w-48 text-sm">
          Search
          <input className="field" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <label className="text-sm">
          Category
          <select className="field" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All</option>
            {categories.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <button className="btn btn-quiet self-end" type="submit">
          Apply
        </button>
      </form>
      {error ? <div className="mt-4"><ErrorNote message={error} /></div> : null}
      {products.length === 0 ? <p className="mt-6">No products yet. Open the sample shop or import a CSV.</p> : null}
      <ul className="mt-4 grid gap-3 md:hidden">
        {products.map((product) => (
          <li key={product.id}>
            <button type="button" className="sheet w-full py-3 text-left" onClick={() => setSelected(product.id)}>
              <span className="flex items-start justify-between gap-3">
                <span>
                  {product.name}
                  <span className="mt-1 block text-[var(--muted)]">{product.sku}</span>
                </span>
                <StockTag product={product} />
              </span>
              <span className="mt-3 grid grid-cols-3 gap-2">
                <span>On hand <span className="nums block">{displayQuantity(product.current_stock, product.unit)}</span></span>
                <span>Reorder <span className="nums block">{displayQuantity(product.min_stock, product.unit)}</span></span>
                <span>Lead <span className="nums block">{product.lead_time_days === null ? "Not set" : `${displayQuantity(product.lead_time_days)} days`}</span></span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      <div className="khata khata-plain mt-4 hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[var(--muted)]">
              <th className="py-2 font-medium">Product</th>
              <th className="py-2 text-right font-medium">Stock</th>
              <th className="py-2 text-right font-medium">Min</th>
              <th className="py-2 text-right font-medium">Lead time</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td className="py-3">
                  <button type="button" className="text-left" onClick={() => setSelected(product.id)}>
                    {product.name}
                    <span className="mt-1 block"><StockTag product={product} /></span>
                    <span className="block text-[var(--muted)]">{product.sku}</span>
                  </button>
                </td>
                <td className="nums py-3 text-right">{displayQuantity(product.current_stock, product.unit)}</td>
                <td className="nums py-3 text-right">{displayQuantity(product.min_stock, product.unit)}</td>
                <td className="nums py-3 text-right">{product.lead_time_days === null ? "Not set" : `${displayQuantity(product.lead_time_days)} days`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ProductEditor product={products.find((item) => item.id === selected) ?? null} onSaved={() => void load()} onClose={() => setSelected(null)} />
      <NewProduct onCreated={() => void load()} />
    </section>
  );
}

function StockTag({ product }: { product: Product }) {
  if (product.current_stock === null) return <span className="stock-tag stock-tag-still">Not set</span>;
  if (product.current_stock <= 0) return <span className="stock-tag stock-tag-check">Out of stock</span>;
  if (product.min_stock !== null && product.current_stock < product.min_stock) return <span className="stock-tag stock-tag-low">Running low</span>;
  return <span className="stock-tag stock-tag-enough">Enough</span>;
}

function fieldValue(value: number | null) {
  return value === null ? "" : String(value);
}

function ProductEditor({ product, onSaved, onClose }: { product: Product | null; onSaved: () => void; onClose: () => void }) {
  const [stock, setStock] = useState("");
  const [minStock, setMinStock] = useState("");
  const [lead, setLead] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const productId = product?.id ?? null;

  useEffect(() => {
    setStock(fieldValue(product?.current_stock ?? null));
    setMinStock(fieldValue(product?.min_stock ?? null));
    setLead(fieldValue(product?.lead_time_days ?? null));
    setMessage(null);
  }, [product?.id, product?.current_stock, product?.min_stock, product?.lead_time_days]);

  if (!productId) return null;

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      await api(`/api/products/${productId}`, {
        method: "PATCH",
        body: JSON.stringify({
          current_stock: stock === "" ? null : Number(stock),
          min_stock: minStock === "" ? null : Number(minStock),
          lead_time_days: lead === "" ? null : Number(lead),
        }),
      });
      setMessage("Saved.");
      onSaved();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not save.");
    }
  }

  async function receive() {
    try {
      await api("/api/inventory/movements", {
        method: "POST",
        body: JSON.stringify({ product_id: productId, movement_type: "receipt", quantity: 1, note: "Received one unit" }),
      });
      setMessage("Receipt recorded.");
      onSaved();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not record the receipt.");
    }
  }

  async function archive() {
    if (!window.confirm("Archive this product? Past sales stay in the shop.")) return;
    try {
      await api(`/api/products/${productId}`, { method: "PATCH", body: JSON.stringify({ archived: true }) });
      setMessage("Archived. History is still stored.");
      onSaved();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not archive.");
    }
  }

  return (
    <form className="parchi mt-6 grid max-w-md gap-3" onSubmit={(event) => void save(event)}>
      <button type="button" className="w-fit text-sm text-[var(--muted)]" onClick={onClose}>
        Back to the list
      </button>
      <h2 className="font-semibold">Edit selected product</h2>
      <label className="text-sm">Current stock<input className="field" value={stock} onChange={(event) => setStock(event.target.value)} /></label>
      <label className="text-sm">Minimum stock<input className="field" value={minStock} onChange={(event) => setMinStock(event.target.value)} /></label>
      <label className="text-sm">Lead time in days<input className="field" value={lead} onChange={(event) => setLead(event.target.value)} /></label>
      <div className="flex flex-wrap gap-2">
        <button className="btn" type="submit">Save details</button>
        <button className="btn btn-quiet" type="button" onClick={() => void receive()}>Receive 1</button>
        <button className="btn btn-quiet" type="button" onClick={() => void archive()}>Archive</button>
      </div>
      {message ? <p className="text-sm">{message}</p> : null}
    </form>
  );
}

function NewProduct({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/api/products", { method: "POST", body: JSON.stringify({ name, sku, current_stock: 0 }) });
      setName("");
      setSku("");
      setMessage("Product added.");
      onCreated();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not add the product.");
    }
  }

  return (
    <form className="mt-6 grid max-w-md gap-3" onSubmit={(event) => void create(event)}>
      <h2 className="font-semibold">Add a product</h2>
      <label className="text-sm">Name<input required className="field" value={name} onChange={(event) => setName(event.target.value)} /></label>
      <label className="text-sm">SKU<input required className="field" value={sku} onChange={(event) => setSku(event.target.value)} /></label>
      <button className="btn btn-quiet w-fit" type="submit">Add product</button>
      {message ? <p className="text-sm">{message}</p> : null}
    </form>
  );
}
