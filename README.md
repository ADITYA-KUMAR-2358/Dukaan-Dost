# DukaanDost

Kam andaaza. Sahi stock. Behtar dukaan.

DukaanDost turns a small shop's billing CSV into item-level demand forecasts and reorder advice. Shops, sales, and forecasts are stored in Supabase when the project URL and a key are set. `SUPABASE_DB_URL` can stay empty. TabPFN runs through the Prior Labs API when `TABPFN_API_KEY` is set. Gemma runs when `LLM_API_KEY` is set. Empty keys stay on a named baseline and a template explanation.

## What works

- A public site with a working sample-product demonstration.
- A sample kirana that stays separate from your own shop.
- CSV preview, column mapping, row-level errors, and duplicate-file protection.
- Product and stock updates, with an audit row for receipts and adjustments.
- Forecasts from a seasonal, moving-average, or intermittent baseline.
- A TabPFN adapter that calls the Prior Labs API when `TABPFN_API_KEY` is set. Failures stay labelled as the baseline.
- Reorder points, pack size, slow-moving flags, and stockout flags from those numbers.
- English and Hinglish template explanations. Gemma through the Google OpenAI-compatible endpoint when `LLM_API_KEY` is set and the answer matches the numbers.
- CSV exports for inventory, forecasts, recommendations, import quality, and evaluation.

## What it does not claim

Forecasts are not guarantees. Inventory value uses unit cost only. A hosted server is not the same as a shop computer. Photographed ledgers are not read.

## Setup

From the repository root, in two terminals:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Choose the sample shop if you do not have a CSV yet.

Tests use a temporary SQLite file and do not call Supabase or Prior Labs. For tests only:

```powershell
cd backend
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
```

Copy `.env.example` to `.env`. Set `NEXT_PUBLIC_SUPABASE_URL` and `SUPABASE_SECRET_KEY`. The secret key is the backend credential. The publishable key is public, and `backend/app/db/supabase_schema.sql` does not grant it access. Run that file in the Supabase SQL editor. On a project that already ran an older copy of the file, run it again so the public policy is removed. Do that only after the secret key is in `.env`, or the API can no longer read the tables. `SUPABASE_DB_URL` stays empty. Leave `TABPFN_API_KEY` and `LLM_API_KEY` empty until you want those calls.

## Models

- TabPFN uses the `tabpfn-client` package and `TABPFN_API_KEY`. The key comes from Prior Labs. This deploy path does not download local TabPFN weights. If the key is empty or the call fails, the screen names the baseline.
- Gemma is optional. Paste a Google AI Studio key into `LLM_API_KEY`. If it is empty, or the call fails, explanations use a template and say so.

## Render

`render.yaml` is a Blueprint with two services: `dukaandost-api` (Python) and `dukaandost-web` (static site). Render will ask for `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `TABPFN_API_KEY`, and `LLM_API_KEY`. Leave `SUPABASE_DB_URL` blank.

The static site build sets `VITE_API_BASE` from the API's public URL. `CORS_ORIGINS` and `FRONTEND_ORIGIN` allow `https://dukaandost-web.onrender.com`. If Render gives the site a different host, change those two values to that origin.

A free Render web service sleeps after 15 minutes without a request. `.github/workflows/keep-alive.yml` pings `/health` every 10 minutes. After the blueprint is deployed and `/health` answers, add a repository secret or variable named `BACKEND_URL` and set it to that API origin with no trailing slash. Put the same value in `.env`. Until then leave both empty. A guessed host makes the workflow fail every 10 minutes. If the secret is missing, the workflow does nothing and does not fail. You can also run it by hand. GitHub may delay scheduled runs, and it pauses them after 60 days without commits.

While the site is open on that host, the page itself pings `/health` every 8 minutes. If the server is still waking, a saffron bar at the top says so and counts the seconds. That bar stays off on localhost.

## Docker

```powershell
docker compose up --build
```

The site is then on port 8080. Compose passes the Supabase URL and keys from `.env`. When those are empty, the API keeps a SQLite file in the `dukaan-data` volume. Put keys in `.env` only on your machine. Do not commit a filled key.

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m ruff check app tests
.\.venv\Scripts\python -m pytest
cd ..\frontend
npm test
npm run typecheck
npm run lint
npm run build
```

## License

The application code is MIT. See `LICENSE`. TabPFN weights are not covered by that license.
