"""
Verification script for Payment Approval Acceleration deployment

This script verifies that all components are properly deployed and functioning.
"""

import os
import sys
from databricks_cli.sdk import ApiClient, ClusterService, DbfsService, WorkspaceService
from databricks_cli.clusters.api import ClusterApi
from databricks_cli.dbfs.api import DbfsApi
from databricks_cli.workspace.api import WorkspaceApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check if required environment variables are set"""
    print("Checking environment variables...")
    required_vars = ['DATABRICKS_HOST', 'DATABRICKS_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✓ All required environment variables are set")
    return True

def check_cluster(api_client):
    """Check if cluster exists and is running"""
    print("\nChecking cluster...")
    try:
        cluster_api = ClusterApi(api_client)
        clusters = cluster_api.list_clusters()
        
        target_cluster = next(
            (c for c in clusters.get('clusters', []) 
             if c['cluster_name'] == 'payment-approval-acceleration'),
            None
        )
        
        if not target_cluster:
            print("❌ Cluster 'payment-approval-acceleration' not found")
            return False
        
        state = target_cluster['state']
        if state == 'RUNNING':
            print(f"✓ Cluster is running (ID: {target_cluster['cluster_id']})")
            return True
        else:
            print(f"⚠️  Cluster exists but is {state}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking cluster: {e}")
        return False

def check_workspace(api_client):
    """Check if notebooks are uploaded"""
    print("\nChecking workspace...")
    try:
        workspace_api = WorkspaceApi(api_client)
        
        paths_to_check = [
            '/Shared/payment_approval_optimization',
            '/Shared/payment_approval_optimization/notebooks',
        ]
        
        all_exist = True
        for path in paths_to_check:
            try:
                workspace_api.get_status(path)
                print(f"✓ Found: {path}")
            except:
                print(f"❌ Missing: {path}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"❌ Error checking workspace: {e}")
        return False

def check_dbfs(api_client):
    """Check if files are uploaded to DBFS"""
    print("\nChecking DBFS...")
    try:
        dbfs_api = DbfsApi(api_client)
        
        paths_to_check = [
            'dbfs:/FileStore/payment_approvals/generators/transaction_generator.py',
            'dbfs:/FileStore/payment_approvals/generators/cardholder_generator.py',
            'dbfs:/FileStore/payment_approvals/generators/merchant_generator.py',
            'dbfs:/FileStore/payment_approvals/config/app_config.yaml',
        ]
        
        all_exist = True
        for path in paths_to_check:
            try:
                dbfs_api.get_status(path)
                print(f"✓ Found: {path}")
            except:
                print(f"❌ Missing: {path}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"❌ Error checking DBFS: {e}")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("Payment Approval Acceleration - Deployment Verification")
    print("=" * 60)
    
    # Check environment variables
    if not check_env_vars():
        sys.exit(1)
    
    # Initialize API client
    try:
        api_client = ApiClient(
            host=os.getenv('DATABRICKS_HOST'),
            token=os.getenv('DATABRICKS_TOKEN')
        )
    except Exception as e:
        print(f"❌ Failed to initialize Databricks API client: {e}")
        sys.exit(1)
    
    # Run checks
    results = {
        'cluster': check_cluster(api_client),
        'workspace': check_workspace(api_client),
        'dbfs': check_dbfs(api_client),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for component, status in results.items():
        status_icon = "✓" if status else "❌"
        print(f"{status_icon} {component.capitalize()}: {'PASS' if status else 'FAIL'}")
    
    print()
    
    if all(results.values()):
        print("✓ All checks passed! Deployment is ready.")
        print("\nNext steps:")
        print("1. Open Databricks workspace")
        print("2. Navigate to /Shared/payment_approval_optimization/notebooks")
        print("3. Run notebooks in sequence starting with 01_data_ingestion")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\nRefer to docs/deployment.md for troubleshooting.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
