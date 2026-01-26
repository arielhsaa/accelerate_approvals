# Deploy to Your Databricks Workspace

Quick guide to deploy to your existing workspace:
**https://adb-984752964297111.11.azuredatabricks.net**

---

## 🚀 Quick Deployment (5 Minutes)

### Step 1: Generate Access Token (2 minutes)

1. Go to your workspace: https://adb-984752964297111.11.azuredatabricks.net
2. Click **Settings** (gear icon) → **Developer**
3. Click **Access Tokens** → **Generate New Token**
4. Set:
   - **Comment**: Payment Approval Demo
   - **Lifetime**: 90 days
5. Click **Generate** and **copy the token**

### Step 2: Set Token (1 minute)

```bash
# In your terminal
export DATABRICKS_TOKEN="<paste-your-token-here>"
```

### Step 3: Run Deployment (2 minutes)

```bash
cd accelerate_approvals
chmod +x scripts/deploy-to-workspace.sh
./scripts/deploy-to-workspace.sh
```

**Done!** Your workspace is now configured.

---

## 📦 What Gets Deployed

The script will:
- ✅ Upload 6 notebooks to `/Shared/payment_approval_optimization/notebooks/`
- ✅ Upload 4 data generators to DBFS
- ✅ Create and configure a cluster
- ✅ Install required libraries (faker, xgboost, lightgbm, plotly)
- ✅ Generate configuration files

**Time**: 5-10 minutes (includes cluster creation)

---

## 📋 After Deployment

### 1. Initialize Data (5 minutes)

1. Open your workspace: https://adb-984752964297111.11.azuredatabricks.net
2. Navigate to: **Workspace** → **Shared** → **payment_approval_optimization** → **notebooks**
3. Open: `01_data_ingestion/01_bronze_ingestion`
4. Attach to cluster: **payment-approval-acceleration**
5. Click **Run All**

This generates:
- 100,000 cardholders
- 5,000 merchants
- 500,000+ transactions

### 2. Start Real-Time Streaming (2 minutes)

1. Open: `01_data_ingestion/02_streaming_pipeline`
2. Click **Run All**
3. Verify streaming queries are active

### 3. Train ML Models (3 minutes)

1. Open: `03_smart_checkout/01_ml_model_training`
2. Click **Run All**
3. Models are registered in MLflow

### 4. Create Dashboards

1. Go to **SQL** → **Dashboards**
2. Create new dashboard
3. Import queries from `sql/dashboards/`:
   - `approval_rate_dashboard.sql`
   - `decline_analysis_dashboard.sql`
   - `smart_retry_dashboard.sql`

### 5. Setup Genie (Natural Language Queries)

1. Go to **Genie**
2. Create new Genie Space:
   - **Name**: Payment Approvals Analysis
   - **Tables**: Select `silver_transactions`, `gold_*` tables
3. Test queries:
   - "What's our approval rate this week?"
   - "Show me top decline reasons"
   - "Which geography has highest decline rate?"

---

## 🔍 Verification

Check everything is working:

```bash
# In your terminal
databricks workspace ls /Shared/payment_approval_optimization/notebooks
databricks fs ls dbfs:/FileStore/payment_approvals/generators
databricks clusters list
```

Expected output:
```
✓ Notebooks in workspace
✓ Generators in DBFS
✓ Cluster running
```

---

## 📊 Workspace Structure

After deployment:

```
Your Workspace
└── Shared
    └── payment_approval_optimization
        ├── notebooks
        │   ├── 01_data_ingestion
        │   │   ├── 01_bronze_ingestion
        │   │   └── 02_streaming_pipeline
        │   ├── 03_smart_checkout
        │   │   └── 01_ml_model_training
        │   ├── 04_reason_code_analysis
        │   │   └── 01_decline_analysis
        │   └── 05_smart_retry
        │       └── 01_retry_predictor
        └── data_generation
            ├── transaction_generator.py
            ├── cardholder_generator.py
            ├── merchant_generator.py
            └── external_data_generator.py
```

---

## 🎯 Demo Flow

Once deployed, follow this sequence:

1. **Data Ingestion** (5 min)
   - Run `01_bronze_ingestion` notebook
   - Generates master data

2. **Streaming** (2 min)
   - Run `02_streaming_pipeline` notebook
   - Real-time processing starts

3. **ML Training** (3 min)
   - Run `01_ml_model_training` notebook
   - 3 models trained (92% AUC)

4. **Analytics** (5 min)
   - Run decline analysis notebook
   - Run smart retry notebook
   - View insights

5. **Dashboards** (5 min)
   - Create SQL dashboards
   - Test Genie queries
   - View real-time metrics

6. **Demo** (30 min)
   - Follow `docs/demo_guide.md`
   - Show business impact
   - Present ROI ($9.6M annual)

---

## ⚡ Quick Commands

```bash
# List clusters
databricks clusters list

# Start cluster
databricks clusters start --cluster-id <cluster-id>

# List notebooks
databricks workspace ls /Shared/payment_approval_optimization

# Check DBFS files
databricks fs ls dbfs:/FileStore/payment_approvals

# Run notebook (example)
databricks jobs create --json '{
  "name": "Generate Data",
  "tasks": [{
    "task_key": "generate",
    "notebook_task": {
      "notebook_path": "/Shared/payment_approval_optimization/notebooks/01_data_ingestion/01_bronze_ingestion"
    },
    "existing_cluster_id": "<cluster-id>"
  }]
}'
```

---

## 🐛 Troubleshooting

### Issue: "Token authentication failed"
```bash
# Regenerate token in Databricks UI
# Update environment variable
export DATABRICKS_TOKEN="new-token-here"
```

### Issue: "Cluster creation failed"
- Check quota limits in Azure subscription
- Try different region or node type
- Contact Azure support for quota increase

### Issue: "Notebooks not visible"
- Refresh browser
- Check permissions on /Shared folder
- Re-run deployment script

### Issue: "Libraries not installing"
- Wait for cluster to be fully running
- Check cluster event log
- Manually install via UI if needed

### Issue: "Storage mount fails"
```python
# In notebook, check if already mounted
display(dbutils.fs.mounts())

# If mount exists but not working, unmount and remount
dbutils.fs.unmount("/mnt/payment_data")
```

---

## 💰 Cost Estimate

Running this demo on your workspace:

```
Cluster Configuration:
- Nodes: 2-8 (auto-scaling)
- Type: Standard_DS3_v2
- Runtime: 14.3 LTS ML

Estimated Costs (per hour):
- DBU Cost: ~$0.55/DBU × 2 × 8 nodes = $8.80/hr
- VM Cost: ~$0.192/hr × 8 nodes = $1.54/hr
- Total: ~$10.34/hr

Daily (8 hours): ~$82.72
Monthly (8h/day, 22 days): ~$1,820

With auto-termination (30 min idle):
Monthly: ~$600-900 (saves 50-60%)
```

### Cost Optimization Tips
1. Enable auto-termination (30 minutes)
2. Use auto-scaling (starts with 2 workers)
3. Stop cluster when not demoing
4. Use spot instances for dev/test

---

## 🎓 Next Steps

After successful deployment:

1. **Learn the Platform**
   - Explore notebooks
   - Run SQL queries
   - Test Genie
   - View MLflow models

2. **Customize**
   - Adjust configurations in `config/app_config.yaml`
   - Modify ML model parameters
   - Create custom dashboards
   - Add your own data sources

3. **Present**
   - Follow `docs/demo_guide.md`
   - Show 30-minute demo
   - Calculate ROI for your use case
   - Present to stakeholders

4. **Production**
   - Enable Unity Catalog
   - Configure RBAC
   - Set up monitoring
   - Implement CI/CD

---

## 📞 Support

### Documentation
- [Demo Guide](../docs/demo_guide.md) - 30-minute presentation
- [Quick Start](../QUICKSTART.md) - 15-minute setup
- [Full README](../README.md) - Complete overview

### Commands
```bash
# Get cluster ID
databricks clusters list | grep payment-approval

# View notebook
databricks workspace export /Shared/payment_approval_optimization/notebooks/01_data_ingestion/01_bronze_ingestion

# Check logs
databricks clusters events --cluster-id <id>
```

---

## ✅ Success Checklist

You're ready when:
- ✅ Notebooks visible in workspace
- ✅ Cluster running
- ✅ Data generators in DBFS
- ✅ Data generated (100K+ records)
- ✅ ML models trained
- ✅ Streaming active
- ✅ Dashboards showing metrics

**Time to Value: 15 minutes!** ⚡

---

**Your workspace URL**: https://adb-984752964297111.11.azuredatabricks.net

**Ready to accelerate payment approvals!** 🚀💳
