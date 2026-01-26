-- Decline Analysis Dashboard
-- Comprehensive analysis of transaction declines and actionable insights

-- Overall Decline Metrics
SELECT 
  COUNT(*) as total_declines,
  ROUND(AVG(amount), 2) as avg_declined_amount,
  ROUND(AVG(composite_risk_score), 2) as avg_risk_score,
  COUNT(DISTINCT cardholder_id) as unique_cardholders,
  COUNT(DISTINCT merchant_id) as unique_merchants,
  SUM(amount) as total_declined_value
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS;

-- Decline Reasons Distribution
SELECT 
  decline_reason_code,
  decline_reason_description,
  COUNT(*) as decline_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
  ROUND(AVG(amount), 2) as avg_amount,
  ROUND(AVG(fraud_score), 2) as avg_fraud_score,
  ROUND(AVG(composite_risk_score), 2) as avg_risk_score
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY decline_reason_code, decline_reason_description
ORDER BY decline_count DESC;

-- Decline Trend (Daily)
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as total_declines,
  COUNT(DISTINCT cardholder_id) as unique_cardholders,
  ROUND(AVG(amount), 2) as avg_declined_amount,
  SUM(amount) as total_declined_value
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAYS
GROUP BY DATE(timestamp)
ORDER BY date;

-- Declines by Geography and Reason
SELECT 
  geography,
  decline_reason_description,
  COUNT(*) as decline_count,
  ROUND(AVG(amount), 2) as avg_amount,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY geography), 2) as pct_of_geo_declines
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY geography, decline_reason_description
ORDER BY geography, decline_count DESC;

-- Declines by Merchant Category
SELECT 
  merchant_category,
  COUNT(*) as decline_count,
  ROUND(AVG(amount), 2) as avg_amount,
  COUNT(DISTINCT merchant_id) as unique_merchants,
  ROUND(AVG(merchant_risk_score), 2) as avg_merchant_risk_score
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY merchant_category
HAVING COUNT(*) > 50
ORDER BY decline_count DESC
LIMIT 20;

-- Declines by Time of Day
SELECT 
  hour_of_day,
  COUNT(*) as decline_count,
  ROUND(AVG(amount), 2) as avg_amount,
  ROUND(AVG(fraud_score), 2) as avg_fraud_score
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Decline Heatmap: Hour x Day of Week
SELECT 
  day_of_week,
  hour_of_day,
  COUNT(*) as decline_count
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY day_of_week, hour_of_day
ORDER BY day_of_week, hour_of_day;

-- Root Cause Analysis
SELECT 
  CASE 
    WHEN decline_reason_code = '51' THEN 'INSUFFICIENT_FUNDS'
    WHEN decline_reason_code IN ('41', '43', '59', '63') THEN 'FRAUD_RELATED'
    WHEN decline_reason_code = '54' THEN 'EXPIRED_CARD'
    WHEN decline_reason_code IN ('61', '65') THEN 'LIMIT_EXCEEDED'
    WHEN decline_reason_code IN ('05', '57', '62') THEN 'ISSUER_RESTRICTION'
    ELSE 'OTHER'
  END as root_cause_category,
  COUNT(*) as decline_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
  ROUND(AVG(amount), 2) as avg_amount,
  COUNT(DISTINCT cardholder_id) as unique_cardholders,
  COUNT(DISTINCT merchant_id) as unique_merchants,
  -- Estimate recoverability
  CASE 
    WHEN decline_reason_code = '51' THEN 0.65
    WHEN decline_reason_code IN ('41', '43', '59', '63') THEN 0.05
    WHEN decline_reason_code = '54' THEN 0.75
    WHEN decline_reason_code IN ('61', '65') THEN 0.55
    WHEN decline_reason_code IN ('05', '57', '62') THEN 0.35
    ELSE 0.25
  END as estimated_recovery_rate
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY 
  CASE 
    WHEN decline_reason_code = '51' THEN 'INSUFFICIENT_FUNDS'
    WHEN decline_reason_code IN ('41', '43', '59', '63') THEN 'FRAUD_RELATED'
    WHEN decline_reason_code = '54' THEN 'EXPIRED_CARD'
    WHEN decline_reason_code IN ('61', '65') THEN 'LIMIT_EXCEEDED'
    WHEN decline_reason_code IN ('05', '57', '62') THEN 'ISSUER_RESTRICTION'
    ELSE 'OTHER'
  END,
  CASE 
    WHEN decline_reason_code = '51' THEN 0.65
    WHEN decline_reason_code IN ('41', '43', '59', '63') THEN 0.05
    WHEN decline_reason_code = '54' THEN 0.75
    WHEN decline_reason_code IN ('61', '65') THEN 0.55
    WHEN decline_reason_code IN ('05', '57', '62') THEN 0.35
    ELSE 0.25
  END
ORDER BY decline_count DESC;

-- Issuer Performance Analysis
SELECT 
  cardholder_country as issuer_country,
  card_network,
  COUNT(*) as total_declines,
  ROUND(AVG(processing_time_ms), 2) as avg_processing_time_ms,
  COUNT(DISTINCT decline_reason_code) as unique_decline_reasons,
  ROUND(AVG(composite_risk_score), 2) as avg_risk_score
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY cardholder_country, card_network
HAVING COUNT(*) > 100
ORDER BY total_declines DESC
LIMIT 30;

-- Recoverable Declines Analysis
SELECT 
  decline_reason_code,
  decline_reason_description,
  COUNT(*) as decline_count,
  SUM(amount) as total_declined_value,
  CASE 
    WHEN decline_reason_code = '51' THEN 'HIGH'
    WHEN decline_reason_code = '54' THEN 'HIGH'
    WHEN decline_reason_code IN ('61', '65') THEN 'MEDIUM'
    WHEN decline_reason_code IN ('05', '57', '62') THEN 'MEDIUM'
    WHEN decline_reason_code IN ('41', '43', '59', '63') THEN 'LOW'
    ELSE 'MEDIUM'
  END as recoverability,
  CASE 
    WHEN decline_reason_code = '51' THEN 'Smart Retry (24-72h delay)'
    WHEN decline_reason_code = '54' THEN 'Account Updater Service'
    WHEN decline_reason_code IN ('61', '65') THEN 'Smart Retry (24h delay) or Split Payment'
    WHEN decline_reason_code IN ('05', '57', '62') THEN 'Smart Routing to Alternative Acquirer'
    WHEN decline_reason_code IN ('41', '43', '59', '63') THEN 'Do Not Retry - Fraud Related'
    ELSE 'Standard Retry (24h delay)'
  END as recommended_action
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY decline_reason_code, decline_reason_description
ORDER BY decline_count DESC;

-- Decline Rate by Risk Score Bands
SELECT 
  CASE 
    WHEN composite_risk_score < 20 THEN '0-20 (Very Low)'
    WHEN composite_risk_score < 40 THEN '20-40 (Low)'
    WHEN composite_risk_score < 60 THEN '40-60 (Medium)'
    WHEN composite_risk_score < 80 THEN '60-80 (High)'
    ELSE '80-100 (Very High)'
  END as risk_band,
  COUNT(*) as decline_count,
  ROUND(AVG(amount), 2) as avg_amount,
  COUNT(DISTINCT decline_reason_code) as unique_decline_reasons
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY 
  CASE 
    WHEN composite_risk_score < 20 THEN '0-20 (Very Low)'
    WHEN composite_risk_score < 40 THEN '20-40 (Low)'
    WHEN composite_risk_score < 60 THEN '40-60 (Medium)'
    WHEN composite_risk_score < 80 THEN '60-80 (High)'
    ELSE '80-100 (Very High)'
  END
ORDER BY 
  CASE 
    WHEN composite_risk_score < 20 THEN 1
    WHEN composite_risk_score < 40 THEN 2
    WHEN composite_risk_score < 60 THEN 3
    WHEN composite_risk_score < 80 THEN 4
    ELSE 5
  END;

-- Merchants with Highest Decline Rates
SELECT 
  m.merchant_id,
  m.merchant_name,
  m.merchant_category,
  m.geography,
  COUNT(*) as total_declines,
  ROUND(AVG(t.amount), 2) as avg_declined_amount,
  COUNT(DISTINCT t.decline_reason_code) as unique_decline_reasons,
  ROUND(AVG(t.composite_risk_score), 2) as avg_risk_score
FROM silver_transactions t
JOIN bronze_merchants m ON t.merchant_id = m.merchant_id
WHERE t.is_approved = FALSE
  AND t.timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY m.merchant_id, m.merchant_name, m.merchant_category, m.geography
HAVING COUNT(*) > 50
ORDER BY total_declines DESC
LIMIT 50;
