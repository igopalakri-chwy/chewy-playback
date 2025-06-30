#!/usr/bin/env python3
"""
Script to run the No Reviews pipeline for the first 10 customers.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add the No_Reviews_Pipeline directory to the path
sys.path.append(str(Path(__file__).parent))

from chewy_playback_pipeline_no_reviews import ChewyPlaybackPipelineNoReviews


def get_first_10_customer_ids():
    """Get the first 10 unique customer IDs from the qualifying reviews CSV."""
    
    # Load the qualifying reviews data
    data_path = Path(__file__).parent.parent / "Data" / "qualifying_reviews.csv"
    qualifying_reviews = pd.read_csv(data_path)
    
    # Get unique customer IDs and take the first 10
    unique_customer_ids = qualifying_reviews['CUSTOMER_ID'].unique()
    first_10_customers = unique_customer_ids[:10]
    
    # Convert to strings for consistency
    customer_ids = [str(customer_id) for customer_id in first_10_customers]
    
    print(f"Found {len(unique_customer_ids)} total customers")
    print(f"Processing first 10 customers: {customer_ids}")
    
    return customer_ids


def main():
    """Run the No Reviews pipeline for the first 10 customers."""
    
    print("🚀 Running No Reviews Pipeline for First 10 Customers")
    print("=" * 60)
    
    try:
        # Get the first 10 customer IDs
        customer_ids = get_first_10_customer_ids()
        
        # Initialize pipeline
        pipeline = ChewyPlaybackPipelineNoReviews()
        
        # Modify the output directory to save in No_Reviews_Pipeline folder
        pipeline.output_dir = Path(__file__).parent / "Output"
        pipeline.output_dir.mkdir(exist_ok=True)
        
        # Run pipeline for the first 10 customers
        pipeline.run_pipeline(customer_ids=customer_ids)
        
        print(f"\n✅ Successfully completed No Reviews pipeline for {len(customer_ids)} customers")
        print(f"📁 Check No_Reviews_Pipeline/Output/ directory for results")
        
    except Exception as e:
        print(f"❌ Error running No Reviews pipeline: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 