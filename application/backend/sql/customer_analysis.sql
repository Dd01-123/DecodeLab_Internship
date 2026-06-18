-- name: top_customers_by_revenue
SELECT CustomerID, ROUND(SUM(TotalPrice), 2) AS revenue, COUNT(DISTINCT OrderID) AS orders
FROM ecommerce_orders
GROUP BY CustomerID
ORDER BY revenue DESC
LIMIT 10;

-- name: top_customers_by_orders
SELECT CustomerID, COUNT(DISTINCT OrderID) AS orders, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY CustomerID
ORDER BY orders DESC, revenue DESC
LIMIT 10;

-- name: repeat_customers
SELECT CustomerID, COUNT(DISTINCT OrderID) AS orders, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY CustomerID
HAVING COUNT(DISTINCT OrderID) > 1
ORDER BY orders DESC, revenue DESC
LIMIT 20;

-- name: customer_purchase_frequency
SELECT orders_per_customer, COUNT(*) AS customer_count
FROM (
    SELECT CustomerID, COUNT(DISTINCT OrderID) AS orders_per_customer
    FROM ecommerce_orders
    GROUP BY CustomerID
)
GROUP BY orders_per_customer
ORDER BY orders_per_customer;

-- name: customer_contribution_percentage
SELECT
    CustomerID,
    ROUND(SUM(TotalPrice), 2) AS revenue,
    ROUND(SUM(TotalPrice) * 100.0 / (SELECT SUM(TotalPrice) FROM ecommerce_orders), 2) AS contribution_pct
FROM ecommerce_orders
GROUP BY CustomerID
ORDER BY contribution_pct DESC
LIMIT 20;
