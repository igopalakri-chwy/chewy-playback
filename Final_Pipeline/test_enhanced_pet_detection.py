#!/usr/bin/env python3
"""
Test script for the enhanced pet detection system.
This tests the LLM-based pet count detection with hashmap approach.
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add the agent directory to path
sys.path.append(str(Path(__file__).parent / 'Agents/Review_and_Order_Intelligence_Agent'))

# Mock data for testing
def create_test_data():
    """Create test data for the enhanced pet detection system."""
    
    # Sample known pet profiles (from Snowflake)
    known_pet_profiles = [
        {
            'PetName': 'Fluffy',
            'PetType': 'cat',
            'PetBreed': 'Persian',
            'Gender': 'FEMALE',
            'PetAge': 'adult',
            'Weight': '12 lbs',
            'Birthday': 'UNK'
        },
        {
            'PetName': 'Whiskers',
            'PetType': 'cat', 
            'PetBreed': 'Maine Coon',
            'Gender': 'MALE',
            'PetAge': 'adult',
            'Weight': '15 lbs',
            'Birthday': 'UNK'
        }
    ]
    
    # Sample reviews that mention additional pets and named pets
    reviews_data = [
        {
            'ReviewText': 'My 3 cats absolutely love this food! Fluffy and Whiskers always finish their bowls first.',  # Count-based: 3 cats vs 2 known
            'CustomerID': '12345',
            'PetName': 'Fluffy'
        },
        {
            'ReviewText': 'Charlie loves this new toy! He plays with it every day.',  # Named pet: Charlie (not in profiles)
            'CustomerID': '12345',
            'PetName': 'Whiskers'
        },
        {
            'ReviewText': 'My dog really enjoys these treats. Great quality!',  # Unnamed species: dog (no dogs in profiles)
            'CustomerID': '12345',
            'PetName': None
        },
        {
            'ReviewText': 'Bella and Max both love this food. All three of my cats enjoy this treat.',  # Multiple named pets + count
            'CustomerID': '12345', 
            'PetName': None
        },
        {
            'ReviewText': 'Perfect litter for my cats. I have 3 indoor cats and this works great.',  # Count confirmation
            'CustomerID': '12345',
            'PetName': None
        }
    ]
    
    return known_pet_profiles, pd.DataFrame(reviews_data)

def test_enhanced_pet_detection():
    """Test the enhanced pet detection system."""
    print("🧪 Testing Enhanced Pet Detection System")
    print("=" * 50)
    
    try:
        from review_order_intelligence_agent import ReviewOrderIntelligenceAgent
        
        # Create test data
        known_pets, reviews_df = create_test_data()
        
        # Initialize agent (requires OpenAI API key)
        agent = ReviewOrderIntelligenceAgent()
        
        print(f"📊 Test Setup:")
        print(f"   Known pets from Snowflake: {len(known_pets)}")
        print(f"   Reviews to analyze: {len(reviews_df)}")
        print()
        
        # Test the enhanced pet detection
        print("🔍 Running enhanced pet detection...")
        pet_detection_result = agent._get_customer_pets_from_reviews(reviews_df, known_pets)
        
        print("✅ Results:")
        print(f"   All pet names found: {pet_detection_result['pet_names']}")
        print()
        
        # Display pet count analysis
        analysis = pet_detection_result['pet_count_analysis']
        print("📈 Pet Count Analysis:")
        print(f"   Original counts: {analysis['original_counts']}")
        print(f"   Detected counts: {analysis['detected_counts']}")
        print(f"   Updated counts: {analysis['updated_counts']}")
        print(f"   Additional pets: {len(analysis['additional_pets'])}")
        print()
        
        if analysis['additional_pets']:
            print("🆕 Additional Pets Detected:")
            for pet in analysis['additional_pets']:
                print(f"   - {pet['name']} ({pet['type']}) - Source: {pet['source']}")
        
        print("\n✅ Enhanced pet detection test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the Final_Pipeline directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_enhanced_pet_detection()