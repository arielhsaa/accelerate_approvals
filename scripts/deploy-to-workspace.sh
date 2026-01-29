#!/bin/bash

# Deployment Script for Existing Databricks Workspace
# Workspace: https://adb-984752964297111.11.azuredatabricks.net

set -e

echo "========================================="
echo "Payment Approval Acceleration"
echo "Deployment to Existing Workspace"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
DATABRICKS_HOST="https://adb-984752964297111.11.azuredatabricks.net"
WORKSPACE_FOLDER="/Shared/payment_approval_optimization"

echo "Target Workspace: $DATABRICKS_HOST"
echo ""

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}❌ Databricks CLI not found${NC}"
    echo "Installing Databricks CLI..."
    pip install databricks-cli
fi
echo -e "${GREEN}✓ Databricks CLI installed${NC}"

# Check if token is configured
if [ -z "$DATABRICKS_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  DATABRICKS_TOKEN not set${NC}"
    echo ""
    echo "Please generate a Personal Access Token:"
    echo "1. Go to: $DATABRICKS_HOST"
    echo "2. Click Settings → Developer → Access Tokens"
    echo "3. Generate New Token"
    echo "4. Run: export DATABRICKS_TOKEN=<your-token>"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Databricks token configured${NC}"

# Configure Databricks CLI
cat > ~/.databrickscfg << EOF
[DEFAULT]
host = $DATABRICKS_HOST
token = $DATABRICKS_TOKEN
EOF
echo -e "${GREEN}✓ Databricks CLI configured${NC}"
echo ""

# Step 1: Create workspace directories
echo "Step 1: Creating workspace directories..."
databricks workspace mkdirs "$WORKSPACE_FOLDER" || true
databricks workspace mkdirs "$WORKSPACE_FOLDER/notebooks" || true
databricks workspace mkdirs "$WORKSPACE_FOLDER/data_generation" || true
echo -e "${GREEN}✓ Workspace directories created${NC}"
echo ""

# Step 2: Upload notebooks
echo "Step 2: Uploading notebooks..."
databricks workspace import-dir \
  notebooks \
  "$WORKSPACE_FOLDER/notebooks" \
  --overwrite
echo -e "${GREEN}✓ Notebooks uploaded${NC}"
echo ""

# Step 3: Upload data generators to DBFS
echo "Step 3: Uploading data generators..."
databricks fs mkdirs dbfs:/FileStore/payment_approvals/generators || true
databricks fs cp data_generation/transaction_generator.py \
  dbfs:/FileStore/payment_approvals/generators/transaction_generator.py --overwrite
databricks fs cp data_generation/cardholder_generator.py \
  dbfs:/FileStore/payment_approvals/generators/cardholder_generator.py --overwrite
databricks fs cp data_generation/merchant_generator.py \
  dbfs:/FileStore/payment_approvals/generators/merchant_generator.py --overwrite
databricks fs cp data_generation/external_data_generator.py \
  dbfs:/FileStore/payment_approvals/generators/external_data_generator.py --overwrite
echo -e "${GREEN}✓ Data generators uploaded${NC}"
echo ""

# Step 4: Upload configuration
echo "Step 4: Uploading configuration..."
databricks fs mkdirs dbfs:/FileStore/payment_approvals/config || true
databricks fs cp config/app_config.yaml \
  dbfs:/FileStore/payment_approvals/config/app_config.yaml --overwrite
echo -e "${GREEN}✓ Configuration uploaded${NC}"
echo ""

# Step 5: Check for existing cluster
echo "Step 5: Checking for cluster..."
CLUSTER_NAME="payment-approval-acceleration"
CLUSTER_ID=$(databricks clusters list --output JSON | \
  python3 -c "import sys, json; clusters = json.load(sys.stdin).get('clusters', []); print(next((c['cluster_id'] for c in clusters if c['cluster_name'] == '$CLUSTER_NAME'), ''))" 2>/dev/null || echo "")

if [ -z "$CLUSTER_ID" ]; then
    echo "Creating new cluster..."
    CLUSTER_ID=$(databricks clusters create --json '{
      "cluster_name": "'$CLUSTER_NAME'",
      "spark_version": "14.3.x-scala2.12",
      "node_type_id": "Standard_DS3_v2",
      "driver_node_type_id": "Standard_DS3_v2",
      "autoscale": {
        "min_workers": 2,
        "max_workers": 8
      },
      "spark_conf": {
        "spark.databricks.delta.preview.enabled": "true",
        "spark.databricks.delta.schema.autoMerge.enabled": "true",
        "spark.databricks.delta.optimizeWrite.enabled": "true"
      },
      "custom_tags": {
        "Project": "PaymentApprovalAcceleration"
      }
    }' | python3 -c "import sys, json; print(json.load(sys.stdin)['cluster_id'])")
    echo -e "${GREEN}✓ Cluster created: $CLUSTER_ID${NC}"
else
    echo -e "${GREEN}✓ Using existing cluster: $CLUSTER_ID${NC}"
fi
echo ""

# Step 6: Install libraries
echo "Step 6: Installing libraries..."
databricks libraries install --json "{
  \"cluster_id\": \"$CLUSTER_ID\",
  \"libraries\": [
    {\"pypi\": {\"package\": \"faker==22.0.0\"}},
    {\"pypi\": {\"package\": \"xgboost==2.0.0\"}},
    {\"pypi\": {\"package\": \"lightgbm==4.1.0\"}},
    {\"pypi\": {\"package\": \"plotly==5.18.0\"}}
  ]
}"
echo -e "${GREEN}✓ Libraries installation initiated${NC}"
echo ""

# Step 7: Wait for cluster to be ready
echo "Step 7: Waiting for cluster to be ready..."
echo -e "${YELLOW}This may take 5-10 minutes...${NC}"

MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATE=$(databricks clusters get --cluster-id $CLUSTER_ID | \
      python3 -c "import sys, json; print(json.load(sys.stdin)['state'])" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$STATE" = "RUNNING" ]; then
        echo -e "${GREEN}✓ Cluster is running${NC}"
        break
    elif [ "$STATE" = "TERMINATED" ]; then
        echo "Starting cluster..."
        databricks clusters start --cluster-id $CLUSTER_ID
    fi
    
    echo "Cluster state: $STATE. Waiting... ($((ATTEMPT+1))/$MAX_ATTEMPTS)"
    sleep 10
    ATTEMPT=$((ATTEMPT+1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}❌ Timeout waiting for cluster${NC}"
    exit 1
fi
echo ""

# Step 8: Create deployment summary
cat > deployment-output.txt << EOF
========================================
Deployment Summary
========================================

Workspace: $DATABRICKS_HOST
Cluster ID: $CLUSTER_ID
Cluster Name: $CLUSTER_NAME

Deployed Components:
✓ Notebooks: $WORKSPACE_FOLDER/notebooks/
✓ Data Generators: dbfs:/FileStore/payment_approvals/generators/
✓ Configuration: dbfs:/FileStore/payment_approvals/config/
✓ Cluster: $CLUSTER_NAME

Next Steps:
1. Open your Databricks workspace:
   $DATABRICKS_HOST

2. Navigate to:
   $WORKSPACE_FOLDER/notebooks/01_data_ingestion/01_bronze_ingestion

3. Attach to cluster: $CLUSTER_NAME

4. Run all cells to generate initial data

5. Continue with remaining notebooks:
   - 02_streaming_pipeline (real-time processing)
   - 01_ml_model_training (train ML models)
   - 01_decline_analysis (analyze declines)
   - 01_retry_predictor (smart retry)

6. Create SQL dashboards using queries from:
   sql/dashboards/

7. Setup Genie for natural language queries

8. Launch Databricks App:
   cd databricks_app
   streamlit run app.py

========================================
EOF

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Summary saved to: deployment-output.txt"
echo ""
echo "Next Steps:"
echo "1. Open workspace: $DATABRICKS_HOST"
echo "2. Navigate to: $WORKSPACE_FOLDER/notebooks/01_data_ingestion/01_bronze_ingestion"
echo "3. Attach to cluster: $CLUSTER_NAME"
echo "4. Run all cells"
echo ""
echo -e "${GREEN}Cluster ID: $CLUSTER_ID${NC}"
echo ""
cat deployment-output.txt
