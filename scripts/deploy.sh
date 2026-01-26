#!/bin/bash

# Deployment script for Payment Approval Acceleration Demo
# This script automates the deployment to Azure Databricks

set -e  # Exit on error

echo "========================================="
echo "Payment Approval Acceleration Deployment"
echo "========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI not found. Please install it first:"
    echo "   pip install databricks-cli"
    exit 1
fi
echo "✓ Databricks CLI found"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with required configuration."
    exit 1
fi
echo "✓ .env file found"

# Load environment variables
source .env

# Verify required environment variables
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo "❌ DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env file"
    exit 1
fi
echo "✓ Environment variables loaded"

echo ""
echo "Step 1: Creating workspace directories..."
databricks workspace mkdirs /Shared/payment_approval_optimization || true
databricks workspace mkdirs /Shared/payment_approval_optimization/notebooks || true
databricks workspace mkdirs /Shared/payment_approval_optimization/data_generation || true
echo "✓ Workspace directories created"

echo ""
echo "Step 2: Uploading notebooks..."
databricks workspace import_dir \
  notebooks \
  /Shared/payment_approval_optimization/notebooks \
  --overwrite
echo "✓ Notebooks uploaded"

echo ""
echo "Step 3: Uploading data generators..."
databricks fs mkdirs dbfs:/FileStore/payment_approvals/generators || true
databricks fs cp data_generation/transaction_generator.py \
  dbfs:/FileStore/payment_approvals/generators/ --overwrite
databricks fs cp data_generation/cardholder_generator.py \
  dbfs:/FileStore/payment_approvals/generators/ --overwrite
databricks fs cp data_generation/merchant_generator.py \
  dbfs:/FileStore/payment_approvals/generators/ --overwrite
databricks fs cp data_generation/external_data_generator.py \
  dbfs:/FileStore/payment_approvals/generators/ --overwrite
echo "✓ Data generators uploaded"

echo ""
echo "Step 4: Uploading configuration..."
databricks fs mkdirs dbfs:/FileStore/payment_approvals/config || true
databricks fs cp config/app_config.yaml \
  dbfs:/FileStore/payment_approvals/config/ --overwrite
echo "✓ Configuration uploaded"

echo ""
echo "Step 5: Creating cluster (if not exists)..."
CLUSTER_ID=$(databricks clusters list --output JSON | \
  python3 -c "import sys, json; clusters = json.load(sys.stdin).get('clusters', []); print(next((c['cluster_id'] for c in clusters if c['cluster_name'] == 'payment-approval-acceleration'), ''))")

if [ -z "$CLUSTER_ID" ]; then
    echo "Creating new cluster..."
    CLUSTER_ID=$(databricks clusters create --json-file config/cluster_config.json | \
      python3 -c "import sys, json; print(json.load(sys.stdin)['cluster_id'])")
    echo "✓ Cluster created: $CLUSTER_ID"
else
    echo "✓ Using existing cluster: $CLUSTER_ID"
fi

echo ""
echo "Step 6: Installing libraries on cluster..."
cat > /tmp/libraries.json <<EOF
{
  "cluster_id": "$CLUSTER_ID",
  "libraries": [
    {"pypi": {"package": "faker==22.0.0"}},
    {"pypi": {"package": "mimesis==11.1.0"}},
    {"pypi": {"package": "xgboost==2.0.0"}},
    {"pypi": {"package": "lightgbm==4.1.0"}},
    {"pypi": {"package": "plotly==5.18.0"}}
  ]
}
EOF
databricks libraries install --json-file /tmp/libraries.json
rm /tmp/libraries.json
echo "✓ Libraries installation initiated"

echo ""
echo "Step 7: Waiting for cluster to be ready..."
while true; do
    STATE=$(databricks clusters get --cluster-id $CLUSTER_ID | \
      python3 -c "import sys, json; print(json.load(sys.stdin)['state'])")
    
    if [ "$STATE" = "RUNNING" ]; then
        echo "✓ Cluster is running"
        break
    elif [ "$STATE" = "TERMINATED" ]; then
        echo "Starting cluster..."
        databricks clusters start --cluster-id $CLUSTER_ID
    fi
    
    echo "Cluster state: $STATE. Waiting..."
    sleep 10
done

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Navigate to Databricks workspace: $DATABRICKS_HOST"
echo "2. Open notebook: /Shared/payment_approval_optimization/notebooks/01_data_ingestion/01_bronze_ingestion"
echo "3. Attach to cluster: payment-approval-acceleration"
echo "4. Run all cells to ingest initial data"
echo "5. Continue with other notebooks in sequence"
echo ""
echo "Cluster ID: $CLUSTER_ID"
echo ""
echo "For detailed instructions, see docs/deployment.md"
echo ""
