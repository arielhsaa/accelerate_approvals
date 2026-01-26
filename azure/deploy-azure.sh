#!/bin/bash

# Azure Deployment Script for Payment Approval Acceleration Demo
# This script deploys all Azure resources and configures Databricks

set -e  # Exit on error

echo "========================================="
echo "Azure Databricks Demo Deployment"
echo "Payment Approval Acceleration"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these values
RESOURCE_GROUP="${RESOURCE_GROUP:-payment-approvals-rg}"
LOCATION="${LOCATION:-eastus}"
WORKSPACE_NAME="${WORKSPACE_NAME:-payment-approvals-ws}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-paymentapprovals$(date +%s | tail -c 5)}"
CONTAINER_NAME="payment-approvals"
KEY_VAULT_NAME="${KEY_VAULT_NAME:-payment-kv-$(date +%s | tail -c 5)}"

echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Workspace: $WORKSPACE_NAME"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first:${NC}"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi
echo -e "${GREEN}✓ Azure CLI found${NC}"

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Running 'az login'...${NC}"
    az login
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}✓ Logged in to subscription: $SUBSCRIPTION_ID${NC}"
echo ""

# Step 1: Create Resource Group
echo "Step 1: Creating Resource Group..."
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Resource group already exists${NC}"
else
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    echo -e "${GREEN}✓ Resource group created${NC}"
fi
echo ""

# Step 2: Create Storage Account
echo "Step 2: Creating Storage Account..."
if az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Storage account already exists${NC}"
else
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2 \
        --output none
    echo -e "${GREEN}✓ Storage account created${NC}"
fi

# Get storage key
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" -o tsv)
echo -e "${GREEN}✓ Retrieved storage key${NC}"
echo ""

# Step 3: Create Storage Container
echo "Step 3: Creating Storage Container..."
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --output none || echo -e "${YELLOW}⚠️  Container already exists${NC}"
echo -e "${GREEN}✓ Storage container ready${NC}"
echo ""

# Step 4: Create Key Vault
echo "Step 4: Creating Key Vault..."
if az keyvault show --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Key Vault already exists${NC}"
else
    az keyvault create \
        --name $KEY_VAULT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    echo -e "${GREEN}✓ Key Vault created${NC}"
fi

# Store storage key in Key Vault
az keyvault secret set \
    --vault-name $KEY_VAULT_NAME \
    --name "storage-account-key" \
    --value "$STORAGE_KEY" \
    --output none
echo -e "${GREEN}✓ Storage key stored in Key Vault${NC}"
echo ""

# Step 5: Deploy Databricks Workspace
echo "Step 5: Deploying Databricks Workspace..."
if az databricks workspace show --name $WORKSPACE_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Databricks workspace already exists${NC}"
else
    az databricks workspace create \
        --name $WORKSPACE_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku premium \
        --output none
    
    echo -e "${YELLOW}⏳ Waiting for workspace to be ready (this may take 5-10 minutes)...${NC}"
    az databricks workspace wait \
        --name $WORKSPACE_NAME \
        --resource-group $RESOURCE_GROUP \
        --created
    echo -e "${GREEN}✓ Databricks workspace deployed${NC}"
fi

# Get workspace URL
WORKSPACE_URL=$(az databricks workspace show \
    --name $WORKSPACE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query workspaceUrl -o tsv)
echo -e "${GREEN}✓ Workspace URL: https://$WORKSPACE_URL${NC}"
echo ""

# Step 6: Generate .env file
echo "Step 6: Generating configuration files..."
cat > .env << EOF
# Azure Configuration
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP=$RESOURCE_GROUP
AZURE_LOCATION=$LOCATION

# Databricks Configuration
DATABRICKS_HOST=https://$WORKSPACE_URL
DATABRICKS_TOKEN=<generate-token-in-databricks-ui>

# Storage Configuration
STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT
STORAGE_ACCOUNT_KEY=$STORAGE_KEY
STORAGE_CONTAINER=$CONTAINER_NAME

# Key Vault Configuration
KEY_VAULT_NAME=$KEY_VAULT_NAME
EOF
echo -e "${GREEN}✓ .env file created${NC}"
echo ""

# Step 7: Create deployment summary
cat > deployment-summary.txt << EOF
========================================
Azure Deployment Summary
========================================

Resource Group: $RESOURCE_GROUP
Location: $LOCATION

Resources Created:
✓ Databricks Workspace: $WORKSPACE_NAME
✓ Storage Account: $STORAGE_ACCOUNT
✓ Storage Container: $CONTAINER_NAME
✓ Key Vault: $KEY_VAULT_NAME

Databricks Workspace URL:
https://$WORKSPACE_URL

Next Steps:
1. Generate Databricks Personal Access Token:
   - Go to https://$WORKSPACE_URL
   - Click your profile → Settings → Developer → Access Tokens
   - Generate New Token
   - Update DATABRICKS_TOKEN in .env file

2. Install Databricks CLI:
   pip install databricks-cli

3. Configure Databricks CLI:
   databricks configure --token

4. Deploy application code:
   ./scripts/deploy.sh

5. Access Databricks workspace and run notebooks

Cost Estimate (per month):
- Databricks Premium: ~\$500-1500 (depends on usage)
- Storage Account: ~\$20-50
- Key Vault: ~\$5
Total: ~\$525-1555/month

To delete all resources:
  az group delete --name $RESOURCE_GROUP --yes --no-wait

========================================
EOF

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Resources deployed:"
echo -e "${GREEN}✓ Resource Group: $RESOURCE_GROUP${NC}"
echo -e "${GREEN}✓ Databricks Workspace: $WORKSPACE_NAME${NC}"
echo -e "${GREEN}✓ Storage Account: $STORAGE_ACCOUNT${NC}"
echo -e "${GREEN}✓ Key Vault: $KEY_VAULT_NAME${NC}"
echo ""
echo "Databricks Workspace URL:"
echo -e "${YELLOW}https://$WORKSPACE_URL${NC}"
echo ""
echo "Next Steps:"
echo "1. Go to Databricks workspace and generate a Personal Access Token"
echo "2. Update DATABRICKS_TOKEN in .env file"
echo "3. Run: ./scripts/deploy.sh"
echo ""
echo "See deployment-summary.txt for full details"
echo ""
echo -e "${GREEN}Total deployment time: $SECONDS seconds${NC}"
