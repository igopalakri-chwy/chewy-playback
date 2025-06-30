#!/usr/bin/env python3
"""
Script to run the Boyue pipeline for a specific customer.
"""

import sys
import os
from pathlib import Path

# Add the test_pipeline_boyue directory to the path
sys.path.append(str(Path(__file__).parent))

from chewy_playback_pipeline_boyue import ChewyPlaybackPipelineBoyue


def main():
    """Run the Boyue pipeline for customer 1183376."""
    
    # Customer ID to test with
    customer_id = "1183376"
    
    print(f"🚀 Running Boyue Pipeline for Customer {customer_id}")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipelineBoyue()
        
        # Run pipeline for specific customer
        pipeline.run_pipeline(customer_ids=[customer_id])
        
        print(f"\n✅ Successfully completed Boyue pipeline for customer {customer_id}")
        print(f"📁 Check Output_Boyue/{customer_id}/ for results")
        
    except Exception as e:
        print(f"❌ Error running Boyue pipeline: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 