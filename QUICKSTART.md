# Quick Start Guide

Get the Payment Approval Acceleration demo running in 15 minutes!

## Prerequisites

- Azure Databricks workspace
- Azure Storage Account
- 15 minutes of your time

## Step 1: Setup (2 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd accelerate_approvals

# Create environment file
cat > .env << EOF
DATABRICKS_HOST=https://<your-workspace>.azuredatabricks.net
DATABRICKS_TOKEN=<your-token>
STORAGE_ACCOUNT_NAME=<your-storage-account>
EOF
```

## Step 2: Deploy (3 minutes)

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

This will:
- Create workspace directories
- Upload notebooks
- Upload data generators
- Create and configure cluster
- Install required libraries

## Step 3: Generate Data (5 minutes)

1. Open Databricks workspace
2. Navigate to: `/Shared/payment_approval_optimization/notebooks/01_data_ingestion/01_bronze_ingestion`
3. Attach to cluster: `payment-approval-acceleration`
4. Run all cells

This generates:
- 100,000 cardholders
- 5,000 merchants
- 500,000 transactions

## Step 4: Start Streaming (2 minutes)

1. Open notebook: `01_data_ingestion/02_streaming_pipeline`
2. Run all cells
3. Verify streaming queries are active

## Step 5: Train Models (3 minutes)

1. Open notebook: `03_smart_checkout/01_ml_model_training`
2. Run all cells
3. Models are automatically registered in MLflow

## Step 6: Explore! (Ongoing)

### View Dashboards
1. Go to **SQL** > **Dashboards**
2. Import queries from `sql/dashboards/`
3. Create visualizations

### Try Genie
1. Go to **Genie**
2. Ask: "What's our approval rate this week?"
3. Explore with natural language queries

### Launch App
```bash
cd databricks_app
pip install -r requirements.txt
streamlit run app.py
```

### Chat with Agent
```bash
python agents/approval_optimizer_agent/agent.py
```

## Verify Everything Works

```bash
python scripts/verify_deployment.py
```

Should show all checks passing ✓

## Quick Demo Flow

1. **Show Architecture**: Explain medallion architecture
2. **Show Streaming**: Real-time transaction processing
3. **Show ML Models**: Approval predictor with 92% AUC
4. **Show Dashboards**: Approval rates and trends
5. **Show Smart Retry**: 37% success rate, $1.2M weekly recovery
6. **Show ROI**: $9.6M annual impact, 450% ROI

## Troubleshooting

### Cluster won't start
```bash
databricks clusters start --cluster-id <cluster-id>
```

### Storage mount fails
Check storage account key in `.env` file

### Notebooks not found
Re-run deployment script:
```bash
./scripts/deploy.sh
```

### No data in dashboards
Run data ingestion notebook first

## Next Steps

- **Customize**: Edit `config/app_config.yaml`
- **Extend**: Add your own ML models
- **Integrate**: Connect real data sources
- **Deploy**: Move to production

## Key Files

- `README.md` - Full documentation
- `docs/deployment.md` - Detailed deployment guide
- `docs/demo_guide.md` - Demo script
- `DEMO_SUMMARY.md` - Complete overview

## Support

- Check documentation in `docs/`
- Review notebook comments
- Consult Databricks docs

## Success Metrics

You're ready when you can:
- ✓ Process transactions in real-time
- ✓ See ML model predictions
- ✓ View approval rate dashboards
- ✓ Calculate business impact
- ✓ Demonstrate ROI

**Time to Value: 15 minutes** ⚡

---

**Need help?** Review the full [Deployment Guide](docs/deployment.md)
