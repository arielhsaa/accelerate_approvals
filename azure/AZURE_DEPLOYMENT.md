# Azure Deployment Guide

Complete guide for deploying the Payment Approval Acceleration demo to Azure.

## 🎯 Overview

This guide will deploy:
- Azure Databricks Premium Workspace
- Azure Storage Account (for Delta Lake)
- Azure Key Vault (for secrets)
- All application code and notebooks

**Estimated Time**: 30 minutes  
**Estimated Cost**: $525-1555/month (varies by usage)

---

## 📋 Prerequisites

### Required Tools

1. **Azure CLI** (version 2.50+)
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Or on macOS
   brew install azure-cli
   
   # Verify installation
   az --version
   ```

2. **Azure Subscription**
   - Active Azure subscription with Contributor access
   - Sufficient quota for Databricks workspace

3. **Git**
   ```bash
   git --version
   ```

4. **Python 3.9+**
   ```bash
   python --version
   ```

### Azure Permissions Required

- Contributor role on the subscription or resource group
- Ability to create:
  - Resource Groups
  - Databricks Workspaces
  - Storage Accounts
  - Key Vaults

---

## 🚀 Deployment Options

### Option 1: Automated Deployment (Recommended)

#### Step 1: Clone Repository

```bash
git clone https://github.com/arielhsaa/accelerate_approvals.git
cd accelerate_approvals
```

#### Step 2: Login to Azure

```bash
az login

# Set your subscription (if you have multiple)
az account set --subscription "<subscription-id-or-name>"

# Verify you're in the right subscription
az account show
```

#### Step 3: Run Deployment Script

```bash
# Make script executable
chmod +x azure/deploy-azure.sh

# Run deployment (customize with environment variables)
RESOURCE_GROUP="payment-approvals-rg" \
LOCATION="eastus" \
WORKSPACE_NAME="payment-approvals-ws" \
./azure/deploy-azure.sh
```

**What this does:**
- ✅ Creates Resource Group
- ✅ Creates Storage Account with container
- ✅ Creates Key Vault
- ✅ Deploys Databricks Premium Workspace
- ✅ Generates .env configuration file

**Output:**
```
✓ Resource Group: payment-approvals-rg
✓ Databricks Workspace: payment-approvals-ws
✓ Storage Account: paymentapprovals12345
✓ Key Vault: payment-kv-12345

Databricks Workspace URL: https://adb-xxxx.azuredatabricks.net
```

#### Step 4: Generate Databricks Token

1. Go to your Databricks workspace URL (shown in output)
2. Click your profile icon → **Settings**
3. Go to **Developer** → **Access Tokens**
4. Click **Generate New Token**
   - Comment: "Deployment Token"
   - Lifetime: 90 days
5. Copy the token

#### Step 5: Update Configuration

```bash
# Edit .env file and add your token
nano .env

# Update this line:
DATABRICKS_TOKEN=<paste-your-token-here>
```

#### Step 6: Deploy Application Code

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure Databricks CLI
databricks configure --token

# Deploy notebooks and code
./scripts/deploy.sh
```

#### Step 7: Verify Deployment

```bash
python scripts/verify_deployment.py
```

Expected output:
```
✓ Environment variables
✓ Cluster running
✓ Workspace files uploaded
✓ DBFS files uploaded
✓ All checks passed!
```

---

### Option 2: ARM Template Deployment

#### Step 1: Deploy Infrastructure

```bash
# Deploy using ARM template
az deployment group create \
  --resource-group payment-approvals-rg \
  --template-file azure/templates/databricks-template.json \
  --parameters workspaceName=payment-approvals-ws

# Get outputs
az deployment group show \
  --resource-group payment-approvals-rg \
  --name databricks-template \
  --query properties.outputs
```

#### Step 2: Configure and Deploy Code

Follow Steps 4-7 from Option 1 above.

---

### Option 3: Azure Portal (Manual)

#### Step 1: Create Databricks Workspace

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search for "Azure Databricks"
3. Click **Create**
4. Configure:
   - **Resource Group**: Create new "payment-approvals-rg"
   - **Workspace Name**: payment-approvals-ws
   - **Region**: East US
   - **Pricing Tier**: Premium
5. Click **Review + Create** → **Create**
6. Wait 5-10 minutes for deployment

#### Step 2: Create Storage Account

1. Click **Create a resource** → **Storage account**
2. Configure:
   - **Resource Group**: payment-approvals-rg
   - **Storage Account Name**: paymentapprovals[random]
   - **Region**: East US
   - **Performance**: Standard
   - **Redundancy**: LRS
3. Click **Review + Create** → **Create**

#### Step 3: Create Container

1. Go to your storage account
2. Click **Containers** → **+ Container**
3. Name: `payment-approvals`
4. Click **Create**

#### Step 4: Create Key Vault

1. Click **Create a resource** → **Key Vault**
2. Configure:
   - **Resource Group**: payment-approvals-rg
   - **Name**: payment-kv-[random]
   - **Region**: East US
3. Click **Review + Create** → **Create**

#### Step 5: Configure Application

Follow Steps 4-7 from Option 1 above.

---

## 📊 Post-Deployment Setup

### 1. Run Data Ingestion

1. Open Databricks workspace
2. Navigate to: `/Shared/payment_approval_optimization/notebooks/01_data_ingestion/01_bronze_ingestion`
3. Attach to cluster: `payment-approval-acceleration`
4. Run all cells

This generates:
- 100,000 cardholders
- 5,000 merchants  
- 500,000+ transactions

### 2. Start Real-Time Streaming

1. Open: `01_data_ingestion/02_streaming_pipeline`
2. Run all cells
3. Verify streaming queries are active

### 3. Train ML Models

1. Open: `03_smart_checkout/01_ml_model_training`
2. Run all cells
3. Verify models in MLflow

### 4. Create SQL Dashboards

1. Go to **SQL** → **Dashboards**
2. Import queries from `sql/dashboards/`
3. Create visualizations

### 5. Setup Genie

1. Go to **Genie** → **Create Genie Space**
2. Name: "Payment Approvals Analysis"
3. Select tables: `silver_transactions`, `gold_*`
4. Test with queries from `sql/genie_queries.md`

### 6. Launch Databricks App

```bash
cd databricks_app
pip install -r requirements.txt

# Update app.py with your Databricks connection details
streamlit run app.py
```

Access at: http://localhost:8501

---

## 🔐 Security Configuration

### Enable Unity Catalog (Recommended for Production)

```bash
# Enable Unity Catalog on your workspace
az databricks workspace update \
  --resource-group payment-approvals-rg \
  --name payment-approvals-ws \
  --enable-unity-catalog true
```

### Configure Key Vault-Backed Secrets

```bash
# Store storage key in Key Vault
az keyvault secret set \
  --vault-name payment-kv-xxxxx \
  --name storage-account-key \
  --value "<your-storage-key>"

# Configure Databricks to use Key Vault
# This is done through Databricks CLI or UI
```

### Setup Network Security (VNet Injection)

For production deployments, consider VNet injection:

```bash
# Create VNet
az network vnet create \
  --resource-group payment-approvals-rg \
  --name databricks-vnet \
  --address-prefix 10.0.0.0/16

# Create subnets for Databricks
az network vnet subnet create \
  --resource-group payment-approvals-rg \
  --vnet-name databricks-vnet \
  --name public-subnet \
  --address-prefix 10.0.1.0/24

az network vnet subnet create \
  --resource-group payment-approvals-rg \
  --vnet-name databricks-vnet \
  --name private-subnet \
  --address-prefix 10.0.2.0/24

# Deploy Databricks with VNet injection
# (Requires ARM template modification)
```

---

## 💰 Cost Optimization

### Estimated Monthly Costs

| Resource | Configuration | Estimated Cost |
|----------|--------------|----------------|
| Databricks Premium | 8 nodes, 8hrs/day | $800-1200 |
| Storage Account | 1TB data | $20-30 |
| Key Vault | Standard | $5 |
| **Total** | | **$825-1235/month** |

### Cost Saving Tips

1. **Use Auto-Scaling Clusters**
   - Set min workers: 2
   - Set max workers: 8
   - Saves ~30% on compute costs

2. **Enable Auto-Termination**
   - Set idle timeout: 30 minutes
   - Prevents unnecessary charges

3. **Use Spot Instances**
   - For non-critical workloads
   - Saves up to 80% on compute

4. **Archive Old Data**
   - Move to Cool/Archive tier after 90 days
   - Reduces storage costs

5. **Schedule Jobs**
   - Run intensive workloads during off-peak
   - Use scheduled start/stop for clusters

### Monitor Costs

```bash
# View current costs
az consumption usage list \
  --resource-group payment-approvals-rg \
  --start-date 2026-01-01 \
  --end-date 2026-01-31

# Set up budget alerts
az consumption budget create \
  --resource-group payment-approvals-rg \
  --budget-name monthly-budget \
  --amount 1000 \
  --time-grain Monthly
```

---

## 🔍 Monitoring & Alerting

### Enable Azure Monitor

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group payment-approvals-rg \
  --workspace-name payment-logs

# Enable diagnostic settings for Databricks
az monitor diagnostic-settings create \
  --name databricks-diagnostics \
  --resource <databricks-workspace-id> \
  --logs '[{"category": "dbfs","enabled": true}]' \
  --workspace <log-analytics-workspace-id>
```

### Setup Alerts

```bash
# Alert when cluster CPU > 80%
az monitor metrics alert create \
  --name high-cpu-alert \
  --resource-group payment-approvals-rg \
  --scopes <databricks-workspace-id> \
  --condition "avg Percentage CPU > 80" \
  --description "CPU usage is above 80%"
```

---

## 🧪 Validation & Testing

### Run Validation Tests

```bash
# Run automated tests
python tests/test_deployment.py

# Run data quality checks
python tests/test_data_quality.py

# Run ML model validation
python tests/test_models.py
```

### Performance Testing

```bash
# Test streaming throughput
python tests/test_streaming_performance.py

# Test ML inference latency
python tests/test_inference_latency.py
```

---

## 🐛 Troubleshooting

### Issue: Deployment Fails

```bash
# Check deployment status
az deployment group show \
  --resource-group payment-approvals-rg \
  --name deployment-name

# View error details
az deployment operation group list \
  --resource-group payment-approvals-rg \
  --name deployment-name
```

### Issue: Cannot Access Databricks Workspace

- Check firewall rules
- Verify network security groups
- Ensure you're logged in with correct account

### Issue: Storage Mount Fails

```python
# In Databricks notebook, check mounts
display(dbutils.fs.mounts())

# Unmount if needed
dbutils.fs.unmount("/mnt/payment_data")

# Remount with correct credentials
```

### Issue: Quota Exceeded

```bash
# Check current quota
az vm list-usage --location eastus --output table

# Request quota increase through Azure Portal
```

---

## 🔄 CI/CD Integration

### Azure DevOps Pipeline

Create `azure-pipelines.yml`:

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: AzureCLI@2
  inputs:
    azureSubscription: 'Azure-Subscription'
    scriptType: 'bash'
    scriptLocation: 'scriptPath'
    scriptPath: 'azure/deploy-azure.sh'

- task: Bash@3
  inputs:
    targetType: 'inline'
    script: |
      pip install databricks-cli
      ./scripts/deploy.sh
```

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy Infrastructure
      run: ./azure/deploy-azure.sh
      
    - name: Deploy Application
      run: ./scripts/deploy.sh
```

---

## 📞 Support & Resources

### Azure Resources

- [Azure Databricks Documentation](https://docs.microsoft.com/azure/databricks/)
- [Azure Storage Documentation](https://docs.microsoft.com/azure/storage/)
- [Azure Key Vault Documentation](https://docs.microsoft.com/azure/key-vault/)

### Cost Calculator

- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Databricks Pricing](https://azure.microsoft.com/pricing/details/databricks/)

### Support Channels

- Azure Support: portal.azure.com → Support
- Databricks Support: accounts.cloud.databricks.com/support
- Community: stackoverflow.com/questions/tagged/azure-databricks

---

## 🎉 Next Steps

After successful deployment:

1. ✅ Run data ingestion notebooks
2. ✅ Train ML models
3. ✅ Create dashboards
4. ✅ Test Genie queries
5. ✅ Launch Databricks App
6. ✅ Setup monitoring and alerts
7. ✅ Configure backup and disaster recovery
8. ✅ Plan production migration

**Your Azure Databricks demo is now live!** 🚀

---

## 🗑️ Cleanup

To delete all resources:

```bash
# Delete entire resource group
az group delete --name payment-approvals-rg --yes --no-wait

# Or delete individual resources
az databricks workspace delete --name payment-approvals-ws --resource-group payment-approvals-rg
az storage account delete --name paymentapprovals12345 --resource-group payment-approvals-rg
az keyvault delete --name payment-kv-12345 --resource-group payment-approvals-rg
```

**Warning**: This permanently deletes all data and cannot be undone!
