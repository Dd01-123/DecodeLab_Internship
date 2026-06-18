-- name: delivered_orders
SELECT
    COUNT(*) AS delivered_orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS percentage
FROM ecommerce_orders
WHERE OrderStatus = 'Delivered';

-- name: pending_orders
SELECT
    COUNT(*) AS pending_orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS percentage
FROM ecommerce_orders
WHERE OrderStatus = 'Pending';

-- name: cancelled_orders
SELECT
    COUNT(*) AS cancelled_orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS percentage
FROM ecommerce_orders
WHERE OrderStatus = 'Cancelled';

-- name: returned_orders
SELECT
    COUNT(*) AS returned_orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS percentage
FROM ecommerce_orders
WHERE OrderStatus = 'Returned';

-- name: order_status_distribution
SELECT
    OrderStatus,
    COUNT(*) AS orders,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS percentage
FROM ecommerce_orders
GROUP BY OrderStatus
ORDER BY orders DESC;
