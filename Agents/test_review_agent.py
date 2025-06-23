#!/usr/bin/env python3
"""
Test script for the Review Intelligence Agent
Demonstrates the agent's capabilities with CSV data processing.
"""

import json
import os
import sys
from pathlib import Path

# Add the current directory to Python path to import the agent
sys.path.append(os.path.dirname(__file__))

from review_intelligence_agent import ReviewIntelligenceAgent

def check_environment_setup():
    """Check if the environment is properly set up."""
    print("🔍 Checking Environment Setup...")
    
    # Check for .env file
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    current_env_file = Path(__file__).parent / '.env'
    
    print(f"📁 Looking for .env file in:")
    print(f"   Project root: {env_file}")
    print(f"   Current directory: {current_env_file}")
    
    if env_file.exists():
        print(f"✅ Found .env file in project root")
    elif current_env_file.exists():
        print(f"✅ Found .env file in current directory")
    else:
        print(f"⚠️ No .env file found")
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        if api_key == 'your-openai-api-key-here':
            print("❌ API key is still set to placeholder value")
            return False
        else:
            print(f"✅ OpenAI API key found (length: {len(api_key)})")
            return True
    else:
        print("❌ OPENAI_API_KEY environment variable not set")
        return False

def test_csv_processing():
    """Test processing of CSV file with customer reviews."""
    print("\n🐾 Testing CSV Processing...")
    
    try:
        # Initialize agent
        agent = ReviewIntelligenceAgent()
        
        # Check if sample CSV exists
        csv_path = "sample_reviews.csv"
        if not os.path.exists(csv_path):
            print(f"❌ Sample CSV file not found: {csv_path}")
            return False
        
        print(f"📝 Processing CSV file: {csv_path}")
        
        # Process CSV file
        results = agent.process_csv_file(csv_path, "output/")
        
        # Display results summary
        print(f"\n✅ CSV processing completed!")
        print(f"📊 Processed {len(results)} customers:")
        
        for customer_id, pets_insights in results.items():
            print(f"   🏠 Customer {customer_id}: {len(pets_insights)} pets")
            for pet_name, insight in pets_insights.items():
                print(f"      🐕 {pet_name}: {insight.confidence_score:.2f} confidence, {insight.overall_sentiment} sentiment")
        
        # Show output file structure
        print(f"\n📁 Generated customer JSON files:")
        output_dir = "output/"
        for customer_id in results.keys():
            safe_customer_id = customer_id.replace('/', '_').replace('\\', '_')
            json_file = f"{safe_customer_id}.json"
            if os.path.exists(os.path.join(output_dir, json_file)):
                print(f"   ✅ {json_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during CSV processing: {e}")
        return False

def test_csv_data_loading():
    """Test loading and grouping of CSV data."""
    print("\n🐾 Testing CSV Data Loading...")
    
    try:
        # Initialize agent
        agent = ReviewIntelligenceAgent()
        
        # Load CSV data
        csv_path = "sample_reviews.csv"
        df = agent.load_reviews_from_csv(csv_path)
        
        print(f"✅ Loaded {len(df)} reviews from CSV")
        print(f"📊 Unique customers: {df['CustomerID'].nunique()}")
        print(f"🐕 Unique pets: {df['Pet_Name'].nunique()}")
        
        # Group reviews
        grouped_reviews = agent.group_reviews_by_customer_and_pet(df)
        
        print(f"📋 Grouped into {len(grouped_reviews)} customers:")
        for customer_id, pets_reviews in grouped_reviews.items():
            print(f"   🏠 Customer {customer_id}: {len(pets_reviews)} pets")
            for pet_name, reviews in pets_reviews.items():
                print(f"      🐕 {pet_name}: {len(reviews)} reviews")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during CSV data loading: {e}")
        return False

def display_sample_output():
    """Display a sample of the expected output format."""
    print("\n📋 Sample Output Format:")
    
    sample_output = {
        "customer_id": "CUST001",
        "analysis_metadata": {
            "total_pets": 2,
            "total_reviews": 7,
            "analysis_timestamp": "2024-01-15T10:30:00",
            "overall_sentiment": "positive",
            "average_confidence": 0.85
        },
        "pets": {
            "Max": {
                "customer_id": "CUST001",
                "pet_name": "Max",
                "personality_traits": ["energetic", "playful", "anxious", "food-motivated"],
                "behavioral_patterns": ["stranger anxiety", "food enthusiasm", "toy engagement"],
                "eating_habits": {
                    "preferences": ["premium food", "interactive feeding"],
                    "timing": "regular mealtimes with enthusiasm",
                    "portion_control": "good",
                    "pickiness_level": "low"
                },
                "play_preferences": ["interactive puzzle toys", "fetch", "mental stimulation"],
                "health_observations": ["improved coat condition", "increased energy", "better digestion"],
                "favorite_products": ["Premium Dog Food", "Interactive Puzzle Toy", "Digestive Probiotic"],
                "emotional_state": {
                    "happiness": 0.85,
                    "anxiety": 0.25,
                    "excitement": 0.80,
                    "calmness": 0.60
                },
                "social_behavior": {
                    "with_humans": "very affectionate and trusting",
                    "with_other_pets": "improving with calming supplements",
                    "stranger_reaction": "initially anxious but improving"
                },
                "training_progress": {
                    "obedience": "good",
                    "house_training": "excellent",
                    "tricks_learned": ["puzzle solving", "calm behavior"]
                },
                "environmental_preferences": ["indoor play", "quiet spaces", "familiar environments"],
                "activity_level": "high",
                "stress_triggers": ["strangers", "loud noises", "unfamiliar situations"],
                "comfort_zones": ["home", "familiar people", "routine activities"],
                "communication_style": "vocal and expressive",
                "relationship_with_owner": "very attached and trusting",
                "seasonal_behaviors": {
                    "summer": ["enjoys outdoor activities", "more active"],
                    "winter": ["prefers indoor play", "cozy activities"],
                    "spring": ["loves walks", "exploring nature"],
                    "fall": ["enjoys outdoor play", "moderate activity"]
                },
                "product_effectiveness": {
                    "Premium Dog Food": {
                        "effectiveness_rating": 0.95,
                        "improvements_noted": ["better coat", "more energy", "improved appetite"],
                        "side_effects": []
                    },
                    "Calming Supplement": {
                        "effectiveness_rating": 0.80,
                        "improvements_noted": ["reduced anxiety", "better social behavior"],
                        "side_effects": []
                    }
                },
                "overall_sentiment": "positive",
                "confidence_score": 0.88,
                "review_count": 4,
                "analysis_timestamp": "2024-01-15T10:30:00"
            }
        },
        "customer_summary": {
            "pet_types": ["Max", "Luna"],
            "personality_diversity": {
                "total_unique_traits": 8,
                "most_common_traits": [["energetic", 1], ["playful", 1]],
                "trait_distribution": {"energetic": 1, "playful": 1}
            },
            "common_health_concerns": [
                ["improved coat condition", 1],
                ["increased energy", 1]
            ],
            "favorite_product_categories": [
                ["Premium Dog Food", 1],
                ["Interactive Puzzle Toy", 1]
            ],
            "overall_activity_level": "high"
        }
    }
    
    print(json.dumps(sample_output, indent=2))

def main():
    """Main test function."""
    print("🧠 Review Intelligence Agent Test Suite")
    print("=" * 50)
    
    # Check environment setup first
    env_ok = check_environment_setup()
    print()
    
    if not env_ok:
        print("❌ Environment not properly configured!")
        print("\n📝 To fix this:")
        print("1. Create a .env file in the project root with:")
        print("   OPENAI_API_KEY=your-actual-api-key-here")
        print("2. Make sure you have installed the requirements:")
        print("   pip install -r requirements.txt")
        print("3. Run this test again")
        return
    
    # Display sample output
    display_sample_output()
    
    # Test CSV data loading
    csv_loading_success = test_csv_data_loading()
    
    # Test CSV processing
    csv_processing_success = test_csv_processing()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"CSV Data Loading: {'✅ PASS' if csv_loading_success else '❌ FAIL'}")
    print(f"CSV Processing: {'✅ PASS' if csv_processing_success else '❌ FAIL'}")
    
    if csv_loading_success and csv_processing_success:
        print("\n🎉 All tests passed! The Review Intelligence Agent is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 