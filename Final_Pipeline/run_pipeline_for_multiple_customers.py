#!/usr/bin/env python3
"""
Script to run the Chewy Playback Pipeline for multiple customers.
This unified pipeline automatically detects whether each customer has reviews or not
and uses the appropriate intelligence agent for each customer.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add the current directory to the path so we can import the pipeline
sys.path.append(str(Path(__file__).parent))

from chewy_playback_pipeline import ChewyPlaybackPipeline


def get_first_10_customers():
    """Get the first 10 customer IDs from the order history data."""
    try:
        # Load order history data
        order_data_path = Path("Data/order_history.csv")
        if not order_data_path.exists():
            print("❌ Order history file not found. Please ensure Data/order_history.csv exists.")
            return []
        
        df = pd.read_csv(order_data_path)
        
        # Get unique customer IDs and take the first 10
        customer_ids = df['CUSTOMER_ID'].astype(str).unique()[:10].tolist()
        
        print(f"Using first 10 customers from dataset: {customer_ids}")
        return customer_ids
        
    except Exception as e:
        print(f"❌ Error loading customer data: {e}")
        return []


def main():
    """Main function to run the pipeline for multiple customers."""
    if len(sys.argv) > 1:
        # Use customer IDs provided as command line arguments
        customer_ids = sys.argv[1:]
        print(f"🚀 Running Chewy Playback Pipeline for {len(customer_ids)} Customers")
        print("=" * 70)
        print(f"Customer IDs: {', '.join(customer_ids)}")
        print("=" * 70)
    else:
        # Use the first 10 customers from the dataset
        customer_ids = get_first_10_customers()
        if not customer_ids:
            print("❌ No customer IDs found. Exiting.")
            sys.exit(1)
        
        print(f"🚀 Running Chewy Playback Pipeline for {len(customer_ids)} Customers")
        print("=" * 70)
        print(f"Customer IDs: {', '.join(customer_ids)}")
        print("=" * 70)
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipeline()
        
        # Run pipeline for the specified customers
        pipeline.run_pipeline(customer_ids=customer_ids)
        
        print(f"\n✅ Pipeline completed for {len(customer_ids)} customers")
        print("🎯 Confidence scores were automatically calculated as part of the pipeline")
        print(f"\n📁 Check the 'Output' directory for results")
        
        # Print results summary
        print("\n📊 Results Summary:")
        for customer_id in customer_ids:
            output_dir = Path("Output") / customer_id
            if output_dir.exists():
                print(f"  ✅ {customer_id}: Results saved to Output/{customer_id}/")
            else:
                print(f"  ❌ {customer_id}: No results generated")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 