#!/usr/bin/env python3
"""
Script to run the Chewy Playback Pipeline for the first 10 customers in the dataset.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add agent directories to path
sys.path.append('Agents/Review_and_Order_Intelligence_Agent')
sys.path.append('Agents/Narrative_Generation_Agent')
sys.path.append('Agents/Image_Generation_Agent')

from chewy_playback_pipeline import ChewyPlaybackPipeline

def get_first_10_customers():
    """Get the first 10 unique customer IDs from the dataset."""
    try:
        df = pd.read_csv('Data/qualifying_reviews.csv')
        unique_customers = df['CUSTOMER_ID'].unique()
        return [str(customer_id) for customer_id in unique_customers[:10]]
    except Exception as e:
        print(f"Error reading customer data: {e}")
        return []

def run_pipeline_for_multiple_customers(customer_ids: list, openai_api_key: str = None):
    """
    Run the complete pipeline for multiple customer IDs.
    
    Args:
        customer_ids: List of customer IDs to process
        openai_api_key: OpenAI API key (optional, can use environment variable)
    """
    print(f"🚀 Running Chewy Playback Pipeline for {len(customer_ids)} Customers")
    print("=" * 70)
    print(f"Customer IDs: {', '.join(customer_ids)}")
    print("=" * 70)
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipeline(openai_api_key=openai_api_key)
        
        # Run pipeline for multiple customers
        pipeline.run_pipeline(customer_ids=customer_ids)
        
        print(f"\n✅ Pipeline completed for {len(customer_ids)} customers")
        print("🎯 Confidence scores were automatically calculated as part of the pipeline")
        print(f"\n📁 Check the 'Output' directory for results")
        
        # Show summary of results
        print("\n📊 Results Summary:")
        for customer_id in customer_ids:
            output_dir = Path("Output") / customer_id
            if output_dir.exists():
                print(f"  ✅ {customer_id}: Results saved to Output/{customer_id}/")
            else:
                print(f"  ❌ {customer_id}: No output found")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        raise

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Chewy Playback Pipeline for first 10 customers")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use environment variable)")
    parser.add_argument("--customers", nargs="+", help="Specific customer IDs to process (optional)")
    
    args = parser.parse_args()
    
    # Check if OpenAI API key is available
    if not args.api_key and not os.getenv('OPENAI_API_KEY'):
        print("❌ OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Get customer IDs
    if args.customers:
        customer_ids = args.customers
        print(f"Using provided customer IDs: {customer_ids}")
    else:
        customer_ids = get_first_10_customers()
        if not customer_ids:
            print("❌ Failed to get customer IDs from dataset")
            sys.exit(1)
        print(f"Using first 10 customers from dataset: {customer_ids}")
    
    # Run pipeline
    run_pipeline_for_multiple_customers(customer_ids, args.api_key)

if __name__ == "__main__":
    main() 