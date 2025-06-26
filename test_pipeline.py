#!/usr/bin/env python3
"""
Test script for the Chewy Playback Pipeline
Tests the pipeline with a single customer to verify everything works.
"""

import os
import sys
from chewy_playback_pipeline import ChewyPlaybackPipeline


def test_pipeline():
    """Test the pipeline with customer 1183376."""
    
    print("🧪 Testing Chewy Playback Pipeline")
    print("=" * 40)
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipeline()
        
        # Test with customer 1183376
        test_customers = ["1183376"]
        
        print(f"Testing with customer(s): {test_customers}")
        
        # Run pipeline
        pipeline.run_pipeline(customer_ids=test_customers)
        
        print("\n✅ Pipeline test completed successfully!")
        print("📁 Check the 'Output/1183376' directory for results")
        
        # List output files
        output_dir = "Output/1183376"
        if os.path.exists(output_dir):
            print(f"\n📋 Output files in {output_dir}:")
            for file in os.listdir(output_dir):
                file_path = os.path.join(output_dir, file)
                if os.path.isfile(file_path):
                    print(f"  📄 {file}")
                elif os.path.isdir(file_path):
                    print(f"  📁 {file}/")
                    for subfile in os.listdir(file_path):
                        print(f"    📄 {subfile}")
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1) 