-- name: top_referral_sources
SELECT ReferralSource, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY ReferralSource
ORDER BY orders DESC
LIMIT 10;

-- name: lowest_referral_sources
SELECT ReferralSource, COUNT(*) AS orders
FROM ecommerce_orders
GROUP BY ReferralSource
ORDER BY orders ASC
LIMIT 10;

-- name: revenue_by_referral_source
SELECT ReferralSource, ROUND(SUM(TotalPrice), 2) AS revenue
FROM ecommerce_orders
GROUP BY ReferralSource
ORDER BY revenue DESC;

-- name: referral_performance
SELECT
    ReferralSource,
    COUNT(*) AS orders,
    ROUND(SUM(TotalPrice), 2) AS revenue,
    ROUND(AVG(TotalPrice), 2) AS average_order_value,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecommerce_orders), 2) AS order_share_pct
FROM ecommerce_orders
GROUP BY ReferralSource
ORDER BY revenue DESC;
