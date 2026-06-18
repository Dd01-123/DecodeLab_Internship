-- name: most_used_payment_method
SELECT PaymentMethod, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY PaymentMethod
ORDER BY orders DESC
LIMIT 1;

-- name: least_used_payment_method
SELECT PaymentMethod, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY PaymentMethod
ORDER BY orders ASC
LIMIT 1;

-- name: revenue_by_payment_method
SELECT PaymentMethod, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY PaymentMethod
ORDER BY revenue DESC;

-- name: payment_method_distribution
SELECT
    PaymentMethod,
    COUNT(*) AS orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS percentage
FROM ecommerce_orders
GROUP BY PaymentMethod
ORDER BY orders DESC;
