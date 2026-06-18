-- name: best_selling_products
SELECT Product, SUM(Quantity) AS units_sold, COUNT(DISTINCT OrderID) AS orders
FROM ecommerce_orders
GROUP BY Product
ORDER BY units_sold DESC
LIMIT 10;

-- name: lowest_selling_products
SELECT Product, SUM(Quantity) AS units_sold, COUNT(DISTINCT OrderID) AS orders
FROM ecommerce_orders
GROUP BY Product
ORDER BY units_sold ASC
LIMIT 10;

-- name: highest_revenue_products
SELECT Product, ROUND(SUM(TotalPrice), 2) AS revenue, SUM(Quantity) AS units_sold
FROM ecommerce_orders
GROUP BY Product
ORDER BY revenue DESC
LIMIT 10;

-- name: lowest_revenue_products
SELECT Product, ROUND(SUM(TotalPrice), 2) AS revenue, SUM(Quantity) AS units_sold
FROM ecommerce_orders
GROUP BY Product
ORDER BY revenue ASC
LIMIT 10;

-- name: product_ranking
SELECT
    Product,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(TotalPrice), 2) AS revenue,
    RANK() OVER (ORDER BY SUM(TotalPrice) DESC) AS revenue_rank,
    RANK() OVER (ORDER BY SUM(Quantity) DESC) AS volume_rank
FROM ecommerce_orders
GROUP BY Product
ORDER BY revenue_rank, volume_rank;

-- name: high_volume_low_revenue_products
WITH product_metrics AS (
    SELECT Product, SUM(Quantity) AS units_sold, SUM(TotalPrice) AS revenue
    FROM ecommerce_orders
    GROUP BY Product
)
SELECT Product, units_sold, ROUND(revenue, 2) AS revenue
FROM product_metrics
WHERE units_sold >= (SELECT AVG(units_sold) FROM product_metrics)
  AND revenue < (SELECT AVG(revenue) FROM product_metrics)
ORDER BY units_sold DESC, revenue ASC;

-- name: high_revenue_low_volume_products
WITH product_metrics AS (
    SELECT Product, SUM(Quantity) AS units_sold, SUM(TotalPrice) AS revenue
    FROM ecommerce_orders
    GROUP BY Product
)
SELECT Product, units_sold, ROUND(revenue, 2) AS revenue
FROM product_metrics
WHERE revenue >= (SELECT AVG(revenue) FROM product_metrics)
  AND units_sold < (SELECT AVG(units_sold) FROM product_metrics)
ORDER BY revenue DESC, units_sold ASC;
