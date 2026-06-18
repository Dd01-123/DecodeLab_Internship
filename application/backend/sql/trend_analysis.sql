-- name: daily_orders
SELECT Date AS day, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY Date
ORDER BY Date;

-- name: weekly_orders
SELECT strftime('%Y-W%W', Date) AS week, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY week
ORDER BY week;

-- name: monthly_orders
SELECT strftime('%Y-%m', Date) AS month, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY month
ORDER BY month;

-- name: daily_revenue
SELECT Date AS day, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY Date
ORDER BY Date;

-- name: weekly_revenue
SELECT strftime('%Y-W%W', Date) AS week, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY week
ORDER BY week;

-- name: monthly_revenue
SELECT strftime('%Y-%m', Date) AS month, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY month
ORDER BY month;
