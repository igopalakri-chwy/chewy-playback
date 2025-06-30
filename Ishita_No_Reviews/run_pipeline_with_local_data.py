#!/usr/bin/env python3
"""
Script to run the Ishita No Reviews pipeline using local Data_No_Reviews folder.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from chewy_playback_pipeline_no_reviews import ChewyPlaybackPipelineNoReviews


def get_first_10_customer_ids():
    """Get the first 10 unique customer IDs from the local processed_orderhistory.csv."""
    
    # Load the local data
    data_path = Path(__file__).parent / "Data_No_Reviews" / "processed_orderhistory.csv"
    order_data = pd.read_csv(data_path)
    
    # Get unique customer IDs and take the first 10
    unique_customer_ids = order_data['customer_id'].unique()
    first_10_customers = unique_customer_ids[:10]
    
    # Convert to strings for consistency
    customer_ids = [str(customer_id) for customer_id in first_10_customers]
    
    print(f"Found {len(unique_customer_ids)} total customers in local data")
    print(f"Processing first 10 customers: {customer_ids}")
    
    return customer_ids


def main():
    """Run the Ishita No Reviews pipeline for the first 10 customers using local data."""
    
    print("🚀 Running Ishita No Reviews Pipeline with Local Data")
    print("=" * 60)
    
    try:
        # Get the first 10 customer IDs from local data
        customer_ids = get_first_10_customer_ids()
        
        # Initialize pipeline
        pipeline = ChewyPlaybackPipelineNoReviews()
        
        # Modify the data directory to use local Data_No_Reviews folder
        pipeline.data_dir = Path(__file__).parent / "Data_No_Reviews"
        
        # Modify the output directory to save in the same folder
        pipeline.output_dir = Path(__file__).parent / "Output"
        pipeline.output_dir.mkdir(exist_ok=True)
        
        # Run pipeline for the first 10 customers
        pipeline.run_pipeline(customer_ids=customer_ids)
        
        print(f"\n✅ Successfully completed Ishita No Reviews pipeline for {len(customer_ids)} customers")
        print(f"📁 Check Ishita_No_Reviews/Output/ directory for results")
        
    except Exception as e:
        print(f"❌ Error running Ishita No Reviews pipeline: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 