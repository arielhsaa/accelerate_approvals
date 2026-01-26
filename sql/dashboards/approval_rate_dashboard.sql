-- Approval Rate Dashboard
-- Real-time monitoring of approval rates across multiple dimensions

-- Overall Approval Metrics (Last 24 Hours)
SELECT 
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(amount), 2) as avg_transaction_amount,
  ROUND(AVG(processing_time_ms), 2) as avg_processing_time_ms,
  ROUND(AVG(fraud_score), 2) as avg_fraud_score
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS;

-- Approval Rate Trend (Last 7 Days, Hourly)
SELECT 
  DATE_TRUNC('hour', timestamp) as hour,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour;

-- Approval Rate by Geography
SELECT 
  geography,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount,
  ROUND(AVG(composite_risk_score), 2) as avg_risk_score
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY geography
ORDER BY total_transactions DESC;

-- Approval Rate by Payment Solution
SELECT 
  solution,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount
FROM (
  SELECT 
    t.*,
    EXPLODE(SPLIT(recommended_solutions, ',')) as solution
  FROM silver_transactions t
  WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
)
GROUP BY solution
ORDER BY approval_rate_pct DESC;

-- Approval Rate by Merchant Category
SELECT 
  merchant_category,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount,
  COUNT(DISTINCT merchant_id) as unique_merchants
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY merchant_category
HAVING COUNT(*) > 100
ORDER BY total_transactions DESC
LIMIT 20;

-- Approval Rate by Card Network
SELECT 
  card_network,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(processing_time_ms), 2) as avg_processing_time_ms
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY card_network
ORDER BY total_transactions DESC;

-- Approval Rate by Transaction Type
SELECT 
  transaction_type,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY transaction_type
ORDER BY total_transactions DESC;

-- Approval Rate by Time of Day
SELECT 
  hour_of_day,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- High-Risk Transactions (Approved Despite High Risk Score)
SELECT 
  transaction_id,
  timestamp,
  amount,
  geography,
  composite_risk_score,
  fraud_score,
  recommended_solutions,
  is_approved
FROM silver_transactions
WHERE composite_risk_score > 70
  AND is_approved = TRUE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY composite_risk_score DESC
LIMIT 100;

-- Low-Risk Transactions (Declined Despite Low Risk Score)
SELECT 
  transaction_id,
  timestamp,
  amount,
  geography,
  composite_risk_score,
  decline_reason_code,
  decline_reason_description,
  recommended_solutions
FROM silver_transactions
WHERE composite_risk_score < 30
  AND is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY composite_risk_score ASC
LIMIT 100;

-- Approval Rate Comparison: With vs Without 3DS
SELECT 
  CASE WHEN requires_3ds THEN 'With 3DS' ELSE 'Without 3DS' END as auth_type,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(amount), 2) as avg_amount
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY CASE WHEN requires_3ds THEN 'With 3DS' ELSE 'Without 3DS' END;

-- Cross-Border vs Domestic Transactions
SELECT 
  CASE WHEN is_cross_border THEN 'Cross-Border' ELSE 'Domestic' END as transaction_location,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as approved_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(fraud_score), 2) as avg_fraud_score
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY CASE WHEN is_cross_border THEN 'Cross-Border' ELSE 'Domestic' END;
