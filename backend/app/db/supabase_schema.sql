-- Shop tables for the Supabase Data API.
-- Row level security stays on. The publishable key is public and has no access.
-- The API uses SUPABASE_SECRET_KEY, which Supabase treats as the service role.

create table if not exists public.shops (
  id text primary key,
  name text not null,
  kind text not null,
  is_demo boolean not null,
  created_at timestamptz not null
);

create table if not exists public.products (
  id text primary key,
  shop_id text not null references public.shops (id) on delete cascade,
  sku text not null,
  name text not null,
  category text not null,
  unit text not null,
  selling_price double precision,
  unit_cost double precision,
  current_stock double precision,
  incoming_qty double precision not null,
  min_stock double precision,
  lead_time_days integer,
  pack_size integer,
  moq integer,
  supplier_name text,
  archived boolean not null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  unique (shop_id, sku)
);

create table if not exists public.import_batches (
  id text primary key,
  shop_id text not null references public.shops (id) on delete cascade,
  filename text not null,
  content_hash text not null,
  encoding text not null,
  delimiter text not null,
  total_rows integer not null,
  accepted_rows integer not null,
  rejected_rows integer not null,
  duplicate_rows integer not null,
  assumptions_json text not null,
  issues_json text not null,
  created_at timestamptz not null,
  unique (shop_id, content_hash)
);

create table if not exists public.sale_lines (
  id text primary key,
  shop_id text not null references public.shops (id) on delete cascade,
  product_id text not null references public.products (id) on delete cascade,
  import_batch_id text references public.import_batches (id) on delete set null,
  invoice_number text,
  sale_date date not null,
  quantity double precision not null,
  returned_quantity double precision not null,
  selling_price double precision,
  unit_cost double precision,
  discount double precision,
  stockout boolean not null,
  fingerprint text not null,
  unique (shop_id, fingerprint)
);

create table if not exists public.inventory_movements (
  id text primary key,
  shop_id text not null references public.shops (id) on delete cascade,
  product_id text not null references public.products (id) on delete cascade,
  movement_type text not null,
  quantity double precision not null,
  note text,
  created_at timestamptz not null
);

create table if not exists public.forecast_runs (
  id text primary key,
  shop_id text not null references public.shops (id) on delete cascade,
  horizon_days integer not null,
  status text not null,
  summary_json text not null,
  error_code text,
  created_at timestamptz not null,
  completed_at timestamptz
);

create table if not exists public.forecast_points (
  id text primary key,
  run_id text not null references public.forecast_runs (id) on delete cascade,
  product_id text not null references public.products (id) on delete cascade,
  forecast_date date not null,
  predicted_qty double precision not null,
  baseline_qty double precision not null,
  model_id text not null,
  baseline_id text not null
);

create table if not exists public.recommendations (
  id text primary key,
  shop_id text not null references public.shops (id) on delete cascade,
  product_id text not null references public.products (id) on delete cascade,
  run_id text not null references public.forecast_runs (id) on delete cascade,
  reorder_point double precision,
  safety_stock double precision,
  lead_time_demand double precision,
  suggested_qty double precision,
  policy text not null,
  slow_status text not null,
  flags_json text not null,
  facts_json text not null,
  user_qty double precision,
  user_note text,
  created_at timestamptz not null
);

create table if not exists public.app_settings (
  shop_id text primary key references public.shops (id) on delete cascade,
  language text not null,
  service_level double precision not null,
  coverage_days integer not null,
  horizon_days integer not null,
  prefer_tabpfn boolean not null,
  ollama_model text not null
);

create table if not exists public.workspace_state (
  id integer primary key,
  active_shop_id text references public.shops (id) on delete set null
);

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'shops', 'products', 'import_batches', 'sale_lines', 'inventory_movements',
    'forecast_runs', 'forecast_points', 'recommendations', 'app_settings', 'workspace_state'
  ]
  loop
    execute format('alter table public.%I enable row level security', table_name);
    execute format('drop policy if exists api_access on public.%I', table_name);
    execute format('revoke all on public.%I from anon, authenticated', table_name);
    execute format(
      'grant select, insert, update, delete on public.%I to service_role',
      table_name
    );
  end loop;
end $$;

notify pgrst, 'reload schema';
