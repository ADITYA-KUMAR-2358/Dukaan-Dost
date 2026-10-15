# Sample billing file

`kirana_billing.csv` is a fictional shop, Sharma Kirana, from 1 July 2026 through 12 October 2026.

It is synthetic. Do not treat the quantities as a real store.

The file is built to exercise the app:

- Steady sellers: Amul Butter 100g, Tata Salt 1kg, Parle-G 800g.
- Rising demand: Cycle Agarbatti.
- Fading demand: Raincoat Medium.
- Intermittent demand: ORS Sachet.
- Short history: Protein Bar, sales only from 1 October 2026.
- Sparse history: Ayurvedic Hair Oil.
- A stockout: Maggi 70g is marked `in_stock=no` from 1 September 2026 through 10 September 2026. Those days are not evidence of low demand.

`current_stock`, cost, lead time, pack size, and minimum order are filled on the last row of each product. Dates are ISO. Ambiguous dates elsewhere in the app are read day-first.

Regenerate the file from the backend folder:

```powershell
..\.venv\Scripts\python -c "from app.services.sample_catalog import write_csv; from pathlib import Path; print(write_csv(Path('../samples/kirana_billing.csv')))"
```
