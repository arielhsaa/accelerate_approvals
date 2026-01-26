# Databricks notebook source
# MAGIC %md
# MAGIC # Real-time Transaction Streaming
# MAGIC 
# MAGIC This notebook demonstrates real-time transaction processing using Spark Structured Streaming.
# MAGIC 
# MAGIC **Features:**
# MAGIC - Structured Streaming with Delta Lake
# MAGIC - Real-time fraud detection enrichment
# MAGIC - Smart checkout decisioning
# MAGIC - Streaming aggregations
# MAGIC - Watermarking for late data

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.streaming import StreamingQuery
import yaml
import sys
sys.path.append('../data_generation')

from transaction_generator import TransactionGenerator
from external_data_generator import ExternalDataGenerator

# Load configuration
with open("../config/app_config.yaml", "r") as f:
    config = yaml.safe_load(f)

BRONZE_PATH = config['storage']['paths']['bronze']
SILVER_PATH = config['storage']['paths']['silver']
CHECKPOINT_PATH = config['storage']['paths']['checkpoints']

print("Configuration loaded successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Simulated Streaming Source

# COMMAND ----------

# MAGIC %python
# MAGIC # Create a streaming transaction generator
# MAGIC import time
# MAGIC import pandas as pd
# MAGIC from datetime import datetime
# MAGIC 
# MAGIC txn_gen = TransactionGenerator(seed=int(time.time()))
# MAGIC ext_data_gen = ExternalDataGenerator(seed=int(time.time()))
# MAGIC 
# MAGIC # Get sample IDs
# MAGIC cardholder_ids = [row.cardholder_id for row in spark.read.format("delta").load(f"{BRONZE_PATH}/cardholders").select("cardholder_id").limit(1000).collect()]
# MAGIC merchant_ids = [row.merchant_id for row in spark.read.format("delta").load(f"{BRONZE_PATH}/merchants").select("merchant_id").limit(500).collect()]
# MAGIC 
# MAGIC print(f"Loaded {len(cardholder_ids)} cardholders and {len(merchant_ids)} merchants")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Streaming Query

# COMMAND ----------

# Read stream from transactions table (simulating continuous ingestion)
transactions_stream = (
    spark.readStream
    .format("delta")
    .option("ignoreChanges", "true")
    .option("maxFilesPerTrigger", 10)
    .load(f"{BRONZE_PATH}/transactions")
)

# Add processing time
transactions_enriched = transactions_stream.withColumn(
    "processing_timestamp", current_timestamp()
).withColumn(
    "watermark_time", col("timestamp")
)

print("Stream source configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-time Enrichment with External Data

# COMMAND ----------

# Load external reference data
cardholders_ref = spark.read.format("delta").load(f"{BRONZE_PATH}/cardholders")
merchants_ref = spark.read.format("delta").load(f"{BRONZE_PATH}/merchants")

# Enrich stream with cardholder data
enriched_stream = (
    transactions_enriched
    .join(
        cardholders_ref.select(
            "cardholder_id",
            "risk_segment",
            "risk_score",
            "historical_approval_rate",
            "threeds_enrolled",
            "digital_wallet_enrolled",
            "card_type"
        ),
        "cardholder_id",
        "left"
    )
    .join(
        merchants_ref.select(
            "merchant_id",
            "merchant_name",
            "mcc",
            "category",
            "merchant_size",
            col("risk_score").alias("merchant_risk_score"),
            col("approval_rate").alias("merchant_approval_rate"),
            "threeds_enabled",
            "network_token_enabled"
        ),
        "merchant_id",
        "left"
    )
)

print("Enrichment joins configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Smart Checkout Decision Logic

# COMMAND ----------

# Apply smart checkout decision logic
def determine_payment_solution(fraud_score, amount, requires_3ds, merchant_risk, cardholder_risk):
    """
    Determine optimal payment solution based on risk factors
    Returns: payment_solution_recommendation
    """
    solutions = []
    
    # 3DS for high-value or high-risk transactions
    if requires_3ds or amount > 500 or fraud_score > 50:
        solutions.append("3DS")
    
    # Antifraud for elevated fraud scores
    if fraud_score > 40:
        solutions.append("Antifraud")
    
    # IDPay for high-value transactions
    if amount > 1000:
        solutions.append("IDPay")
    
    # Network Token for better security
    if merchant_risk < 50 and cardholder_risk < 50:
        solutions.append("NetworkToken")
    
    # Passkey for low-risk, enrolled cardholders
    if cardholder_risk < 30 and fraud_score < 20:
        solutions.append("Passkey")
    
    # Default to DataShareOnly
    if not solutions:
        solutions.append("DataShareOnly")
    
    return ",".join(solutions)

# Register UDF
determine_payment_solution_udf = udf(determine_payment_solution, StringType())

# Apply smart routing
smart_routed_stream = enriched_stream.withColumn(
    "recommended_payment_solution",
    determine_payment_solution_udf(
        col("fraud_score"),
        col("amount"),
        col("requires_3ds"),
        col("merchant_risk_score"),
        col("risk_score")
    )
).withColumn(
    "approval_probability",
    when(col("is_approved"), 1.0).otherwise(0.0)
)

print("Smart checkout logic applied")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Aggregations - Real-time Metrics

# COMMAND ----------

# Approval rate by geography (5-minute windows)
approval_by_geo_stream = (
    smart_routed_stream
    .withWatermark("watermark_time", "10 minutes")
    .groupBy(
        window(col("watermark_time"), "5 minutes"),
        col("geography")
    )
    .agg(
        count("*").alias("total_transactions"),
        sum(when(col("is_approved"), 1).otherwise(0)).alias("approved_transactions"),
        avg("amount").alias("avg_amount"),
        avg("fraud_score").alias("avg_fraud_score"),
        avg("processing_time_ms").alias("avg_processing_time_ms")
    )
    .withColumn(
        "approval_rate",
        col("approved_transactions") / col("total_transactions")
    )
)

# Decline analysis by reason code
decline_analysis_stream = (
    smart_routed_stream
    .filter(col("is_approved") == False)
    .withWatermark("watermark_time", "10 minutes")
    .groupBy(
        window(col("watermark_time"), "5 minutes"),
        col("decline_reason_code"),
        col("decline_reason_description")
    )
    .agg(
        count("*").alias("decline_count"),
        avg("amount").alias("avg_declined_amount"),
        collect_set("geography").alias("affected_geographies")
    )
    .orderBy(col("decline_count").desc())
)

print("Streaming aggregations configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Streams to Delta Lake

# COMMAND ----------

# Write enriched transactions to Silver layer
enriched_transactions_writer = (
    smart_routed_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/silver_transactions")
    .option("mergeSchema", "true")
    .trigger(processingTime="5 seconds")
    .start(f"{SILVER_PATH}/enriched_transactions")
)

print("✓ Enriched transactions stream started")

# COMMAND ----------

# Write approval metrics
approval_metrics_writer = (
    approval_by_geo_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/approval_metrics")
    .trigger(processingTime="5 seconds")
    .start(f"{SILVER_PATH}/approval_metrics")
)

print("✓ Approval metrics stream started")

# COMMAND ----------

# Write decline analysis
decline_analysis_writer = (
    decline_analysis_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/decline_analysis")
    .trigger(processingTime="5 seconds")
    .start(f"{SILVER_PATH}/decline_analysis")
)

print("✓ Decline analysis stream started")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-time Monitoring

# COMMAND ----------

# Display real-time approval rates
display(
    smart_routed_stream
    .groupBy(
        window(col("watermark_time"), "1 minute"),
        col("geography")
    )
    .agg(
        count("*").alias("transactions"),
        (sum(when(col("is_approved"), 1).otherwise(0)) / count("*")).alias("approval_rate")
    )
    .select(
        col("window.start").alias("window_start"),
        col("geography"),
        col("transactions"),
        col("approval_rate")
    )
    .orderBy("window_start", "geography")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Query Status

# COMMAND ----------

# Check active streams
active_streams = spark.streams.active

print(f"Active Streams: {len(active_streams)}")
for stream in active_streams:
    print(f"  - {stream.name}: {stream.status}")
    print(f"    Progress: {stream.lastProgress}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stop Streams (when needed)

# COMMAND ----------

# Uncomment to stop streams
# for stream in spark.streams.active:
#     stream.stop()
# print("All streams stopped")
