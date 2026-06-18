-- name: revenue_by_product
SELECT Product, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY Product
ORDER BY revenue DESC;

-- name: revenue_by_payment_method
SELECT PaymentMethod, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY PaymentMethod
ORDER BY revenue DESC;

-- name: revenue_by_referral_source
SELECT ReferralSource, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY ReferralSource
ORDER BY revenue DESC;

-- name: monthly_revenue
SELECT strftime('%Y-%m', Date) AS month, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY month
ORDER BY month;

-- name: daily_revenue
SELECT Date AS day, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY Date
ORDER BY Date;
