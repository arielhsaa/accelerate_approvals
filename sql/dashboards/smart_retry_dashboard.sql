-- Smart Retry Dashboard
-- Monitor and optimize retry performance

-- Overall Retry Metrics
SELECT 
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as retry_success_rate_pct,
  ROUND(AVG(amount), 2) as avg_retry_amount,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS;

-- Retry Success Rate by Decline Reason
SELECT 
  decline_reason_code,
  decline_reason_description,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY decline_reason_code, decline_reason_description
ORDER BY total_retries DESC;

-- Retry Success by Attempt Number
SELECT 
  retry_attempt,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY retry_attempt
ORDER BY retry_attempt;

-- Optimal Retry Timing Analysis
-- This query estimates time between original decline and retry
WITH retry_pairs AS (
  SELECT 
    r.transaction_id as retry_txn_id,
    r.original_transaction_id,
    r.timestamp as retry_timestamp,
    r.is_approved as retry_approved,
    r.amount,
    r.decline_reason_code,
    o.timestamp as original_timestamp,
    ROUND((UNIX_TIMESTAMP(r.timestamp) - UNIX_TIMESTAMP(o.timestamp)) / 3600, 1) as hours_between
  FROM silver_transactions r
  JOIN silver_transactions o ON r.original_transaction_id = o.transaction_id
  WHERE r.retry_attempt > 0
    AND r.timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
)
SELECT 
  CASE 
    WHEN hours_between < 6 THEN '0-6 hours'
    WHEN hours_between < 24 THEN '6-24 hours'
    WHEN hours_between < 48 THEN '24-48 hours'
    WHEN hours_between < 72 THEN '48-72 hours'
    ELSE '72+ hours'
  END as retry_delay_bucket,
  decline_reason_code,
  COUNT(*) as total_retries,
  SUM(CASE WHEN retry_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN retry_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct
FROM retry_pairs
GROUP BY 
  CASE 
    WHEN hours_between < 6 THEN '0-6 hours'
    WHEN hours_between < 24 THEN '6-24 hours'
    WHEN hours_between < 48 THEN '24-48 hours'
    WHEN hours_between < 72 THEN '48-72 hours'
    ELSE '72+ hours'
  END,
  decline_reason_code
HAVING COUNT(*) > 10
ORDER BY decline_reason_code, retry_delay_bucket;

-- Retry Performance by Geography
SELECT 
  geography,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY geography
ORDER BY total_retries DESC;

-- Daily Retry Performance Trend
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAYS
GROUP BY DATE(timestamp)
ORDER BY date;

-- Insufficient Funds Retry Analysis (Most Common Recoverable Decline)
SELECT 
  retry_attempt,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue
FROM silver_transactions
WHERE retry_attempt > 0
  AND decline_reason_code = '51'  -- Insufficient Funds
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY retry_attempt
ORDER BY retry_attempt;

-- Blocked Low-Probability Retries (Simulated)
-- Transactions that would have been retried but were blocked by smart retry logic
SELECT 
  decline_reason_code,
  decline_reason_description,
  COUNT(*) as blocked_retries,
  ROUND(AVG(predicted_approval_probability), 4) as avg_predicted_success_prob,
  ROUND(AVG(amount), 2) as avg_amount,
  COUNT(*) * 0.15 as estimated_cost_saved  -- Assuming $0.15 per retry attempt
FROM silver_transactions
WHERE is_approved = FALSE
  AND retry_attempt = 0
  AND predicted_approval_probability < 0.30  -- Below retry threshold
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY decline_reason_code, decline_reason_description
ORDER BY blocked_retries DESC;

-- Retry ROI Analysis
WITH retry_metrics AS (
  SELECT 
    COUNT(*) as total_retries,
    SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
    SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue,
    COUNT(*) * 0.15 as retry_costs  -- Assuming $0.15 per retry
  FROM silver_transactions
  WHERE retry_attempt > 0
    AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
)
SELECT 
  total_retries,
  successful_retries,
  ROUND(successful_retries * 100.0 / total_retries, 2) as success_rate_pct,
  ROUND(recovered_revenue, 2) as recovered_revenue,
  ROUND(retry_costs, 2) as retry_costs,
  ROUND(recovered_revenue - retry_costs, 2) as net_revenue,
  ROUND((recovered_revenue - retry_costs) / retry_costs * 100, 2) as roi_pct
FROM retry_metrics;

-- Cardholder Retry Patterns
SELECT 
  cardholder_id,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  SUM(amount) as total_retry_amount,
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_amount
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAYS
GROUP BY cardholder_id
HAVING COUNT(*) >= 3
ORDER BY total_retries DESC
LIMIT 100;

-- Merchant Retry Performance
SELECT 
  m.merchant_id,
  m.merchant_name,
  m.merchant_category,
  COUNT(*) as total_retries,
  SUM(CASE WHEN t.is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN t.is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
  SUM(CASE WHEN t.is_approved THEN t.amount ELSE 0 END) as recovered_revenue
FROM silver_transactions t
JOIN bronze_merchants m ON t.merchant_id = m.merchant_id
WHERE t.retry_attempt > 0
  AND t.timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY m.merchant_id, m.merchant_name, m.merchant_category
HAVING COUNT(*) > 20
ORDER BY recovered_revenue DESC
LIMIT 50;

-- Retry Recommendations Queue
-- Declined transactions that should be retried based on smart retry logic
SELECT 
  transaction_id,
  cardholder_id,
  merchant_id,
  amount,
  decline_reason_code,
  decline_reason_description,
  timestamp as declined_at,
  ROUND((UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600, 1) as hours_since_decline,
  predicted_approval_probability,
  CASE 
    WHEN decline_reason_code = '51' AND 
         (UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600 >= 24 
    THEN 'RETRY_NOW'
    WHEN decline_reason_code = '51' AND 
         (UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600 < 24 
    THEN CONCAT('RETRY_IN_', CAST(24 - (UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600 AS INT), '_HOURS')
    WHEN decline_reason_code IN ('61', '65') AND 
         (UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600 >= 24 
    THEN 'RETRY_NOW'
    WHEN decline_reason_code IN ('05', '57', '62') AND 
         (UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600 >= 6 
    THEN 'RETRY_NOW'
    ELSE 'WAIT'
  END as retry_recommendation
FROM silver_transactions
WHERE is_approved = FALSE
  AND retry_attempt = 0
  AND decline_reason_code NOT IN ('41', '43', '54', '59', '63')  -- Exclude non-retryable
  AND predicted_approval_probability >= 0.30
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
ORDER BY 
  CASE 
    WHEN decline_reason_code = '51' AND 
         (UNIX_TIMESTAMP(CURRENT_TIMESTAMP) - UNIX_TIMESTAMP(timestamp)) / 3600 >= 24 
    THEN 1
    ELSE 2
  END,
  predicted_approval_probability DESC
LIMIT 1000;
