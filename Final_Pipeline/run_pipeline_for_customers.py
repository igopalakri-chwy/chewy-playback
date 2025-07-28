#!/usr/bin/env python3
"""
Script to run the Chewy Playback Pipeline for customer IDs from a text file.
Outputs will be saved to the Output_Chewy_People directory.
"""

import os
import sys
from pathlib import Path
from chewy_playback_pipeline import ChewyPlaybackPipeline

def read_customer_ids(file_path: str) -> list:
    """Read customer IDs from a text file."""
    customer_ids = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    customer_ids.append(line)
        print(f"✅ Read {len(customer_ids)} customer IDs from {file_path}")
        return customer_ids
    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found")
        return []
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return []

def main():
    """Main function to run the pipeline for customer IDs from file."""
    
    # Path to the customer IDs file
    customer_ids_file = "cust_ids_chewy.txt"
    
    # Check if the file exists
    if not os.path.exists(customer_ids_file):
        print(f"❌ Error: {customer_ids_file} not found in current directory")
        print("Please make sure the file is in the same directory as this script")
        sys.exit(1)
    
    # Read customer IDs
    customer_ids = read_customer_ids(customer_ids_file)
    
    if not customer_ids:
        print("❌ No customer IDs found. Exiting.")
        sys.exit(1)
    
    print(f"📋 Customer IDs to process: {customer_ids}")
    
    try:
        # Initialize pipeline
        print("🚀 Initializing Chewy Playback Pipeline...")
        pipeline = ChewyPlaybackPipeline()
        
        # Override the output directory to use Output_Chewy_People
        pipeline.output_dir = Path(__file__).parent / "Output_Chewy_People"
        pipeline.output_dir.mkdir(exist_ok=True)
        
        print(f"📁 Output will be saved to: {pipeline.output_dir}")
        
        # Run pipeline for the customer IDs
        print(f"🎯 Running pipeline for {len(customer_ids)} customers...")
        pipeline.run_pipeline(customer_ids=customer_ids)
        
        print("✅ Pipeline completed successfully!")
        print(f"📁 Check the 'Output_Chewy_People' directory for results")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 