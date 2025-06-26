#!/usr/bin/env python3
"""
Simple script to run the confidence score calculator on the output file.
"""

import sys
import os

# Add agent directory to path
sys.path.append('Agents/Review_and_Order_Intelligence_Agent')

from add_confidence_score import ConfidenceScoreCalculator

def main():
    """Run confidence score calculator on the output file."""
    print("🎯 Running Confidence Score Calculator")
    print("=" * 40)
    
    # Path to the output file
    output_file = "Output/1183376/enriched_pet_profile.json"
    
    if os.path.exists(output_file):
        print(f"Processing file: {output_file}")
        
        calculator = ConfidenceScoreCalculator()
        success = calculator.process_json_file(output_file)
        
        if success:
            print("✅ Successfully added confidence scores!")
            
            # Show the results
            import json
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            print("\n📊 Confidence Scores:")
            
            # Check if this is the direct structure (pet_name -> data)
            if any(isinstance(value, dict) and 'PetType' in value for value in data.values()):
                # Show pet confidence scores
                for pet_name, pet_data in data.items():
                    if isinstance(pet_data, dict) and 'confidence_score' in pet_data:
                        print(f"  {pet_name}: {pet_data['confidence_score']:.3f}")
                
                # Show customer confidence score
                if 'cust_confidence_score' in data:
                    print(f"\n🏠 Customer Confidence Score: {data['cust_confidence_score']:.3f}")
            else:
                # Show for nested structure (customer_id -> pets)
                for customer_id, customer_pets in data.items():
                    if isinstance(customer_pets, dict):
                        print(f"\nCustomer {customer_id}:")
                        for pet_name, pet_data in customer_pets.items():
                            if isinstance(pet_data, dict) and 'confidence_score' in pet_data:
                                print(f"  {pet_name}: {pet_data['confidence_score']:.3f}")
                        
                        if 'cust_confidence_score' in customer_pets:
                            print(f"  Customer Confidence: {customer_pets['cust_confidence_score']:.3f}")
        else:
            print("❌ Failed to add confidence scores")
    else:
        print(f"❌ File not found: {output_file}")

if __name__ == "__main__":
    main() 