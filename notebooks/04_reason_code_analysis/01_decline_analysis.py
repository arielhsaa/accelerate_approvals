# Databricks notebook source
# MAGIC %md
# MAGIC # Reason Code Performance Analysis
# MAGIC 
# MAGIC Transform transaction decline signals into actionable insights by analyzing
# MAGIC decline patterns and root causes in near real-time.
# MAGIC 
# MAGIC **Objectives:**
# MAGIC - Identify clear root causes behind transaction declines
# MAGIC - Translate reason codes into concrete actions
# MAGIC - Deliver insights in near real-time
# MAGIC - Track improvement opportunities

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load configuration
import yaml
with open("../config/app_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Reason code mappings
REASON_CODES = config['reason_codes']

print("✓ Setup complete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Decline Data

# COMMAND ----------

# Load silver transactions
transactions = spark.table("silver_transactions")

# Filter declined transactions
declines = transactions.filter(col("is_approved") == False)

print(f"Total transactions: {transactions.count():,}")
print(f"Declined transactions: {declines.count():,}")
print(f"Decline rate: {declines.count() / transactions.count():.2%}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reason Code Distribution Analysis

# COMMAND ----------

# Analyze reason code distribution
reason_code_dist = (declines
    .groupBy("decline_reason_code", "decline_reason_description")
    .agg(
        count("*").alias("decline_count"),
        avg("amount").alias("avg_amount"),
        avg("fraud_score").alias("avg_fraud_score"),
        avg("composite_risk_score").alias("avg_risk_score")
    )
    .orderBy(desc("decline_count"))
)

display(reason_code_dist)

# COMMAND ----------

# Visualize reason code distribution
reason_code_pdf = reason_code_dist.toPandas()

fig = px.bar(
    reason_code_pdf.head(10),
    x='decline_reason_description',
    y='decline_count',
    title='Top 10 Decline Reasons',
    labels={'decline_count': 'Number of Declines', 'decline_reason_description': 'Decline Reason'},
    color='avg_risk_score',
    color_continuous_scale='Reds'
)
fig.update_layout(xaxis_tickangle=-45, height=500)
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Decline Patterns by Dimension

# COMMAND ----------

# Analyze by geography
decline_by_geo = (declines
    .groupBy("geography", "decline_reason_code", "decline_reason_description")
    .agg(count("*").alias("decline_count"))
    .withColumn("total_declines_geo", sum("decline_count").over(Window.partitionBy("geography")))
    .withColumn("decline_pct", col("decline_count") / col("total_declines_geo"))
    .orderBy("geography", desc("decline_count"))
)

display(decline_by_geo)

# COMMAND ----------

# Analyze by merchant category
decline_by_category = (declines
    .groupBy("merchant_category", "decline_reason_code", "decline_reason_description")
    .agg(
        count("*").alias("decline_count"),
        avg("amount").alias("avg_amount")
    )
    .withColumn("total_declines_cat", sum("decline_count").over(Window.partitionBy("merchant_category")))
    .withColumn("decline_pct", col("decline_count") / col("total_declines_cat"))
    .filter(col("total_declines_cat") > 100)  # Filter categories with significant volume
    .orderBy(desc("decline_count"))
)

display(decline_by_category.limit(20))

# COMMAND ----------

# Analyze by time of day
decline_by_hour = (declines
    .groupBy("hour_of_day", "decline_reason_code", "decline_reason_description")
    .agg(count("*").alias("decline_count"))
    .orderBy("hour_of_day", desc("decline_count"))
)

# Pivot for heatmap
decline_heatmap = (decline_by_hour
    .groupBy("hour_of_day")
    .pivot("decline_reason_description")
    .agg(first("decline_count"))
    .fillna(0)
    .orderBy("hour_of_day")
)

display(decline_heatmap)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Root Cause Analysis

# COMMAND ----------

# Create root cause categories
def categorize_decline_reason(reason_code):
    """Categorize decline reasons into root cause groups"""
    categories = {
        "51": "INSUFFICIENT_FUNDS",
        "05": "ISSUER_POLICY",
        "12": "INVALID_TRANSACTION",
        "41": "FRAUD_LOST_CARD",
        "43": "FRAUD_STOLEN_CARD",
        "54": "EXPIRED_CARD",
        "55": "INCORRECT_PIN",
        "57": "ISSUER_RESTRICTION",
        "59": "FRAUD_SUSPECTED",
        "61": "LIMIT_EXCEEDED",
        "62": "CARD_RESTRICTED",
        "63": "SECURITY_VIOLATION",
        "65": "LIMIT_EXCEEDED"
    }
    return categories.get(reason_code, "OTHER")

categorize_udf = udf(categorize_decline_reason, StringType())

# Add root cause category
declines_with_category = declines.withColumn(
    "root_cause_category",
    categorize_udf(col("decline_reason_code"))
)

# Analyze by root cause
root_cause_analysis = (declines_with_category
    .groupBy("root_cause_category")
    .agg(
        count("*").alias("decline_count"),
        avg("amount").alias("avg_amount"),
        avg("fraud_score").alias("avg_fraud_score"),
        countDistinct("cardholder_id").alias("unique_cardholders"),
        countDistinct("merchant_id").alias("unique_merchants")
    )
    .orderBy(desc("decline_count"))
)

display(root_cause_analysis)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Actionable Insights Generation

# COMMAND ----------

# Generate actionable recommendations based on decline patterns
def generate_recommendations(decline_data):
    """Generate actionable recommendations from decline data"""
    recommendations = []
    
    # Analyze each root cause
    for row in decline_data.collect():
        category = row['root_cause_category']
        count = row['decline_count']
        avg_amount = row['avg_amount']
        fraud_score = row['avg_fraud_score']
        
        if category == "INSUFFICIENT_FUNDS":
            recommendations.append({
                "category": category,
                "priority": "HIGH",
                "action": "Implement Smart Retry with optimal timing (24-72 hours)",
                "expected_impact": "30-40% recovery rate",
                "affected_transactions": count
            })
        elif category == "FRAUD_SUSPECTED" or category.startswith("FRAUD_"):
            recommendations.append({
                "category": category,
                "priority": "CRITICAL",
                "action": "Review fraud detection thresholds; consider 3DS for high-risk transactions",
                "expected_impact": "Reduce false positives by 15-20%",
                "affected_transactions": count
            })
        elif category == "EXPIRED_CARD":
            recommendations.append({
                "category": category,
                "priority": "MEDIUM",
                "action": "Implement Account Updater service to refresh card details",
                "expected_impact": "70-80% recovery rate",
                "affected_transactions": count
            })
        elif category == "LIMIT_EXCEEDED":
            recommendations.append({
                "category": category,
                "priority": "MEDIUM",
                "action": "Offer split payment or alternative payment methods",
                "expected_impact": "25-35% recovery rate",
                "affected_transactions": count
            })
        elif category == "ISSUER_POLICY" or category == "ISSUER_RESTRICTION":
            recommendations.append({
                "category": category,
                "priority": "HIGH",
                "action": "Engage with issuer for policy clarification; implement smart routing to alternative acquirers",
                "expected_impact": "10-15% improvement",
                "affected_transactions": count
            })
    
    return recommendations

recommendations = generate_recommendations(root_cause_analysis)
recommendations_df = spark.createDataFrame(recommendations)

display(recommendations_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Decline Trend Analysis

# COMMAND ----------

# Analyze decline trends over time
decline_trends = (declines
    .withColumn("date", to_date("timestamp"))
    .groupBy("date", "root_cause_category")
    .agg(count("*").alias("decline_count"))
    .orderBy("date", "root_cause_category")
)

# Calculate daily decline rate
daily_stats = (transactions
    .withColumn("date", to_date("timestamp"))
    .groupBy("date")
    .agg(
        count("*").alias("total_transactions"),
        sum(when(col("is_approved") == False, 1).otherwise(0)).alias("declined_transactions")
    )
    .withColumn("decline_rate", col("declined_transactions") / col("total_transactions"))
    .orderBy("date")
)

display(daily_stats)

# COMMAND ----------

# Visualize decline trends
daily_stats_pdf = daily_stats.toPandas()

fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Daily Transaction Volume', 'Daily Decline Rate'),
    vertical_spacing=0.15
)

fig.add_trace(
    go.Scatter(x=daily_stats_pdf['date'], y=daily_stats_pdf['total_transactions'],
               mode='lines+markers', name='Total Transactions'),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=daily_stats_pdf['date'], y=daily_stats_pdf['decline_rate'],
               mode='lines+markers', name='Decline Rate', line=dict(color='red')),
    row=2, col=1
)

fig.update_xaxes(title_text="Date", row=2, col=1)
fig.update_yaxes(title_text="Transactions", row=1, col=1)
fig.update_yaxes(title_text="Decline Rate", row=2, col=1)
fig.update_layout(height=700, showlegend=True, title_text="Decline Trends Over Time")
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Issuer Performance Analysis

# COMMAND ----------

# Analyze performance by issuer (using cardholder country as proxy)
issuer_performance = (transactions
    .groupBy("cardholder_country", "card_network")
    .agg(
        count("*").alias("total_transactions"),
        sum(when(col("is_approved") == True, 1).otherwise(0)).alias("approved_transactions"),
        sum(when(col("is_approved") == False, 1).otherwise(0)).alias("declined_transactions"),
        avg("processing_time_ms").alias("avg_processing_time")
    )
    .withColumn("approval_rate", col("approved_transactions") / col("total_transactions"))
    .withColumn("decline_rate", col("declined_transactions") / col("total_transactions"))
    .filter(col("total_transactions") > 100)  # Filter for statistical significance
    .orderBy(desc("total_transactions"))
)

display(issuer_performance)

# COMMAND ----------

# Identify underperforming issuers
underperforming_issuers = (issuer_performance
    .filter(col("approval_rate") < 0.80)  # Below 80% approval rate
    .orderBy("approval_rate")
)

print(f"Underperforming issuers: {underperforming_issuers.count()}")
display(underperforming_issuers)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Correlation Analysis

# COMMAND ----------

# Analyze correlation between decline reasons and various factors
correlation_analysis = (declines
    .groupBy("decline_reason_code", "geography", "merchant_category")
    .agg(
        count("*").alias("decline_count"),
        avg("amount").alias("avg_amount"),
        avg("fraud_score").alias("avg_fraud_score"),
        avg("composite_risk_score").alias("avg_risk_score")
    )
    .filter(col("decline_count") > 10)
)

display(correlation_analysis)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-Time Decline Monitoring Dashboard

# COMMAND ----------

# Create aggregated metrics for dashboard
dashboard_metrics = {
    "total_declines_today": declines.filter(to_date("timestamp") == current_date()).count(),
    "decline_rate_today": declines.filter(to_date("timestamp") == current_date()).count() / 
                          transactions.filter(to_date("timestamp") == current_date()).count(),
    "top_decline_reason": reason_code_dist.first()["decline_reason_description"],
    "most_affected_geography": decline_by_geo.orderBy(desc("decline_count")).first()["geography"],
    "avg_declined_amount": declines.agg(avg("amount")).collect()[0][0]
}

print("Today's Decline Metrics:")
print("=" * 60)
for metric, value in dashboard_metrics.items():
    if isinstance(value, float):
        if "rate" in metric:
            print(f"{metric}: {value:.2%}")
        else:
            print(f"{metric}: ${value:,.2f}")
    else:
        print(f"{metric}: {value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Insights to Gold Layer

# COMMAND ----------

# Save reason code analysis
(reason_code_dist
    .write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("gold_reason_code_analysis"))

# Save recommendations
(recommendations_df
    .write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("gold_decline_recommendations"))

# Save issuer performance
(issuer_performance
    .write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("gold_issuer_performance"))

print("✓ Insights saved to Gold layer")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Success!
# MAGIC 
# MAGIC Reason Code Performance Analysis complete:
# MAGIC - ✓ Decline patterns identified
# MAGIC - ✓ Root causes categorized
# MAGIC - ✓ Actionable recommendations generated
# MAGIC - ✓ Real-time monitoring enabled
# MAGIC - ✓ Insights saved to Gold layer
