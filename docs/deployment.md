# Deployment Guide

This guide walks you through deploying the Payment Approval Acceleration demo to Azure Databricks.

## Prerequisites

- Azure Databricks workspace (Premium or Enterprise tier)
- Azure Storage Account or ADLS Gen2
- Databricks CLI installed and configured
- Python 3.9 or higher
- Git

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd accelerate_approvals
```

## Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Databricks Configuration
DATABRICKS_HOST=https://<workspace>.azuredatabricks.net
DATABRICKS_TOKEN=<your-personal-access-token>
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>

# Storage Configuration
STORAGE_ACCOUNT_NAME=<your-storage-account>
STORAGE_ACCOUNT_KEY=<your-storage-key>
STORAGE_CONTAINER=payment-approvals
```

## Step 3: Create Databricks Cluster

### Option A: Using Databricks CLI

```bash
databricks clusters create --json-file config/cluster_config.json
```

### Option B: Using Databricks UI

1. Navigate to **Compute** in Databricks workspace
2. Click **Create Cluster**
3. Configure with these settings:
   - **Cluster Name**: payment-approval-acceleration
   - **Cluster Mode**: Standard
   - **Databricks Runtime**: 14.3 LTS ML
   - **Worker Type**: Standard_DS3_v2
   - **Workers**: 2-8 (auto-scaling)
   - **Driver Type**: Standard_DS3_v2

4. Add Spark configuration:
   ```
   spark.databricks.delta.preview.enabled true
   spark.databricks.delta.schema.autoMerge.enabled true
   spark.databricks.delta.optimizeWrite.enabled true
   spark.databricks.delta.autoCompact.enabled true
   ```

5. Click **Create Cluster**

## Step 4: Setup Storage

### Create Storage Container

```bash
# Using Azure CLI
az storage container create \
  --name payment-approvals \
  --account-name <your-storage-account>
```

### Mount Storage in Databricks

Run this in a Databricks notebook:

```python
storage_account_name = "<your-storage-account>"
storage_account_key = "<your-storage-key>"
container_name = "payment-approvals"
mount_point = "/mnt/payment_data"

# Check if already mounted
if not any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
    dbutils.fs.mount(
        source = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net",
        mount_point = mount_point,
        extra_configs = {
            f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net": storage_account_key
        }
    )
    print(f"✓ Mounted {mount_point}")
else:
    print(f"✓ {mount_point} already mounted")
```

## Step 5: Install Dependencies

### On Cluster

1. Navigate to your cluster in Databricks UI
2. Click **Libraries** tab
3. Click **Install New**
4. Select **PyPI** and install:
   - `faker==22.0.0`
   - `mimesis==11.1.0`
   - `xgboost==2.0.0`
   - `lightgbm==4.1.0`
   - `plotly==5.18.0`

### For Local Development

```bash
pip install -r requirements.txt
```

## Step 6: Upload Notebooks

### Using Databricks CLI

```bash
# Upload all notebooks
databricks workspace import_dir \
  notebooks \
  /Shared/payment_approval_optimization \
  --overwrite
```

### Using Databricks UI

1. Navigate to **Workspace**
2. Create folder: `/Shared/payment_approval_optimization`
3. Upload notebooks from `notebooks/` directory

## Step 7: Upload Data Generators

```bash
# Upload Python files to DBFS
databricks fs cp data_generation/transaction_generator.py \
  dbfs:/FileStore/payment_approvals/generators/

databricks fs cp data_generation/cardholder_generator.py \
  dbfs:/FileStore/payment_approvals/generators/

databricks fs cp data_generation/merchant_generator.py \
  dbfs:/FileStore/payment_approvals/generators/

databricks fs cp data_generation/external_data_generator.py \
  dbfs:/FileStore/payment_approvals/generators/
```

## Step 8: Run Data Ingestion

### Execute Bronze Layer Ingestion

1. Open notebook: `01_data_ingestion/01_bronze_ingestion`
2. Attach to your cluster
3. Run all cells
4. Verify data is loaded:
   - 100,000 cardholders
   - 5,000 merchants
   - 500,000+ transactions

### Start Streaming Pipeline

1. Open notebook: `01_data_ingestion/02_streaming_pipeline`
2. Attach to your cluster
3. Run all cells
4. Verify streaming queries are active

## Step 9: Train ML Models

1. Open notebook: `03_smart_checkout/01_ml_model_training`
2. Attach to your cluster
3. Run all cells
4. Verify models are registered in MLflow:
   - payment_approval_predictor
   - smart_routing_optimizer
   - composite_risk_scorer

## Step 10: Create SQL Endpoints

### Create SQL Warehouse

1. Navigate to **SQL Warehouses**
2. Click **Create SQL Warehouse**
3. Configure:
   - **Name**: payment-approvals-warehouse
   - **Cluster Size**: Medium
   - **Auto Stop**: 10 minutes
4. Click **Create**

### Import SQL Dashboards

1. Navigate to **SQL** > **Dashboards**
2. Click **Create Dashboard**
3. Import queries from `sql/dashboards/`:
   - `approval_rate_dashboard.sql`
   - `decline_analysis_dashboard.sql`
   - `smart_retry_dashboard.sql`

## Step 11: Deploy Databricks App

### Using Databricks Apps (Preview)

1. Navigate to **Apps** in Databricks workspace
2. Click **Create App**
3. Configure:
   - **Name**: Payment Approval Acceleration
   - **Source**: Upload `databricks_app/app.py`
   - **Requirements**: Upload `databricks_app/requirements.txt`
4. Click **Deploy**

### Alternative: Run Locally

```bash
cd databricks_app
pip install -r requirements.txt
streamlit run app.py
```

## Step 12: Deploy Databricks Agent

### Create Agent Endpoint

```python
from databricks import agents
from agents.approval_optimizer_agent.agent import ApprovalOptimizerAgent

# Initialize agent
agent = ApprovalOptimizerAgent()

# Deploy to Databricks Model Serving
agents.deploy(
    agent=agent,
    endpoint_name="approval-optimizer-agent",
    model_name="databricks-meta-llama-3-1-70b-instruct"
)
```

## Step 13: Setup Genie

1. Navigate to **Genie** in Databricks workspace
2. Click **Create Genie Space**
3. Configure:
   - **Name**: Payment Approvals Analysis
   - **Description**: Natural language queries for payment approval data
   - **Tables**: Select all silver and gold tables
4. Test with sample queries from `sql/genie_queries.md`

## Step 14: Configure Monitoring

### Enable Delta Lake Monitoring

```sql
-- Enable table monitoring
ALTER TABLE silver_transactions 
SET TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.logRetentionDuration' = '30 days'
);
```

### Setup Alerts

Create alerts in Databricks SQL for:
- Approval rate drops below 80%
- Decline rate spikes above 20%
- Processing latency exceeds 500ms
- Fraud score anomalies

## Step 15: Verify Deployment

Run the verification script:

```bash
python scripts/verify_deployment.py
```

This will check:
- ✓ Cluster is running
- ✓ Storage is mounted
- ✓ Tables are created
- ✓ Streaming queries are active
- ✓ ML models are registered
- ✓ Dashboards are accessible
- ✓ App is deployed

## Step 16: Load Sample Data (Optional)

To generate additional test data:

```python
# In a Databricks notebook
from transaction_generator import TransactionGenerator

generator = TransactionGenerator()
cardholder_ids = [f"CH{i:010d}" for i in range(1, 10001)]
merchant_ids = [f"MER{i:08d}" for i in range(1, 1001)]

# Generate 100K transactions
transactions = generator.generate_batch(
    num_transactions=100000,
    cardholder_ids=cardholder_ids,
    merchant_ids=merchant_ids
)

# Write to Delta
spark.createDataFrame(transactions).write.format("delta").mode("append").save("/mnt/payment_data/bronze/transactions")
```

## Troubleshooting

### Issue: Storage Mount Fails

**Solution**: Verify storage account key and container name. Ensure storage account allows access from Databricks.

### Issue: Streaming Query Fails

**Solution**: Check checkpoint location permissions. Ensure Delta tables exist.

### Issue: ML Model Training Fails

**Solution**: Verify cluster has ML runtime. Check data availability in silver tables.

### Issue: Dashboard Shows No Data

**Solution**: Verify SQL warehouse is running. Check table permissions.

### Issue: App Deployment Fails

**Solution**: Verify all dependencies in requirements.txt. Check app logs for errors.

## Next Steps

1. **Customize Configuration**: Edit `config/app_config.yaml` for your use case
2. **Tune ML Models**: Adjust hyperparameters in training notebooks
3. **Create Custom Dashboards**: Build dashboards specific to your KPIs
4. **Integrate External Data**: Connect real fraud intelligence or AML data sources
5. **Setup CI/CD**: Automate deployment with Azure DevOps or GitHub Actions

## Support

For issues or questions:
- Check the [README.md](../README.md)
- Review notebook documentation
- Consult Databricks documentation

## Security Considerations

- **Never commit secrets**: Use Azure Key Vault or Databricks Secrets
- **Enable Unity Catalog**: For data governance and access control
- **Use Service Principals**: For production deployments
- **Enable audit logs**: Track all data access
- **Encrypt data**: Enable encryption at rest and in transit

## Production Readiness Checklist

- [ ] Enable Unity Catalog
- [ ] Setup proper IAM roles and permissions
- [ ] Configure network security (VNet injection)
- [ ] Enable audit logging
- [ ] Setup monitoring and alerting
- [ ] Configure backup and disaster recovery
- [ ] Implement CI/CD pipeline
- [ ] Load test the system
- [ ] Document runbooks for operations
- [ ] Train operations team

## Cost Optimization

- Use auto-scaling clusters
- Enable auto-stop for SQL warehouses
- Use spot instances for non-critical workloads
- Optimize Delta table partitioning
- Archive old data to cheaper storage tiers
- Monitor and optimize query performance
