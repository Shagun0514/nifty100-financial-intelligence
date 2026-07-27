# Performance Notes — Sprint 6, Day 43

## Load Test: 10 concurrent GET /api/v1/screener requests

- All requests completed: 5.36s total (target: < 10s) — PASS
- All responses HTTP 200: yes
- Slowest individual request: 5.361s
- Per-request results: [{'status': 200, 'elapsed_s': 5.187}, {'status': 200, 'elapsed_s': 5.361}, {'status': 200, 'elapsed_s': 4.973}, {'status': 200, 'elapsed_s': 5.338}, {'status': 200, 'elapsed_s': 5.272}, {'status': 200, 'elapsed_s': 5.275}, {'status': 200, 'elapsed_s': 4.929}, {'status': 200, 'elapsed_s': 4.999}, {'status': 200, 'elapsed_s': 5.192}, {'status': 200, 'elapsed_s': 5.131}]

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
see `db/schema.sql`. This mainly benefits the `/companies/{ticker}/*` endpoints and
year-range filtered queries, not the screener (which does a full-table scan by design
since it filters on computed columns).
