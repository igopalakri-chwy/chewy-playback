#!/usr/bin/env python3
"""
Simple example usage of the Review Intelligence Agent
"""

from review_intelligence_agent import ReviewIntelligenceAgent
import os

def main():
    """Example usage of the Review Intelligence Agent."""
    print("🐾 Review Intelligence Agent - Example Usage")
    print("=" * 50)
    
    try:
        # Initialize the agent
        agent = ReviewIntelligenceAgent()
        
        # Process CSV file
        csv_path = "sample_reviews.csv"
        if os.path.exists(csv_path):
            print(f"📝 Processing {csv_path}...")
            results = agent.process_csv_file(csv_path, "output/")
            
            print(f"✅ Successfully processed {len(results)} customers")
            
            # Display summary
            for customer_id, pets_insights in results.items():
                print(f"\n🏠 Customer {customer_id}:")
                for pet_name, insight in pets_insights.items():
                    print(f"   🐕 {pet_name}:")
                    print(f"      Personality: {', '.join(insight.personality_traits[:3])}")
                    print(f"      Activity Level: {insight.activity_level}")
                    print(f"      Sentiment: {insight.overall_sentiment}")
                    print(f"      Confidence: {insight.confidence_score:.2f}")
            
            print(f"\n📁 Customer JSON files saved to output/ directory")
            
        else:
            print(f"❌ CSV file not found: {csv_path}")
            print("Please ensure you have a CSV file with the required columns.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your OpenAI API key and CSV file format.")

if __name__ == "__main__":
    main() 