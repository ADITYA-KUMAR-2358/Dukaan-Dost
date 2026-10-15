export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown[];

  constructor(status: number, code: string, message: string, details: unknown[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function apiBase() {
  const configured = import.meta.env.VITE_API_BASE?.trim() ?? "";
  return configured.replace(/\/$/, "");
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    let code = "request_failed";
    let message = "The request could not be completed.";
    let details: unknown[] = [];
    try {
      const payload = await response.json();
      code = payload.error?.code ?? code;
      message = payload.error?.message ?? message;
      details = payload.error?.details ?? [];
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(response.status, code, message, details);
  }
  const type = response.headers.get("content-type") ?? "";
  if (type.includes("text/csv")) {
    return (await response.text()) as T;
  }
  return (await response.json()) as T;
}

export type Shop = { id: string; name: string; kind: string; is_demo: boolean };

export type Product = {
  id: string;
  sku: string;
  name: string;
  category: string;
  unit: string;
  selling_price: number | null;
  unit_cost: number | null;
  current_stock: number | null;
  incoming_qty: number;
  min_stock: number | null;
  lead_time_days: number | null;
  pack_size: number | null;
  moq: number | null;
  supplier_name: string | null;
  archived: boolean;
};

export type Dashboard = {
  shop: { id: string; name: string; is_demo: boolean };
  active_products: number;
  inventory_value: number | null;
  inventory_value_products: number;
  products_missing_cost: number;
  reorder_count: number;
  stockout_risk_count: number;
  slow_moving_count: number;
  demand_trend: { recent_7_days: number; prior_7_days: number } | null;
  last_import: { filename: string; accepted_rows: number; rejected_rows: number; created_at: string } | null;
  last_forecast: { id: string; status: string; completed_at: string | null } | null;
  has_forecast: boolean;
};
