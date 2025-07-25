#!/usr/bin/env python3
"""
Breed Predictor Agent Testing Script

This script tests the Breed Predictor Agent with the following requirements:
1. Takes customer ID and enriched pet profile JSON file path as inputs
2. Loads the enriched pet profile
3. Gets order history for that customer
4. Finds dogs with unknown breeds (Breed is "UNK", "Mixed", or empty)
5. Uses confidence scores to select which pet to predict
6. Runs breed prediction only for the selected dog

Usage:
    python test_breed_predictor.py --customer_id 887148270 --profile_path "../../Output/887148270/enriched_pet_profile.json"
    python test_breed_predictor.py --customer_id 887148270  # Will auto-find profile in Output folder
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the current directory to Python path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the breed predictor components
from breed_predictor_agent import BreedPredictorAgent
from predictor import BreedPredictor
from confidence_scorer import ConfidenceScorer

class BreedPredictorTester:
    """
    Testing class for the Breed Predictor Agent with enhanced selection logic.
    """
    
    def __init__(self):
        """Initialize the tester with required components."""
        print("Initializing Breed Predictor Tester...")
        
        try:
            self.breed_agent = BreedPredictorAgent()
            self.predictor = BreedPredictor()
            self.confidence_scorer = ConfidenceScorer()
            print("✓ Breed Predictor Agent initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing Breed Predictor Agent: {e}")
            sys.exit(1)
    
    def load_enriched_pet_profile(self, profile_path: str) -> Dict[str, Any]:
        """Load enriched pet profile from JSON file."""
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Enriched pet profile not found: {profile_path}")
        
        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            
            print(f"✓ Loaded enriched pet profile from {profile_path}")
            print(f"  Found {len(profile_data)} pets in profile")
            
            return profile_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in profile file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading profile: {e}")
    
    def find_profile_path(self, customer_id: str) -> str:
        """Auto-find enriched pet profile path for customer ID."""
        base_paths = [
            f"../../Output/{customer_id}/enriched_pet_profile.json",
            f"../Output/{customer_id}/enriched_pet_profile.json",
            f"Final_Pipeline/Output/{customer_id}/enriched_pet_profile.json"
        ]
        
        for path in base_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(f"Could not find enriched pet profile for customer {customer_id}")
    
    def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get order history for customer using existing agent methods."""
        print(f"  Getting order history for customer {customer_id}...")
        
        try:
            # Use the breed agent's existing method to extract orders
            orders = self.breed_agent.extract_customer_orders(customer_id)
            
            print(f"  ✓ Found {len(orders)} orders for customer {customer_id}")
            
            if orders:
                # Show order statistics
                categories = {}
                for order in orders:
                    category = order.get('category', 'Unknown')
                    categories[category] = categories.get(category, 0) + 1
                
                top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"    Top purchase categories: {', '.join([f'{cat} ({count})' for cat, count in top_categories])}")
            
            return orders
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not get order history: {e}")
            return []
    
    def should_predict_breed_for_pet(self, pet_data: Dict[str, Any]) -> bool:
        """
        Determine if a pet needs breed prediction.
        Requirements:
        - Must be a dog (PetType = "Dog")
        - Breed must be unknown ("UNK", "Mixed", "Unknown", or empty)
        """
        pet_name = pet_data.get('PetName', 'Unknown')
        print(f"🔍 TESTING {pet_name} FOR BREED PREDICTION...")
        
        # Check if it's a dog
        pet_type = pet_data.get('PetType', '').lower()
        print(f"   Pet type: {pet_type}")
        if pet_type != 'dog':
            print(f"   ❌ Not a dog, skipping")
            return False
        
        # Check if breed is unknown
        breed = pet_data.get('Breed', '').strip()
        print(f"   Breed: '{breed}'")
        
        # Handle null/empty breeds
        if not breed:
            print(f"   ✅ Empty breed - QUALIFIES")
            return True
            
        breed_lower = breed.lower()
        print(f"   Breed (lowercase): '{breed_lower}'")
        
        # Exact matches for unknown/mixed breeds
        unknown_indicators = [
            'unk', 'unknown', 'mixed', 'mix', 
            'mixed / unknown', 'unknown / mixed',
            'other', 'null', 'n/a', 'na'
        ]
        
        # Check exact match first
        exact_match = breed_lower in unknown_indicators
        print(f"   Exact match in unknown list: {exact_match}")
        
        if exact_match:
            print(f"   ✅ Exact match - QUALIFIES")
            return True
            
        # Check if breed contains mixed/unknown keywords
        keyword_match = any(keyword in breed_lower for keyword in ['mixed', 'unknown', 'unk'])
        print(f"   Contains unknown keywords: {keyword_match}")
        
        if keyword_match:
            print(f"   ✅ Keyword match - QUALIFIES")
            return True
            
        print(f"   ❌ Known breed - does NOT qualify")
        return False
    
    def calculate_pet_selection_confidence(self, pet_data: Dict[str, Any], orders: List[Dict[str, Any]]) -> float:
        """
        Calculate SELECTION confidence score for choosing which pet to predict.
        This is different from the pet's profile confidence - it includes order history richness.
        This determines which pet to choose for prediction when multiple qualify.
        """
        # Start with existing profile confidence score if available
        profile_confidence = pet_data.get('confidence_score', 0.0) * 100  # Convert to 0-100 scale
        
        # Add bonus for data completeness and order richness
        bonus = 0.0
        
        # Age bonus
        age = pet_data.get('LifeStage', pet_data.get('age', ''))
        if age and str(age).isdigit():
            bonus += 10.0
        
        # Size bonus
        size = pet_data.get('SizeCategory', pet_data.get('size', ''))
        if size and size.upper() != 'UNK':
            bonus += 8.0
        
        # Weight bonus
        weight = pet_data.get('Weight', pet_data.get('weight', ''))
        if weight and str(weight).replace('.', '').isdigit():
            bonus += 7.0
        
        # Gender bonus
        gender = pet_data.get('Gender', pet_data.get('gender', ''))
        if gender and gender.upper() not in ['UNK', 'UNKNOWN']:
            bonus += 5.0
        
        # Order history bonus
        order_count = len(orders)
        if order_count >= 50:
            bonus += 20.0
        elif order_count >= 20:
            bonus += 15.0
        elif order_count >= 10:
            bonus += 10.0
        elif order_count >= 5:
            bonus += 5.0
        
        # Product category diversity bonus
        categories = set()
        for order in orders:
            if isinstance(order, dict):
                categories.add(order.get('category', 'Unknown'))
        categories.discard('Unknown')
        if len(categories) >= 4:
            bonus += 10.0
        elif len(categories) >= 2:
            bonus += 5.0
        
        total_score = profile_confidence + bonus
        return min(total_score, 100.0)  # Cap at 100
    
    def find_best_prediction_candidate(self, pets_data: Dict[str, Any], orders: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the best pet candidate for breed prediction based on requirements:
        1. Must be a dog with unknown breed
        2. Select based on highest confidence score
        """
        candidates = []
        
        print(f"  Analyzing {len(pets_data)} pets for breed prediction candidates...")
        
        for pet_name, pet_data in pets_data.items():
            # Skip non-pet entries (like cust_confidence_score, gets_playback, etc.)
            if not isinstance(pet_data, dict) or 'PetName' not in pet_data:
                continue
                
            print(f"🔍 TESTING {pet_name} FOR BREED PREDICTION...")
            
            if self.should_predict_breed_for_pet(pet_data):
                selection_confidence = self.calculate_pet_selection_confidence(pet_data, orders)
                profile_confidence = pet_data.get('confidence_score', 0.0) * 100
                
                print(f"    ✓ {pet_name} qualifies for prediction:")
                print(f"      Profile confidence: {profile_confidence:.1f}%")
                print(f"      Selection confidence: {selection_confidence:.1f}% (includes order data)")
                
                candidates.append({
                    'name': pet_name,
                    'data': pet_data,
                    'selection_confidence': selection_confidence,
                    'profile_confidence': profile_confidence
                })
            else:
                pet_type = pet_data.get('PetType', 'Unknown').lower()
                breed = pet_data.get('Breed', 'Unknown')
                
                if pet_type != 'dog':
                    print(f"    ✗ {pet_name} - Not a dog")
                else:
                    print(f"    ✗ {pet_name} - Breed already known ({breed})")
        
        if not candidates:
            print("  ⚠ No pets qualify for breed prediction")
            return None
        
        # Sort by selection confidence (highest first)
        candidates.sort(key=lambda x: x['selection_confidence'], reverse=True)
        best_candidate = candidates[0]
        
        print(f"\n  Selected pet for prediction:")
        print(f"    🐕 {best_candidate['name']} (Selection confidence: {best_candidate['selection_confidence']:.1f}%)")
        print(f"    📊 Profile confidence: {best_candidate['profile_confidence']:.1f}%")
        
        pet_data = best_candidate['data']
        breed = pet_data.get('Breed', 'Unknown')
        size = pet_data.get('SizeCategory', pet_data.get('size', 'Unknown'))
        age = pet_data.get('LifeStage', pet_data.get('age', 'Unknown'))
        
        print(f"    📊 Current breed: {breed}")
        print(f"    📏 Size: {size}, Age: {age}")
        
        if len(candidates) > 1:
            skipped_count = len(candidates) - 1
            print(f"    ℹ Skipping {skipped_count} other qualifying pets with lower confidence")
            for candidate in candidates[1:]:
                print(f"      - {candidate['name']} (Selection: {candidate['selection_confidence']:.1f}%)")
        
        return best_candidate
    
    def run_breed_prediction(self, customer_id: str, selected_pet: Dict[str, Any], orders: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Run breed prediction for the selected pet"""
        print(f"\n🧠 Running breed prediction for {selected_pet['name']}...")
        print(f"  Customer ID: {customer_id}")
        print(f"  Order count: {len(orders)}")
        
        try:
            result = self.breed_agent.predict_breed_for_pet_with_orders(
                customer_id=customer_id,
                pet_name=selected_pet['name'],
                pet_data=selected_pet['data'],
                customer_orders=orders
            )
            return result
        except Exception as e:
            print(f"❌ Error during breed prediction: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def display_prediction_results(self, prediction_result: Dict[str, Any]) -> None:
        """Display the breed prediction results in a clear format"""
        print("\n" + "="*60)
        print("🎯 BREED PREDICTION RESULTS")
        print("="*60)
        
        pet_name = prediction_result.get('pet_name', 'Unknown')
        customer_id = prediction_result.get('customer_id', 'Unknown')
        timestamp = prediction_result.get('prediction_timestamp', 'Unknown')
        
        print(f"Pet: {pet_name}")
        print(f"Customer: {customer_id}")
        print(f"Timestamp: {timestamp}")
        
        # Breed distribution
        breed_dist = prediction_result.get('breed_distribution', {})
        if breed_dist:
            # Get top breed
            top_breed = max(breed_dist, key=breed_dist.get)
            top_percentage = breed_dist[top_breed]
            
            print(f"\n🏆 TOP PREDICTION:")
            print(f"   {top_breed} ({top_percentage:.1f}%)")
            
            print(f"\n📊 BREED DISTRIBUTION:")
            sorted_breeds = sorted(breed_dist.items(), key=lambda x: x[1], reverse=True)
            for i, (breed, percentage) in enumerate(sorted_breeds, 1):
                print(f"   {i}. {breed}: {percentage:.1f}%")
            
            # Verify percentages sum to 100%
            total = sum(breed_dist.values())
            if abs(total - 100.0) > 0.1:
                print(f"   ⚠️ Note: Percentages sum to {total:.1f}% (should be 100%)")
        
        # Confidence (LLM-generated prediction confidence)
        confidence = prediction_result.get('confidence', {})
        conf_score = confidence.get('score', 0)
        conf_level = confidence.get('level', 'Unknown')
        conf_source = confidence.get('source', 'Unknown')
        
        print(f"\n🔍 PREDICTION CONFIDENCE:")
        print(f"   Score: {conf_score}/100")
        print(f"   Level: {conf_level}")
        print(f"   Source: {conf_source}")
        
        # Explanations
        explanations = prediction_result.get('explanations', {})
        if explanations:
            print(f"\n💡 BREED EXPLANATIONS:")
            for breed, explanation in explanations.items():
                print(f"   {breed}: {explanation}")
        
        # Data used
        pet_profile = prediction_result.get('pet_profile_used', {})
        if pet_profile:
            print(f"\n📋 DATA USED:")
            print(f"   Age: {pet_profile.get('age', 'Unknown')}")
            print(f"   Size: {pet_profile.get('size', 'Unknown')}")
            print(f"   Gender: {pet_profile.get('gender', 'Unknown')}")
            print(f"   Orders analyzed: {pet_profile.get('order_count', 0)}")
            
            health_indicators = pet_profile.get('health_indicators', [])
            if health_indicators:
                print(f"   Health indicators: {', '.join(health_indicators)}")
        
        print("")
    
    def test_customer(self, customer_id: str, profile_path: Optional[str] = None) -> bool:
        """
        Main testing method for a customer.
        Returns True if prediction was successful, False otherwise.
        """
        print(f"\n{'='*60}")
        print(f"🐕 TESTING BREED PREDICTOR FOR CUSTOMER {customer_id}")
        print(f"{'='*60}")
        
        try:
            # 1. Load enriched pet profile
            if not profile_path:
                profile_path = self.find_profile_path(customer_id)
            
            pets_data = self.load_enriched_pet_profile(profile_path)
            
            # 2. Get customer orders
            orders = self.get_customer_orders(customer_id)
            
            if not orders:
                print("⚠ Warning: No order history found - prediction quality may be limited")
            
            # 3. Find best prediction candidate
            print("📍 Step 3: Finding best prediction candidate...")
            selected_pet = self.find_best_prediction_candidate(pets_data, orders)
            print(f"📍 Step 3 complete. Selected: {selected_pet.get('pet_name') if selected_pet else None}")
            
            if not selected_pet:
                print("❌ No pets qualify for breed prediction")
                print("   All pets are either:")
                print("   - Not dogs, or")
                print("   - Already have known breeds")
                return False
            
            # Step 4: Run breed prediction
            print("📍 Step 4: Running breed prediction...")
            prediction_result = self.run_breed_prediction(customer_id, selected_pet, orders)
            print(f"📍 Step 4 complete. Result: {type(prediction_result)}")
            
            if prediction_result:
                print("✓ Breed prediction completed successfully!")
                
                # Display the results
                self.display_prediction_results(prediction_result)
                return True
            else:
                print("❌ Breed prediction failed")
                return False
                
        except Exception as e:
            print(f"❌ Error testing customer {customer_id}: {e}")
            return False

def main():
    """Main entry point for the testing script."""
    parser = argparse.ArgumentParser(
        description="Test the Breed Predictor Agent with customer data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_breed_predictor.py --customer_id 887148270 --profile_path "../../Output/887148270/enriched_pet_profile.json"
  python test_breed_predictor.py --customer_id 887148270  # Auto-find profile
  python test_breed_predictor.py --customer_id 4760852
        """
    )
    
    parser.add_argument(
        '--customer_id', 
        required=True,
        help='Customer ID to test'
    )
    
    parser.add_argument(
        '--profile_path',
        help='Path to enriched pet profile JSON file (auto-detected if not provided)'
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = BreedPredictorTester()
    
    # Run test
    success = tester.test_customer(args.customer_id, args.profile_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 