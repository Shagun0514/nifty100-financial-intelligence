-- 1. Row counts per table (sanity check)
SELECT 'companies' t, COUNT(*) n FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'documents', COUNT(*) FROM documents;

-- 2. Companies with fewer than 5 years of P&L data (DQ-16)
SELECT c.company_name, COUNT(DISTINCT p.year) yrs
FROM companies c JOIN profitandloss p ON p.company_id=c.id
GROUP BY c.id HAVING yrs<5;

-- 3. Year coverage range per company
SELECT company_id, MIN(year) first_year, MAX(year) last_year, COUNT(*) n_years
FROM profitandloss GROUP BY company_id ORDER BY n_years;

-- 4. NULL counts per key P&L column
SELECT
  SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) null_sales,
  SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) null_net_profit,
  SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) null_eps
FROM profitandloss;

-- 5. Sector-wise average OPM% (needs sectors table loaded)
SELECT s.broad_sector, ROUND(AVG(p.opm_percentage),2) avg_opm
FROM profitandloss p
JOIN sectors s ON s.company_id=p.company_id
GROUP BY s.broad_sector ORDER BY avg_opm DESC;

-- 6. Balance sheet mismatches (DQ-04 support query)
SELECT company_id, year, total_assets, total_liabilities,
       ROUND(ABS(total_assets-total_liabilities)/NULLIF(total_assets,0)*100,2) pct_diff
FROM balancesheet
WHERE ABS(total_assets-total_liabilities)/NULLIF(total_assets,0) >= 0.01;

-- 7. Companies with negative net_profit in latest year
SELECT company_id, year, net_profit FROM profitandloss
WHERE year=(SELECT MAX(year) FROM profitandloss) AND net_profit<0;

-- 8. Top 10 by sales, latest year
SELECT c.company_name, p.year, p.sales
FROM profitandloss p JOIN companies c ON c.id=p.company_id
WHERE p.year=(SELECT MAX(year) FROM profitandloss)
ORDER BY p.sales DESC LIMIT 10;

-- 9. Documents coverage per company (annual report link count)
SELECT company_id, COUNT(*) n_reports FROM documents GROUP BY company_id ORDER BY n_reports;

-- 10. Peer groups and member counts
SELECT peer_group_name, COUNT(*) n_members FROM peer_groups GROUP BY peer_group_name;
