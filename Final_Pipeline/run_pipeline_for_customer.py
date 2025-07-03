#!/usr/bin/env python3
"""
Script to run the Chewy Playback Pipeline for a single customer.
This unified pipeline automatically detects whether the customer has reviews or not
and uses the appropriate intelligence agent.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import the pipeline
sys.path.append(str(Path(__file__).parent))

from chewy_playback_pipeline import ChewyPlaybackPipeline


def main():
    """Main function to run the pipeline for a single customer."""
    if len(sys.argv) != 2:
        print("Usage: python run_pipeline_for_customer.py <customer_id>")
        print("Example: python run_pipeline_for_customer.py 1183376")
        sys.exit(1)
    
    customer_id = sys.argv[1]
    
    print(f"🚀 Running Chewy Playback Pipeline for Customer ID: {customer_id}")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipeline()
        
        # Run pipeline for the specific customer
        pipeline.run_pipeline(customer_ids=[customer_id])
        
        print(f"\n✅ Pipeline completed for customer {customer_id}")
        print("🎯 Confidence scores were automatically calculated as part of the pipeline")
        print(f"\n📁 Check the 'Output/{customer_id}' directory for results")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 