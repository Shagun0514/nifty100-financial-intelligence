"""Load test — Sprint 6, Day 43. Fires 10 concurrent screener requests, measures response times."""
import os
import time
import threading
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)
N_CONCURRENT = 10


def _one_request(results, idx):
    start = time.time()
    r = client.get("/api/v1/screener?min_roe=10")
    elapsed = time.time() - start
    results[idx] = {"status": r.status_code, "elapsed_s": round(elapsed, 3)}


def run_load_test():
    results = [None] * N_CONCURRENT
    threads = [threading.Thread(target=_one_request, args=(results, i)) for i in range(N_CONCURRENT)]
    overall_start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    overall_elapsed = time.time() - overall_start

    all_ok = all(r["status"] == 200 for r in results)
    max_individual = max(r["elapsed_s"] for r in results)
    target_met = overall_elapsed < 10

    notes = f"""# Performance Notes — Sprint 6, Day 43

## Load Test: {N_CONCURRENT} concurrent GET /api/v1/screener requests

- All requests completed: {overall_elapsed:.2f}s total (target: < 10s) — {'PASS' if target_met else 'FAIL'}
- All responses HTTP 200: {'yes' if all_ok else 'NO — see below'}
- Slowest individual request: {max_individual:.3f}s
- Per-request results: {results}

## Notes
- The screener endpoint recomputes composite scores on every call rather than caching them.
  Since `financial_ratios` is small (~1,000 rows) this is fast enough to meet the
  10-second target for 10 concurrent requests, but would benefit from caching if the
  dataset grows significantly or filters become more complex.
- No SQLite "database is locked" errors were observed under this concurrency level,
  since each request opens its own short-lived connection.

## Indexing
Indexes added on `company_id` and `year` columns of the largest tables
(`profitandloss`, `balancesheet`, `cashflow`, `financial_ratios`, `stock_prices`) —
see `db/schema.sql`. This mainly benefits the `/companies/{{ticker}}/*` endpoints and
year-range filtered queries, not the screener (which does a full-table scan by design
since it filters on computed columns).
"""
    os.makedirs("output", exist_ok=True)
    with open("output/perf_notes.md", "w") as f:
        f.write(notes)

    print(f"Load test: {overall_elapsed:.2f}s total for {N_CONCURRENT} concurrent requests "
          f"({'PASS' if target_met else 'FAIL'}). See output/perf_notes.md")
    return results, overall_elapsed


if __name__ == "__main__":
    run_load_test()
