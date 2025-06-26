#!/usr/bin/env python3
"""
Script to run the Chewy Playback Pipeline for a specific customer ID
and then add confidence scores to the output.
"""

import os
import sys
from pathlib import Path

# Add agent directories to path
sys.path.append('Agents/Review_and_Order_Intelligence_Agent')
sys.path.append('Agents/Narrative_Generation_Agent')
sys.path.append('Agents/Image_Generation_Agent')

from chewy_playback_pipeline import ChewyPlaybackPipeline
from add_confidence_score import ConfidenceScoreCalculator

def run_pipeline_for_customer(customer_id: str, openai_api_key: str = None):
    """
    Run the complete pipeline for a specific customer ID.
    
    Args:
        customer_id: The customer ID to process
        openai_api_key: OpenAI API key (optional, can use environment variable)
    """
    print(f"🚀 Running Chewy Playback Pipeline for Customer ID: {customer_id}")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipeline(openai_api_key=openai_api_key)
        
        # Run pipeline for specific customer
        pipeline.run_pipeline(customer_ids=[customer_id])
        
        print(f"\n✅ Pipeline completed for customer {customer_id}")
        
        # Add confidence scores to the output
        print("\n🎯 Adding confidence scores to the output...")
        calculator = ConfidenceScoreCalculator()
        
        # Find the output file for this customer
        output_file = Path("Output") / customer_id / "enriched_pet_profile.json"
        
        if output_file.exists():
            success = calculator.process_json_file(str(output_file))
            if success:
                print(f"✅ Confidence scores added to {output_file}")
            else:
                print(f"❌ Failed to add confidence scores to {output_file}")
        else:
            print(f"❌ Output file not found: {output_file}")
        
        print(f"\n📁 Check the 'Output/{customer_id}' directory for results")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        raise

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Chewy Playback Pipeline for specific customer")
    parser.add_argument("customer_id", help="Customer ID to process")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use environment variable)")
    
    args = parser.parse_args()
    
    # Check if OpenAI API key is available
    if not args.api_key and not os.getenv('OPENAI_API_KEY'):
        print("❌ OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Run pipeline
    run_pipeline_for_customer(args.customer_id, args.api_key)

if __name__ == "__main__":
    main() 