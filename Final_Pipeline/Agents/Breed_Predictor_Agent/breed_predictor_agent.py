#!/usr/bin/env python3
"""
Breed Predictor Agent for Final Pipeline
Integrates the breed prediction system to predict dog breeds for pets with unknown/mixed breeds.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from predictor import BreedPredictor
    from confidence_scorer import ConfidenceScorer
except ImportError as e:
    print(f"Warning: Could not import breed predictor modules: {e}")
    BreedPredictor = None
    ConfidenceScorer = None


class BreedPredictorAgent:
    """
    Agent that predicts dog breeds for pets with unknown or mixed breeds.
    Only activates for dogs with unknown/mixed breeds in the enriched pet profile.
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the Breed Predictor Agent."""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required for Breed Predictor Agent")
        
        # Initialize the breed predictor
        if BreedPredictor:
            try:
                self.predictor = BreedPredictor()
                self.available = True
            except Exception as e:
                print(f"Warning: Could not initialize BreedPredictor: {e}")
                self.available = False
        else:
            self.available = False
    
    def should_predict_breed(self, pet_data: Dict[str, Any]) -> bool:
        """
        Determine if breed prediction should be performed for this pet.
        Only predicts for dogs with unknown or mixed breeds.
        """
        import re
        # Check if pet is a dog
        pet_type = pet_data.get('PetType', pet_data.get('type', '')).lower()
        if pet_type not in ['dog', 'dogs', 'canine']:
            return False
        
        # Check if breed is unknown or mixed (robust to slashes, spaces, etc.)
        breed = pet_data.get('Breed', pet_data.get('breed', '')).lower()
        # Replace non-alphabetic characters with spaces
        breed_clean = re.sub(r'[^a-z]', ' ', breed)
        unknown_indicators = ['unknown', 'unk', 'mixed', 'mix', 'mutt', 'other', '']
        return any(indicator in breed_clean.split() for indicator in unknown_indicators)
    
    def extract_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Extract order data for a specific customer from the pipeline's data sources.
        Now uses Snowflake data instead of CSV files.
        """
        order_data = []
        
        # Try to get order data from the pipeline's Snowflake connector
        try:
            # Import the pipeline's Snowflake connector
            from chewy_playback_pipeline import ChewyPlaybackPipeline
            
            # Create a temporary pipeline instance to access Snowflake data
            pipeline = ChewyPlaybackPipeline()
            
            # Get customer orders from Snowflake
            orders_df = pipeline._get_cached_customer_orders_dataframe(customer_id)
            
            if not orders_df.empty:
                # Convert to list of dictionaries
                for _, row in orders_df.iterrows():
                    order = {
                        'item_name': row.get('ProductName', 'Unknown'),
                        'category': 'Unknown',
                        'order_date': '',
                        'quantity': row.get('Quantity', 1),
                        'brand': 'Chewy'
                    }
                    order_data.append(order)
                
                print(f"    📊 Found {len(order_data)} orders from Snowflake for customer {customer_id}")
            else:
                print(f"    ⚠️ No order data found in Snowflake for customer {customer_id}")
                
        except Exception as e:
            print(f"    ⚠️ Could not get Snowflake data for customer {customer_id}: {e}")
            
            # Fallback to CSV files if Snowflake fails
        order_files = [
            "Data/zero_reviews.csv",
            "Data/processed_orderhistory.csv", 
            "Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv"
        ]
        
        for order_file in order_files:
            if os.path.exists(order_file):
                try:
                    df = pd.read_csv(order_file)
                    
                    # Check for customer ID in different column formats
                    customer_col = None
                    for col in ['CustomerID', 'CUSTOMER_ID', 'customer_id']:
                        if col in df.columns:
                            customer_col = col
                            break
                    
                    if customer_col:
                        customer_orders = df[df[customer_col].astype(str) == str(customer_id)]
                        
                        if not customer_orders.empty:
                            # Convert to list of dictionaries
                            for _, row in customer_orders.iterrows():
                                order = {
                                    'item_name': row.get('ProductName', row.get('item_name', row.get('ITEM_NAME', 'Unknown'))),
                                    'category': 'Unknown',
                                    'order_date': row.get('OrderDate', row.get('order_date', row.get('ORDER_DATE', ''))),
                                    'quantity': row.get('Quantity', row.get('quantity', 1)),
                                    'brand': row.get('Brand', row.get('brand', 'Chewy'))
                                }
                                order_data.append(order)
                            
                            break  # Use first file that has data
                            
                except Exception as e:
                    print(f"Error reading {order_file}: {e}")
                    continue
        
        return order_data
    
    def create_pet_profile_for_prediction(self, pet_data: Dict[str, Any], 
                                        customer_orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a pet profile in the format expected by the breed predictor.
        """
        # Extract basic pet information
        pet_profile = {
            'name': pet_data.get('PetName', pet_data.get('name', 'Unknown')),
            'age': pet_data.get('LifeStage', pet_data.get('age', 'Unknown')),
            'size': pet_data.get('SizeCategory', pet_data.get('size', 'Unknown')),
            'gender': pet_data.get('Gender', pet_data.get('gender', 'Unknown')),
            'purchase_history': customer_orders,
            'health_indicators': []
        }
        
        # Extract health indicators from pet data if available
        if 'PersonalityTraits' in pet_data:
            traits = pet_data['PersonalityTraits']
            if isinstance(traits, list):
                pet_profile['health_indicators'].extend(traits)
        
        if 'BehavioralCues' in pet_data:
            cues = pet_data['BehavioralCues']
            if isinstance(cues, list):
                pet_profile['health_indicators'].extend(cues)
        
        return pet_profile
    
    def predict_breed_for_pet(self, customer_id: str, pet_name: str, 
                            pet_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Predict breed for a specific pet if conditions are met.
        Returns None if prediction is not needed or failed.
        """
        if not self.available:
            print(f"    ⚠️ Breed Predictor not available for {pet_name}")
            return None
        
        # Check if breed prediction is needed
        if not self.should_predict_breed(pet_data):
            print(f"    ℹ️ No breed prediction needed for {pet_name} (not a dog or breed known)")
            return None
        
        print(f"    🐕 Predicting breed for {pet_name} (unknown/mixed breed dog)...")
        
        try:
            # Extract customer orders
            customer_orders = self.extract_customer_orders(customer_id)
            
            if not customer_orders:
                print(f"    ⚠️ No order data found for customer {customer_id}")
                return None
            
            # Create pet profile for prediction
            pet_profile = self.create_pet_profile_for_prediction(pet_data, customer_orders)
            
            # Use the breed predictor's LLM analysis directly
            distribution, confidence_result, explanations = self._get_llm_predictions_direct(
                pet_profile, customer_orders
            )
            
            # Format the results
            prediction_result = {
                'customer_id': customer_id,
                'pet_name': pet_name,
                'prediction_timestamp': pd.Timestamp.now().isoformat(),
                'breed_distribution': distribution,
                'confidence': {
                    'score': confidence_result.get('confidence_score', 0),
                    'level': confidence_result.get('confidence_level', 'Unknown'),
                    'reliability_flags': confidence_result.get('reliability_flags', []),
                    'recommendations': confidence_result.get('recommendations', [])
                },
                'explanations': explanations,
                'pet_profile_used': {
                    'age': pet_profile.get('age'),
                    'size': pet_profile.get('size'),
                    'gender': pet_profile.get('gender'),
                    'order_count': len(customer_orders),
                    'health_indicators': pet_profile.get('health_indicators', [])
                }
            }
            
            # Get top breed
            if distribution:
                top_breed = max(distribution.items(), key=lambda x: x[1])
                prediction_result['top_predicted_breed'] = {
                    'breed': top_breed[0],
                    'percentage': top_breed[1]
                }
            
            print(f"    ✅ Breed prediction completed for {pet_name}")
            if 'top_predicted_breed' in prediction_result:
                top = prediction_result['top_predicted_breed']
                print(f"    🏆 Top prediction: {top['breed']} ({top['percentage']:.1f}%)")
            
            return prediction_result
            
        except Exception as e:
            print(f"    ❌ Error predicting breed for {pet_name}: {e}")
            return None
    
    def predict_breed_for_pet_with_orders(self, customer_id: str, pet_name: str, 
                                        pet_data: Dict[str, Any],
                                        customer_orders: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Predict breed for a specific pet if conditions are met, using provided order data.
        Returns None if prediction is not needed or failed.
        """
        if not self.available:
            print(f"    ⚠️ Breed Predictor not available for {pet_name}")
            return None
        
        # Check if breed prediction is needed
        if not self.should_predict_breed(pet_data):
            print(f"    ℹ️ No breed prediction needed for {pet_name} (not a dog or breed known)")
            return None
        
        print(f"    🐕 Predicting breed for {pet_name} (unknown/mixed breed dog)...")
        
        try:
            if not customer_orders:
                print(f"    ⚠️ No order data provided for customer {customer_id}")
                return None
            
            # Create pet profile for prediction
            pet_profile = self.create_pet_profile_for_prediction(pet_data, customer_orders)
            
            # Use the breed predictor's LLM analysis directly
            distribution, confidence_result, explanations = self._get_llm_predictions_direct(
                pet_profile, customer_orders
            )
            
            # Format the results
            prediction_result = {
                'customer_id': customer_id,
                'pet_name': pet_name,
                'prediction_timestamp': pd.Timestamp.now().isoformat(),
                'breed_distribution': distribution,
                'confidence': {
                    'score': confidence_result.get('confidence_score', 0),
                    'level': confidence_result.get('confidence_level', 'Unknown'),
                    'reliability_flags': confidence_result.get('reliability_flags', []),
                    'recommendations': confidence_result.get('recommendations', [])
                },
                'explanations': explanations,
                'pet_profile_used': {
                    'age': pet_profile.get('age'),
                    'size': pet_profile.get('size'),
                    'gender': pet_profile.get('gender'),
                    'order_count': len(customer_orders),
                    'health_indicators': pet_profile.get('health_indicators', [])
                }
            }
            
            # Get top breed
            if distribution:
                top_breed = max(distribution.items(), key=lambda x: x[1])
                prediction_result['top_predicted_breed'] = {
                    'breed': top_breed[0],
                    'percentage': top_breed[1]
                }
            
            print(f"    ✅ Breed prediction completed for {pet_name}")
            if 'top_predicted_breed' in prediction_result:
                top = prediction_result['top_predicted_breed']
                print(f"    🏆 Top prediction: {top['breed']} ({top['percentage']:.1f}%)")
            
            return prediction_result
            
        except Exception as e:
            print(f"    ❌ Error predicting breed for {pet_name}: {e}")
            return None
    
    def _get_llm_predictions_direct(self, pet_profile: Dict[str, Any], 
                                  purchase_history: List[Dict[str, Any]]) -> tuple:
        """
        Get breed predictions directly using LLM analysis of pipeline data.
        Returns (distribution, confidence_result, explanations)
        """
        try:
            # Extract health indicators from purchase data
            health_indicators = self._extract_health_indicators_from_purchases(purchase_history)
            existing_indicators = pet_profile.get('health_indicators', [])
            all_health_indicators = list(set(health_indicators + existing_indicators))
            
            # Get breed list from breed definitions
            breed_list = list(self.predictor.breed_definitions.keys())
            breed_profiles = self.predictor._create_breed_health_profile()
            
            # Create comprehensive prompt for LLM
            prompt = self.predictor._create_prediction_prompt(
                pet_profile, purchase_history, all_health_indicators, breed_list, breed_profiles
            )
            
            # Call OpenAI API
            response = self.predictor.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert dog breed analyst with extensive knowledge of breed characteristics, health predispositions, and typical care requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            distribution = self.predictor._parse_breed_distribution(result, breed_list)
            
            # Generate explanations for top breeds
            explanations = self.predictor._generate_breed_explanations(
                distribution, pet_profile, purchase_history, all_health_indicators
            )
            
            # Calculate confidence score
            confidence_result = self.predictor.confidence_scorer.calculate_confidence(
                pet_profile, purchase_history, distribution
            )
            
            return distribution, confidence_result, explanations
            
        except Exception as e:
            print(f"    ⚠️ LLM prediction failed, using fallback: {e}")
            # Use fallback prediction
            breed_list = list(self.predictor.breed_definitions.keys())
            distribution = self.predictor._fallback_prediction(pet_profile, [], breed_list)
            explanations = {}
            confidence_result = {
                'confidence_score': 20,
                'confidence_level': 'Low',
                'reliability_flags': ['LLM prediction failed'],
                'recommendations': ['Consider manual breed assessment']
            }
            return distribution, confidence_result, explanations
    
    def _extract_health_indicators_from_purchases(self, purchase_history: List[Dict[str, Any]]) -> List[str]:
        """Extract health-related keywords from purchase history."""
        health_keywords = {
            'joint': ['joint', 'arthritis', 'hip', 'elbow', 'mobility', 'orthopedic', 'glucosamine', 'chondroitin'],
            'digestive': ['grain-free', 'sensitive', 'digestive', 'probiotic', 'stomach', 'limited ingredient'],
            'skin': ['skin', 'coat', 'shampoo', 'grooming', 'allergy', 'hypoallergenic'],
            'dental': ['dental', 'teeth', 'breath', 'oral', 'tartar', 'plaque', 'bully stick'],
            'urinary': ['bladder', 'kidney', 'urinary', 'cranberry', 'incontinence'],
            'size': ['small', 'large', 'big', 'tiny', 'medium'],
            'energy': ['toy', 'exercise', 'play', 'fetch', 'smart', 'intelligent'],
            'age': ['senior', 'puppy', 'young', 'old', 'aging']
        }
        
        indicators = []
        
        for purchase in purchase_history:
            combined_text = f"{purchase.get('item_name', '')} {purchase.get('item_desc', '')} {purchase.get('category', '')}".lower()
            
            for category, keywords in health_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        indicators.append(f"{category}:{keyword}")
                        
        return list(set(indicators))  # Remove duplicates
    
    def process_customer_pets(self, customer_id: str, 
                            enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all pets for a customer and predict breeds where needed.
        """
        if not self.available:
            return {}
        
        print(f"  🐕 Running Breed Predictor Agent for customer {customer_id}...")
        
        predictions = {}
        
        # Handle different data structures
        if isinstance(enriched_profiles, dict) and 'pets' in enriched_profiles:
            pets_data = enriched_profiles['pets']
        else:
            pets_data = enriched_profiles
        
        # Process each pet
        for pet_name, pet_data in pets_data.items():
            prediction = self.predict_breed_for_pet(customer_id, pet_name, pet_data)
            if prediction:
                predictions[pet_name] = prediction
        
        if predictions:
            print(f"    ✅ Breed predictions completed for {len(predictions)} pets")
        else:
            print(f"    ℹ️ No breed predictions needed for customer {customer_id}")
        
        return predictions
    
    def process_customer_pets_with_orders(self, customer_id: str, 
                                        enriched_profiles: Dict[str, Any],
                                        customer_orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process pets for a customer and predict breed for the most suitable pet.
        New logic:
        - If no pets have unknown/mixed breeds, skip prediction
        - If one pet has unknown/mixed breed, predict for that pet
        - If multiple pets have unknown/mixed breeds, choose the one with highest confidence score
        """
        if not self.available:
            return {}
        
        print(f"  🐕 Running Breed Predictor Agent for customer {customer_id}...")
        
        # Handle different data structures
        if isinstance(enriched_profiles, dict) and 'pets' in enriched_profiles:
            pets_data = enriched_profiles['pets']
        else:
            pets_data = enriched_profiles
        
        # Find pets that need breed prediction
        pets_needing_prediction = []
        
        for pet_name, pet_data in pets_data.items():
            if self.should_predict_breed(pet_data):
                # Calculate confidence score for this pet
                confidence_score = self._calculate_pet_confidence_score(pet_data, customer_orders)
                pets_needing_prediction.append({
                    'pet_name': pet_name,
                    'pet_data': pet_data,
                    'confidence_score': confidence_score
                })
        
        # Apply new logic
        if not pets_needing_prediction:
            print(f"    ℹ️ No breed prediction needed for customer {customer_id} (no unknown/mixed breeds)")
            return {}
        
        elif len(pets_needing_prediction) == 1:
            # Only one pet needs prediction
            selected_pet = pets_needing_prediction[0]
            print(f"    🐕 Predicting breed for {selected_pet['pet_name']} (only pet with unknown breed)")
            
        else:
            # Multiple pets need prediction - choose the one with highest confidence
            selected_pet = max(pets_needing_prediction, key=lambda x: x['confidence_score'])
            print(f"    🐕 Predicting breed for {selected_pet['pet_name']} (highest confidence: {selected_pet['confidence_score']:.1f})")
            print(f"    ℹ️ Skipping {len(pets_needing_prediction) - 1} other pets with unknown breeds")
        
        # Predict breed for the selected pet
        prediction = self.predict_breed_for_pet_with_orders(
            customer_id, 
            selected_pet['pet_name'], 
            selected_pet['pet_data'], 
            customer_orders
        )
        
        if prediction:
            # Convert to simplified format
            simplified_prediction = self._convert_to_simplified_format(
                customer_id, 
                selected_pet['pet_name'], 
                prediction
            )
            print(f"    ✅ Breed prediction completed for {selected_pet['pet_name']}")
            return simplified_prediction
        else:
            print(f"    ❌ Failed to predict breed for {selected_pet['pet_name']}")
            return {}
    
    def _calculate_pet_confidence_score(self, pet_data: Dict[str, Any], customer_orders: List[Dict[str, Any]]) -> float:
        """
        Calculate a confidence score for breed prediction based on available data.
        Higher scores indicate more reliable predictions.
        """
        score = 0.0
        
        # Base score for having order data
        if customer_orders:
            score += 20.0
        
        # Score for order count (more orders = more data)
        order_count = len(customer_orders)
        if order_count >= 50:
            score += 30.0
        elif order_count >= 20:
            score += 20.0
        elif order_count >= 10:
            score += 10.0
        
        # Score for having pet age
        pet_age = pet_data.get('PetAge', pet_data.get('age', ''))
        if pet_age and str(pet_age).isdigit():
            score += 15.0
        
        # Score for having pet size
        pet_size = pet_data.get('Size', pet_data.get('size', ''))
        if pet_size and pet_size != 'UNK':
            score += 10.0
        
        # Score for having gender
        pet_gender = pet_data.get('Gender', pet_data.get('gender', ''))
        if pet_gender:
            score += 5.0
        
        # Score for having weight
        pet_weight = pet_data.get('Weight', pet_data.get('weight', ''))
        if pet_weight and str(pet_weight).isdigit():
            score += 10.0
        
        # Score for diverse order categories (more categories = better data)
        categories = set()
        for order in customer_orders:
            category = order.get('category', 'Unknown')
            if category != 'Unknown':
                categories.add(category)
        
        if len(categories) >= 5:
            score += 10.0
        elif len(categories) >= 3:
            score += 5.0
        
        return min(score, 100.0)  # Cap at 100
    
    def _convert_to_simplified_format(self, customer_id: str, pet_name: str, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert the detailed prediction format to the simplified format requested.
        """
        # Get the top predicted breed
        breed_distribution = prediction.get('breed_distribution', {})
        if not breed_distribution:
            return {}
        
        # Find the breed with highest percentage
        top_breed = max(breed_distribution.items(), key=lambda x: x[1])
        
        # Get confidence score
        confidence_data = prediction.get('confidence', {})
        confidence_score = confidence_data.get('score', 0)
        
        # Convert breed name to readable format
        breed_name = top_breed[0].replace('_', ' ').title()
        
        return {
            "customer_id": customer_id,
            "pet_name": pet_name,
            "predicted_breed": breed_name,
            "confidence": confidence_score
        }


def main():
    """Test the Breed Predictor Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Breed Predictor Agent')
    parser.add_argument('customer_id', help='Customer ID to test')
    parser.add_argument('--api-key', help='OpenAI API key')
    
    args = parser.parse_args()
    
    try:
        agent = BreedPredictorAgent(openai_api_key=args.api_key)
        print("✅ Breed Predictor Agent initialized successfully")
        
        # This would need actual data to test
        print("Note: This is a test of the agent initialization only.")
        print("For full testing, use within the Final Pipeline.")
        
    except Exception as e:
        print(f"❌ Error initializing Breed Predictor Agent: {e}")


if __name__ == "__main__":
    main() 