# Genie - Natural Language to SQL Queries

This document contains example natural language queries that can be used with Databricks Genie
to explore the payment approval acceleration data.

## Overview Queries

### "What is our current approval rate?"
```sql
SELECT 
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS;
```

### "Show me the trend of approval rates over the last 30 days"
```sql
SELECT 
  DATE(timestamp) as date,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAYS
GROUP BY DATE(timestamp)
ORDER BY date;
```

### "How many transactions did we process today?"
```sql
SELECT COUNT(*) as total_transactions
FROM silver_transactions
WHERE DATE(timestamp) = CURRENT_DATE;
```

## Decline Analysis Queries

### "What are the top reasons for transaction declines?"
```sql
SELECT 
  decline_reason_description,
  COUNT(*) as decline_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY decline_reason_description
ORDER BY decline_count DESC
LIMIT 10;
```

### "Show me declines due to insufficient funds"
```sql
SELECT 
  COUNT(*) as decline_count,
  ROUND(AVG(amount), 2) as avg_amount,
  SUM(amount) as total_declined_value
FROM silver_transactions
WHERE is_approved = FALSE
  AND decline_reason_code = '51'
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS;
```

### "Which geography has the highest decline rate?"
```sql
SELECT 
  geography,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_approved = FALSE THEN 1 ELSE 0 END) as declined_transactions,
  ROUND(SUM(CASE WHEN is_approved = FALSE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as decline_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY geography
ORDER BY decline_rate_pct DESC;
```

## Smart Checkout Queries

### "Which payment solution has the best approval rate?"
```sql
SELECT 
  solution,
  COUNT(*) as total_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM (
  SELECT 
    t.*,
    EXPLODE(SPLIT(recommended_solutions, ',')) as solution
  FROM silver_transactions t
  WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
)
GROUP BY solution
ORDER BY approval_rate_pct DESC;
```

### "Show me high-value transactions that were approved"
```sql
SELECT 
  transaction_id,
  amount,
  geography,
  recommended_solutions,
  composite_risk_score
FROM silver_transactions
WHERE is_approved = TRUE
  AND amount > 1000
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY amount DESC
LIMIT 100;
```

### "What's the approval rate for transactions using 3DS?"
```sql
SELECT 
  CASE WHEN requires_3ds THEN 'With 3DS' ELSE 'Without 3DS' END as auth_type,
  COUNT(*) as total_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY CASE WHEN requires_3ds THEN 'With 3DS' ELSE 'Without 3DS' END;
```

## Smart Retry Queries

### "What's our retry success rate?"
```sql
SELECT 
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS;
```

### "How much revenue have we recovered through retries?"
```sql
SELECT 
  SUM(CASE WHEN is_approved THEN amount ELSE 0 END) as recovered_revenue,
  COUNT(CASE WHEN is_approved THEN 1 END) as successful_retries
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS;
```

### "Which decline reasons have the best retry success rate?"
```sql
SELECT 
  decline_reason_description,
  COUNT(*) as total_retries,
  SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) as successful_retries,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct
FROM silver_transactions
WHERE retry_attempt > 0
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY decline_reason_description
HAVING COUNT(*) > 10
ORDER BY success_rate_pct DESC;
```

## Performance Analysis Queries

### "Show me the average transaction amount by merchant category"
```sql
SELECT 
  merchant_category,
  COUNT(*) as transaction_count,
  ROUND(AVG(amount), 2) as avg_amount,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY merchant_category
HAVING COUNT(*) > 100
ORDER BY transaction_count DESC
LIMIT 20;
```

### "What's the approval rate during peak hours?"
```sql
SELECT 
  hour_of_day,
  COUNT(*) as transaction_count,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY hour_of_day
ORDER BY transaction_count DESC
LIMIT 5;
```

### "Show me cross-border vs domestic transaction performance"
```sql
SELECT 
  CASE WHEN is_cross_border THEN 'Cross-Border' ELSE 'Domestic' END as transaction_type,
  COUNT(*) as total_transactions,
  ROUND(SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as approval_rate_pct,
  ROUND(AVG(fraud_score), 2) as avg_fraud_score
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY CASE WHEN is_cross_border THEN 'Cross-Border' ELSE 'Domestic' END;
```

## Risk Analysis Queries

### "Show me high-risk transactions that were approved"
```sql
SELECT 
  transaction_id,
  amount,
  composite_risk_score,
  fraud_score,
  recommended_solutions
FROM silver_transactions
WHERE is_approved = TRUE
  AND composite_risk_score > 70
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY composite_risk_score DESC
LIMIT 50;
```

### "What's the average risk score by geography?"
```sql
SELECT 
  geography,
  ROUND(AVG(composite_risk_score), 2) as avg_risk_score,
  ROUND(AVG(fraud_score), 2) as avg_fraud_score,
  COUNT(*) as transaction_count
FROM silver_transactions
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY geography
ORDER BY avg_risk_score DESC;
```

### "Show me transactions with low risk that were declined"
```sql
SELECT 
  transaction_id,
  amount,
  composite_risk_score,
  decline_reason_description,
  geography
FROM silver_transactions
WHERE is_approved = FALSE
  AND composite_risk_score < 30
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY composite_risk_score ASC
LIMIT 50;
```

## Business Impact Queries

### "Calculate the potential revenue from improving approval rates by 5%"
```sql
WITH current_metrics AS (
  SELECT 
    COUNT(*) as total_transactions,
    AVG(amount) as avg_amount,
    SUM(CASE WHEN is_approved THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as current_approval_rate
  FROM silver_transactions
  WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAYS
)
SELECT 
  total_transactions,
  ROUND(avg_amount, 2) as avg_transaction_amount,
  ROUND(current_approval_rate * 100, 2) as current_approval_rate_pct,
  ROUND((current_approval_rate + 0.05) * 100, 2) as improved_approval_rate_pct,
  ROUND(total_transactions * 0.05 * avg_amount, 2) as additional_monthly_revenue,
  ROUND(total_transactions * 0.05 * avg_amount * 12, 2) as additional_annual_revenue
FROM current_metrics;
```

### "What's the cost of declines by merchant category?"
```sql
SELECT 
  merchant_category,
  COUNT(*) as decline_count,
  SUM(amount) as total_declined_value,
  ROUND(AVG(amount), 2) as avg_declined_amount
FROM silver_transactions
WHERE is_approved = FALSE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS
GROUP BY merchant_category
ORDER BY total_declined_value DESC
LIMIT 20;
```

## Tips for Using Genie

1. **Be Specific**: Include time ranges and specific metrics in your questions
2. **Use Business Terms**: Genie understands terms like "approval rate", "decline", "revenue"
3. **Ask Follow-up Questions**: Build on previous queries for deeper analysis
4. **Compare Metrics**: Ask comparative questions like "compare approval rates between geographies"
5. **Request Visualizations**: Ask Genie to "show as a chart" or "visualize the trend"

## Example Genie Conversations

**User**: "What's our approval rate this week?"
**Genie**: Returns approval rate percentage with trend

**User**: "Show me the breakdown by geography"
**Genie**: Returns approval rates for each geography

**User**: "Which geography needs the most improvement?"
**Genie**: Identifies geography with lowest approval rate and suggests actions

**User**: "How much revenue could we recover?"
**Genie**: Calculates potential revenue from improving that geography's approval rate
