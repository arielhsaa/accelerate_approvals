# Databricks notebook source
# MAGIC %md
# MAGIC # Real-Time Transaction Streaming Pipeline
# MAGIC 
# MAGIC This notebook implements a real-time streaming pipeline using Spark Structured Streaming
# MAGIC to process payment transactions with Smart Checkout decisioning.
# MAGIC 
# MAGIC **Features:**
# MAGIC - Real-time transaction ingestion
# MAGIC - Smart Checkout decisioning
# MAGIC - Fraud detection integration
# MAGIC - External data enrichment (Moody's)
# MAGIC - Delta Lake streaming writes
# MAGIC - Watermarking and late data handling

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.streaming import StreamingQuery
from delta.tables import DeltaTable
import yaml
import json

# Load configuration
with open("../config/app_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Storage paths
BRONZE_PATH = config['storage']['paths']['bronze']
SILVER_PATH = config['storage']['paths']['silver']
GOLD_PATH = config['storage']['paths']['gold']
CHECKPOINT_PATH = config['storage']['paths']['checkpoints']

print(f"Silver Path: {SILVER_PATH}")
print(f"Checkpoint Path: {CHECKPOINT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define UDFs for Smart Decisioning

# COMMAND ----------

from pyspark.sql.functions import udf
from pyspark.sql.types import StringType, ArrayType, DoubleType, StructType, StructField
import random

# Smart Checkout Decision UDF
@udf(returnType=ArrayType(StringType()))
def smart_checkout_decision(
    amount: float,
    fraud_score: float,
    cardholder_risk_score: float,
    merchant_risk_score: float,
    geography: str,
    is_cross_border: bool,
    threeds_enrolled: bool
) -> list:
    """
    Determine optimal payment solutions for a transaction
    
    Returns list of payment solutions to apply
    """
    solutions = []
    
    # 3DS decisioning
    if amount > 500 or fraud_score > 50 or is_cross_border:
        if threeds_enrolled:
            solutions.append("3DS")
    
    # Antifraud
    if fraud_score > 40 or merchant_risk_score > 60:
        solutions.append("Antifraud")
    
    # IDPay for high-value transactions
    if amount > 1000:
        solutions.append("IDPay")
    
    # Network Token for eligible transactions
    if cardholder_risk_score < 30 and merchant_risk_score < 40:
        solutions.append("NetworkToken")
    
    # Passkey for VIP customers
    if cardholder_risk_score < 20 and amount > 500:
        solutions.append("Passkey")
    
    # Default to DataShareOnly if no other solutions
    if len(solutions) == 0:
        solutions.append("DataShareOnly")
    
    return solutions

# Approval Prediction UDF
@udf(returnType=DoubleType())
def predict_approval_probability(
    amount: float,
    fraud_score: float,
    cardholder_approval_rate: float,
    merchant_approval_rate: float,
    payment_solutions: str,
    hour_of_day: int,
    is_weekend: bool
) -> float:
    """
    Predict probability of transaction approval
    
    This is a simplified rule-based model. In production, use MLflow model.
    """
    # Base probability from historical rates
    base_prob = (cardholder_approval_rate + merchant_approval_rate) / 2
    
    # Adjust for fraud score
    fraud_adjustment = -0.005 * fraud_score
    
    # Adjust for amount
    amount_adjustment = -0.05 if amount > 1000 else 0.0
    
    # Adjust for payment solutions
    solution_boost = 0.0
    if "3DS" in payment_solutions:
        solution_boost += 0.05
    if "NetworkToken" in payment_solutions:
        solution_boost += 0.15
    if "IDPay" in payment_solutions:
        solution_boost += 0.12
    if "Passkey" in payment_solutions:
        solution_boost += 0.20
    
    # Time-based adjustment
    time_adjustment = -0.05 if (hour_of_day < 6 or hour_of_day > 22) else 0.0
    weekend_adjustment = -0.02 if is_weekend else 0.0
    
    # Calculate final probability
    final_prob = base_prob + fraud_adjustment + amount_adjustment + solution_boost + time_adjustment + weekend_adjustment
    
    return max(0.0, min(1.0, final_prob))

# Risk Score Calculation UDF
@udf(returnType=DoubleType())
def calculate_composite_risk_score(
    fraud_score: float,
    cardholder_risk_score: float,
    merchant_risk_score: float,
    moodys_risk_score: float
) -> float:
    """
    Calculate composite risk score from multiple sources
    """
    # Weighted average
    weights = [0.40, 0.25, 0.20, 0.15]  # fraud, cardholder, merchant, moodys
    scores = [fraud_score, cardholder_risk_score, merchant_risk_score, moodys_risk_score]
    
    composite = sum(w * s for w, s in zip(weights, scores))
    return round(composite, 2)

print("✓ UDFs registered")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Streaming Transactions

# COMMAND ----------

# Read streaming transactions from Delta table
streaming_transactions = (spark
    .readStream
    .format("delta")
    .option("readChangeFeed", "true")
    .option("startingVersion", "latest")
    .table("bronze_transactions")
)

print("✓ Streaming source configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enrich with Cardholder Data

# COMMAND ----------

# Read cardholder dimension (static for now, can be streaming with CDC)
cardholders = spark.read.format("delta").load(f"{BRONZE_PATH}/cardholders")

# Select relevant cardholder features
cardholder_features = cardholders.select(
    col("cardholder_id"),
    col("risk_score").alias("cardholder_risk_score"),
    col("risk_segment"),
    col("historical_approval_rate").alias("cardholder_approval_rate"),
    col("threeds_enrolled"),
    col("digital_wallet_enrolled"),
    col("biometric_enabled"),
    col("account_age_months"),
    col("avg_transaction_amount").alias("cardholder_avg_amount")
)

# Join with streaming transactions
enriched_with_cardholder = (streaming_transactions
    .join(cardholder_features, "cardholder_id", "left")
)

print("✓ Cardholder enrichment configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enrich with Merchant Data

# COMMAND ----------

# Read merchant dimension
merchants = spark.read.format("delta").load(f"{BRONZE_PATH}/merchants")

# Select relevant merchant features
merchant_features = merchants.select(
    col("merchant_id"),
    col("merchant_name"),
    col("mcc"),
    col("category").alias("merchant_category"),
    col("risk_score").alias("merchant_risk_score"),
    col("approval_rate").alias("merchant_approval_rate"),
    col("fraud_rate").alias("merchant_fraud_rate"),
    col("threeds_enabled").alias("merchant_threeds_enabled"),
    col("network_token_enabled").alias("merchant_network_token_enabled")
)

# Join with enriched stream
enriched_with_merchant = (enriched_with_cardholder
    .join(merchant_features, "merchant_id", "left")
)

print("✓ Merchant enrichment configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate External Data (Moody's Risk Scores)

# COMMAND ----------

# Simulate Moody's risk score lookup
@udf(returnType=DoubleType())
def get_moodys_risk_score(cardholder_id: str, merchant_id: str, geography: str) -> float:
    """
    Simulate Moody's risk score API call
    In production, this would be an actual API call or cached lookup
    """
    import random
    import hashlib
    
    # Use hash for deterministic "random" scores
    seed = int(hashlib.md5(f"{cardholder_id}{merchant_id}".encode()).hexdigest(), 16) % 100
    random.seed(seed)
    
    base_score = random.uniform(10, 50)
    
    # Geography adjustment
    geo_adjustment = {
        "US": 0,
        "UK": 2,
        "EU": 1,
        "LATAM": 8,
        "APAC": 5
    }.get(geography, 5)
    
    return round(base_score + geo_adjustment, 2)

# Add Moody's risk score
enriched_with_external = (enriched_with_merchant
    .withColumn("moodys_risk_score", 
                get_moodys_risk_score(col("cardholder_id"), col("merchant_id"), col("geography")))
)

print("✓ External data enrichment configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Smart Checkout Decisioning

# COMMAND ----------

# Apply smart checkout logic
with_smart_checkout = (enriched_with_external
    .withColumn("recommended_solutions",
                smart_checkout_decision(
                    col("amount"),
                    col("fraud_score"),
                    col("cardholder_risk_score"),
                    col("merchant_risk_score"),
                    col("geography"),
                    col("is_cross_border"),
                    col("threeds_enrolled")
                ))
    .withColumn("composite_risk_score",
                calculate_composite_risk_score(
                    col("fraud_score"),
                    col("cardholder_risk_score"),
                    col("merchant_risk_score"),
                    col("moodys_risk_score")
                ))
    .withColumn("predicted_approval_probability",
                predict_approval_probability(
                    col("amount"),
                    col("fraud_score"),
                    col("cardholder_approval_rate"),
                    col("merchant_approval_rate"),
                    col("payment_solutions_applied"),
                    col("hour_of_day"),
                    col("is_weekend")
                ))
)

# Add processing metadata
final_stream = (with_smart_checkout
    .withColumn("processing_timestamp", current_timestamp())
    .withColumn("data_quality_score", lit(1.0))  # Placeholder for DQ checks
    .withColumn("model_version", lit("v1.0"))
)

print("✓ Smart checkout decisioning configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Silver Layer (Enriched Transactions)

# COMMAND ----------

# Define output schema for Silver layer
silver_transaction_query = (final_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/silver_transactions")
    .option("mergeSchema", "true")
    .trigger(processingTime="5 seconds")
    .toTable("silver_transactions")
)

print("✓ Silver layer streaming write started")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-Time Aggregations (Gold Layer)

# COMMAND ----------

# Aggregate approval rates by geography (5-minute windows)
approval_by_geography = (final_stream
    .withWatermark("timestamp", "10 minutes")
    .groupBy(
        window(col("timestamp"), "5 minutes"),
        col("geography")
    )
    .agg(
        count("*").alias("total_transactions"),
        sum(when(col("is_approved"), 1).otherwise(0)).alias("approved_transactions"),
        avg("amount").alias("avg_amount"),
        avg("fraud_score").alias("avg_fraud_score"),
        avg("predicted_approval_probability").alias("avg_predicted_approval_prob")
    )
    .withColumn("approval_rate", col("approved_transactions") / col("total_transactions"))
)

# Write to Gold layer
geography_query = (approval_by_geography
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/gold_approval_by_geography")
    .trigger(processingTime="10 seconds")
    .toTable("gold_approval_by_geography")
)

print("✓ Geography aggregation streaming started")

# COMMAND ----------

# Aggregate by payment solution
approval_by_solution = (final_stream
    .withWatermark("timestamp", "10 minutes")
    .withColumn("solution", explode(col("recommended_solutions")))
    .groupBy(
        window(col("timestamp"), "5 minutes"),
        col("solution")
    )
    .agg(
        count("*").alias("total_transactions"),
        sum(when(col("is_approved"), 1).otherwise(0)).alias("approved_transactions"),
        avg("amount").alias("avg_amount"),
        avg("composite_risk_score").alias("avg_risk_score")
    )
    .withColumn("approval_rate", col("approved_transactions") / col("total_transactions"))
)

# Write to Gold layer
solution_query = (approval_by_solution
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/gold_approval_by_solution")
    .trigger(processingTime="10 seconds")
    .toTable("gold_approval_by_solution")
)

print("✓ Payment solution aggregation streaming started")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Decline Reason Analysis Stream

# COMMAND ----------

# Analyze decline reasons in real-time
decline_analysis = (final_stream
    .filter(col("is_approved") == False)
    .withWatermark("timestamp", "10 minutes")
    .groupBy(
        window(col("timestamp"), "5 minutes"),
        col("decline_reason_code"),
        col("decline_reason_description"),
        col("geography")
    )
    .agg(
        count("*").alias("decline_count"),
        avg("amount").alias("avg_declined_amount"),
        avg("composite_risk_score").alias("avg_risk_score"),
        collect_set("recommended_solutions").alias("recommended_solutions_list")
    )
)

# Write decline analysis to Gold layer
decline_query = (decline_analysis
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/gold_decline_analysis")
    .trigger(processingTime="10 seconds")
    .toTable("gold_decline_analysis")
)

print("✓ Decline analysis streaming started")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitor Streaming Queries

# COMMAND ----------

# Display active streams
print("Active Streaming Queries:")
print("=" * 60)
for stream in spark.streams.active:
    print(f"Stream ID: {stream.id}")
    print(f"Name: {stream.name}")
    print(f"Status: {stream.status}")
    print("-" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Progress Monitoring

# COMMAND ----------

# Monitor query progress
def monitor_stream_progress(query: StreamingQuery, duration_seconds: int = 60):
    """Monitor streaming query progress"""
    import time
    
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        if query.lastProgress:
            progress = query.lastProgress
            print(f"Batch: {progress['batchId']}")
            print(f"Input Rows: {progress['numInputRows']}")
            print(f"Processing Rate: {progress['processedRowsPerSecond']:.2f} rows/sec")
            print(f"Latency: {progress.get('durationMs', {}).get('triggerExecution', 0)} ms")
            print("-" * 40)
        time.sleep(10)

# Example: Monitor silver transaction stream
# monitor_stream_progress(silver_transaction_query, duration_seconds=60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Success!
# MAGIC 
# MAGIC Real-time streaming pipeline is now processing transactions with:
# MAGIC - Smart Checkout decisioning
# MAGIC - Multi-source data enrichment
# MAGIC - Real-time aggregations
# MAGIC - Decline analysis
# MAGIC 
# MAGIC All data is being written to Delta Lake with ACID guarantees.
