# Databricks notebook source
# MAGIC %md
# MAGIC # Data Ingestion - Bronze Layer
# MAGIC 
# MAGIC This notebook ingests raw transaction, cardholder, merchant, and external data into Delta Lake Bronze layer.
# MAGIC 
# MAGIC **Architecture:**
# MAGIC - **Source**: Synthetic data generators
# MAGIC - **Destination**: Delta Lake Bronze tables
# MAGIC - **Pattern**: Medallion Architecture (Bronze layer)
# MAGIC - **Features**: Schema enforcement, data quality checks, audit columns

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable
import yaml

# Load configuration
with open("../config/app_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Storage paths
BRONZE_PATH = config['storage']['paths']['bronze']
CHECKPOINT_PATH = config['storage']['paths']['checkpoints']

print(f"Bronze Path: {BRONZE_PATH}")
print(f"Checkpoint Path: {CHECKPOINT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Schemas

# COMMAND ----------

# Transaction Schema
transaction_schema = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("cardholder_id", StringType(), False),
    StructField("merchant_id", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("amount", DecimalType(18, 2), False),
    StructField("currency", StringType(), False),
    StructField("card_network", StringType(), False),
    StructField("transaction_type", StringType(), False),
    StructField("geography", StringType(), False),
    StructField("merchant_country", StringType(), False),
    StructField("cardholder_country", StringType(), False),
    StructField("is_approved", BooleanType(), False),
    StructField("decline_reason_code", StringType(), True),
    StructField("decline_reason_description", StringType(), True),
    StructField("fraud_score", DecimalType(5, 2), False),
    StructField("requires_3ds", BooleanType(), False),
    StructField("threeds_authenticated", BooleanType(), False),
    StructField("payment_solutions_applied", StringType(), True),
    StructField("processing_time_ms", DecimalType(10, 2), False),
    StructField("hour_of_day", IntegerType(), False),
    StructField("day_of_week", IntegerType(), False),
    StructField("day_of_month", IntegerType(), False),
    StructField("is_weekend", BooleanType(), False),
    StructField("is_cross_border", BooleanType(), False),
    StructField("is_card_present", BooleanType(), False),
    StructField("merchant_initiated", BooleanType(), False),
    StructField("retry_attempt", IntegerType(), False),
    StructField("original_transaction_id", StringType(), True)
])

# Cardholder Schema
cardholder_schema = StructType([
    StructField("cardholder_id", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("gender", StringType(), True),
    StructField("age", IntegerType(), False),
    StructField("geography", StringType(), False),
    StructField("country", StringType(), False),
    StructField("city", StringType(), True),
    StructField("postal_code", StringType(), True),
    StructField("card_type", StringType(), False),
    StructField("risk_segment", StringType(), False),
    StructField("risk_score", DecimalType(5, 2), False),
    StructField("credit_limit", DecimalType(18, 2), False),
    StructField("account_age_months", IntegerType(), False),
    StructField("account_created", TimestampType(), False),
    StructField("card_expiry", TimestampType(), False),
    StructField("avg_monthly_transactions", IntegerType(), False),
    StructField("avg_transaction_amount", DecimalType(18, 2), False),
    StructField("historical_approval_rate", DecimalType(5, 4), False),
    StructField("historical_decline_count", IntegerType(), False),
    StructField("historical_fraud_incidents", IntegerType(), False),
    StructField("threeds_enrolled", BooleanType(), False),
    StructField("digital_wallet_enrolled", BooleanType(), False),
    StructField("wallet_types", StringType(), True),
    StructField("biometric_enabled", BooleanType(), False),
    StructField("is_active", BooleanType(), False),
    StructField("last_transaction_date", TimestampType(), True),
    StructField("kyc_verified", BooleanType(), False),
    StructField("email_verified", BooleanType(), False),
    StructField("phone_verified", BooleanType(), False),
    StructField("address_verified", BooleanType(), False),
    StructField("created_at", TimestampType(), False),
    StructField("updated_at", TimestampType(), False)
])

# Merchant Schema
merchant_schema = StructType([
    StructField("merchant_id", StringType(), False),
    StructField("merchant_name", StringType(), False),
    StructField("mcc", StringType(), False),
    StructField("category", StringType(), False),
    StructField("merchant_size", StringType(), False),
    StructField("geography", StringType(), False),
    StructField("country", StringType(), False),
    StructField("city", StringType(), True),
    StructField("postal_code", StringType(), True),
    StructField("business_age_months", IntegerType(), False),
    StructField("onboarded_date", TimestampType(), False),
    StructField("risk_score", IntegerType(), False),
    StructField("approval_rate", DecimalType(5, 4), False),
    StructField("avg_daily_transactions", IntegerType(), False),
    StructField("avg_monthly_volume", DecimalType(18, 2), False),
    StructField("avg_ticket_size", DecimalType(18, 2), False),
    StructField("chargeback_rate", DecimalType(5, 4), False),
    StructField("fraud_rate", DecimalType(5, 4), False),
    StructField("threeds_enabled", BooleanType(), False),
    StructField("network_token_enabled", BooleanType(), False),
    StructField("recurring_billing_enabled", BooleanType(), False),
    StructField("supports_credit", BooleanType(), False),
    StructField("supports_debit", BooleanType(), False),
    StructField("supports_digital_wallets", BooleanType(), False),
    StructField("supports_bnpl", BooleanType(), False),
    StructField("pci_compliant", BooleanType(), False),
    StructField("kyb_verified", BooleanType(), False),
    StructField("settlement_currency", StringType(), False),
    StructField("settlement_period_days", IntegerType(), False),
    StructField("is_active", BooleanType(), False),
    StructField("last_transaction_date", TimestampType(), True),
    StructField("total_lifetime_volume", DecimalType(18, 2), False),
    StructField("total_lifetime_transactions", LongType(), False),
    StructField("created_at", TimestampType(), False),
    StructField("updated_at", TimestampType(), False)
])

print("Schemas defined successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate and Ingest Master Data (One-time)

# COMMAND ----------

# MAGIC %python
# MAGIC # Generate cardholders
# MAGIC import sys
# MAGIC sys.path.append('../data_generation')
# MAGIC 
# MAGIC from cardholder_generator import CardholderGenerator
# MAGIC from merchant_generator import MerchantGenerator
# MAGIC 
# MAGIC # Generate cardholders
# MAGIC ch_generator = CardholderGenerator(seed=42)
# MAGIC cardholders_df = ch_generator.generate_batch(num_cardholders=100000)
# MAGIC 
# MAGIC # Convert to Spark DataFrame
# MAGIC cardholders_spark = spark.createDataFrame(cardholders_df)
# MAGIC 
# MAGIC # Write to Delta Lake
# MAGIC (cardholders_spark
# MAGIC  .write
# MAGIC  .format("delta")
# MAGIC  .mode("overwrite")
# MAGIC  .option("overwriteSchema", "true")
# MAGIC  .save(f"{BRONZE_PATH}/cardholders"))
# MAGIC 
# MAGIC print(f"✓ Ingested {cardholders_spark.count():,} cardholders")

# COMMAND ----------

# MAGIC %python
# MAGIC # Generate merchants
# MAGIC mer_generator = MerchantGenerator(seed=42)
# MAGIC merchants_df = mer_generator.generate_batch(num_merchants=5000)
# MAGIC 
# MAGIC # Convert to Spark DataFrame
# MAGIC merchants_spark = spark.createDataFrame(merchants_df)
# MAGIC 
# MAGIC # Write to Delta Lake
# MAGIC (merchants_spark
# MAGIC  .write
# MAGIC  .format("delta")
# MAGIC  .mode("overwrite")
# MAGIC  .option("overwriteSchema", "true")
# MAGIC  .save(f"{BRONZE_PATH}/merchants"))
# MAGIC 
# MAGIC print(f"✓ Ingested {merchants_spark.count():,} merchants")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Delta Tables with Data Quality Constraints

# COMMAND ----------

# Create Transactions table with constraints
spark.sql(f"""
CREATE TABLE IF NOT EXISTS bronze_transactions
USING DELTA
LOCATION '{BRONZE_PATH}/transactions'
""")

# Add constraints
spark.sql("""
ALTER TABLE bronze_transactions ADD CONSTRAINT valid_amount CHECK (amount > 0);
ALTER TABLE bronze_transactions ADD CONSTRAINT valid_fraud_score CHECK (fraud_score >= 0 AND fraud_score <= 100);
""")

# Create Cardholders table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS bronze_cardholders
USING DELTA
LOCATION '{BRONZE_PATH}/cardholders'
""")

# Create Merchants table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS bronze_merchants
USING DELTA
LOCATION '{BRONZE_PATH}/merchants'
""")

print("✓ Delta tables created with constraints")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup Streaming Ingestion for Transactions

# COMMAND ----------

# MAGIC %python
# MAGIC from transaction_generator import TransactionGenerator
# MAGIC import time
# MAGIC from pyspark.sql.streaming import StreamingQuery
# MAGIC 
# MAGIC # Initialize generator
# MAGIC txn_generator = TransactionGenerator(seed=42)
# MAGIC 
# MAGIC # Get cardholder and merchant IDs
# MAGIC cardholder_ids = [row.cardholder_id for row in spark.read.format("delta").load(f"{BRONZE_PATH}/cardholders").select("cardholder_id").limit(1000).collect()]
# MAGIC merchant_ids = [row.merchant_id for row in spark.read.format("delta").load(f"{BRONZE_PATH}/merchants").select("merchant_id").limit(500).collect()]
# MAGIC 
# MAGIC print(f"Using {len(cardholder_ids)} cardholders and {len(merchant_ids)} merchants for transaction generation")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Batch Load Historical Transactions

# COMMAND ----------

# MAGIC %python
# MAGIC # Generate 7 days of historical transactions
# MAGIC from datetime import datetime, timedelta
# MAGIC 
# MAGIC print("Generating historical transactions (7 days)...")
# MAGIC start_time = datetime.now() - timedelta(days=7)
# MAGIC 
# MAGIC historical_txns_df = txn_generator.generate_batch(
# MAGIC     num_transactions=500000,
# MAGIC     cardholder_ids=cardholder_ids,
# MAGIC     merchant_ids=merchant_ids,
# MAGIC     start_time=start_time,
# MAGIC     time_range_hours=168  # 7 days
# MAGIC )
# MAGIC 
# MAGIC # Convert to Spark DataFrame
# MAGIC historical_txns_spark = spark.createDataFrame(historical_txns_df)
# MAGIC 
# MAGIC # Write to Delta Lake
# MAGIC (historical_txns_spark
# MAGIC  .write
# MAGIC  .format("delta")
# MAGIC  .mode("append")
# MAGIC  .save(f"{BRONZE_PATH}/transactions"))
# MAGIC 
# MAGIC print(f"✓ Ingested {historical_txns_spark.count():,} historical transactions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Validation

# COMMAND ----------

# Validate data quality
transactions = spark.read.format("delta").load(f"{BRONZE_PATH}/transactions")
cardholders = spark.read.format("delta").load(f"{BRONZE_PATH}/cardholders")
merchants = spark.read.format("delta").load(f"{BRONZE_PATH}/merchants")

print("Data Quality Report:")
print("=" * 60)
print(f"Transactions: {transactions.count():,}")
print(f"Cardholders: {cardholders.count():,}")
print(f"Merchants: {merchants.count():,}")
print()

print("Transaction Statistics:")
print(f"  Approval Rate: {transactions.filter(col('is_approved') == True).count() / transactions.count():.2%}")
print(f"  Avg Transaction Amount: ${transactions.agg(avg('amount')).collect()[0][0]:.2f}")
print(f"  Date Range: {transactions.agg(min('timestamp'), max('timestamp')).collect()[0]}")
print()

print("Cardholder Statistics:")
print(f"  3DS Enrolled: {cardholders.filter(col('threeds_enrolled') == True).count() / cardholders.count():.2%}")
print(f"  Digital Wallet Enrolled: {cardholders.filter(col('digital_wallet_enrolled') == True).count() / cardholders.count():.2%}")
print()

print("Merchant Statistics:")
print(f"  PCI Compliant: {merchants.filter(col('pci_compliant') == True).count() / merchants.count():.2%}")
print(f"  3DS Enabled: {merchants.filter(col('threeds_enabled') == True).count() / merchants.count():.2%}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Delta Tables

# COMMAND ----------

# Optimize tables for better query performance
spark.sql("OPTIMIZE bronze_transactions ZORDER BY (timestamp, cardholder_id, merchant_id)")
spark.sql("OPTIMIZE bronze_cardholders ZORDER BY (cardholder_id)")
spark.sql("OPTIMIZE bronze_merchants ZORDER BY (merchant_id)")

print("✓ Delta tables optimized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enable Change Data Feed (for downstream processing)

# COMMAND ----------

spark.sql("ALTER TABLE bronze_transactions SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
spark.sql("ALTER TABLE bronze_cardholders SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
spark.sql("ALTER TABLE bronze_merchants SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

print("✓ Change Data Feed enabled")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Success!
# MAGIC 
# MAGIC Bronze layer ingestion complete. Data is now ready for Silver layer processing.
