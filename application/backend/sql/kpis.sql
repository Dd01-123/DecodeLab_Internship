-- name: total_orders
SELECT COUNT(DISTINCT OrderID) AS total_orders
FROM ecommerce_orders;

-- name: total_revenue
SELECT ROUND(SUM(TotalPrice), 2) AS total_revenue
FROM ecommerce_orders;

-- name: average_order_value
SELECT ROUND(AVG(TotalPrice), 2) AS average_order_value
FROM ecommerce_orders;

-- name: total_customers
SELECT COUNT(DISTINCT CustomerID) AS total_customers
FROM ecommerce_orders;

-- name: average_quantity_per_order
SELECT ROUND(AVG(Quantity), 2) AS average_quantity_per_order
FROM ecommerce_orders;

-- name: average_items_per_order
SELECT ROUND(AVG(ItemsInCart), 2) AS average_items_per_order
FROM ecommerce_orders;
