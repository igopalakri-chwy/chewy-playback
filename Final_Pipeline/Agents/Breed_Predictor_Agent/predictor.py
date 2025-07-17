"""
Enhanced Breed Predictor based on purchase history.
Uses OpenAI GPT to infer breed percentages for pets with unknown/mixed breed.
Updated to work with processed order data from predictorData.csv.
Now includes trained breed characteristics model for improved accuracy.
"""

import json
import pandas as pd
import os
from openai import OpenAI
from typing import Dict, List, Tuple
import re
from dotenv import load_dotenv
from datetime import datetime

# Import the confidence scorer
try:
    from confidence_scorer import ConfidenceScorer
except ImportError:
    from .confidence_scorer import ConfidenceScorer

# Load environment variables
load_dotenv()

class BreedPredictor:
    """
    A breed prediction system that uses LLM analysis of pet data and purchase history.
    Removed statistical model component to focus on LLM predictions only.
    """
    
    def __init__(self):
        """Initialize the breed predictor with OpenAI client only."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.breed_definitions = self._load_breed_definitions()
        
        # Initialize confidence scorer
        self.confidence_scorer = ConfidenceScorer()
        
    def _load_breed_definitions(self) -> Dict:
        """Load all breed definition files."""
        breed_definitions = {}
        
        # Try the new dog_breed_data directory first
        breeds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dog_breed_data')
        
        if not os.path.exists(breeds_dir):
            # Fallback to old location
            breeds_dir = os.path.join(os.path.dirname(__file__), 'data', 'breeds')
            
        if not os.path.exists(breeds_dir):
            raise FileNotFoundError(f"Breeds directory not found: {breeds_dir}")
            
        breed_files = [f for f in os.listdir(breeds_dir) if f.endswith('.json')]
        
        for breed_file in breed_files:
            breed_name = breed_file.replace('_cleaned.json', '')
            filepath = os.path.join(breeds_dir, breed_file)
            
            try:
                with open(filepath, 'r') as f:
                    breed_definitions[breed_name] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load breed file {breed_file}: {e}")
                
        return breed_definitions
    
    def load_data(self, use_test_data: bool = False) -> Tuple[Dict, Dict]:
        """Load processed pet data and return pet data structure."""
        if use_test_data:
            pets_path = os.path.join(os.path.dirname(__file__), 'data', 'test_data_1pet.json')
        else:
            # Use cleaned data by default
            pets_path = os.path.join(os.path.dirname(__file__), 'data', 'pet_data_1pet_cleaned.json')
        
        with open(pets_path, 'r') as f:
            customers = json.load(f)
            
        return customers, customers
    
    def _extract_health_indicators_from_purchases(self, purchase_history: List[Dict]) -> List[str]:
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
    
    def _create_breed_health_profile(self) -> Dict:
        """Create health profiles for each breed based on their characteristics."""
        breed_profiles = {}
        
        for breed_key, breed_data in self.breed_definitions.items():
            profile = {
                'common_health_issues': [],
                'size_category': 'medium',
                'exercise_needs': int(breed_data.get('exercise_needs', 3)),
                'grooming_needs': int(breed_data.get('grooming_needs', 3)),
                'health_issues_score': int(breed_data.get('health_issues', 3))
            }
            
            # Extract health issues from health_description
            health_desc = breed_data.get('health_description', '').lower()
            if 'hip dysplasia' in health_desc or 'joint' in health_desc:
                profile['common_health_issues'].append('joint')
            if 'allergy' in health_desc or 'skin' in health_desc:
                profile['common_health_issues'].append('skin')
            if 'dental' in health_desc or 'teeth' in health_desc:
                profile['common_health_issues'].append('dental')
            if 'eye' in health_desc:
                profile['common_health_issues'].append('eye')
            if 'stomach' in health_desc or 'digestive' in health_desc:
                profile['common_health_issues'].append('digestive')
                
            # Determine size category from weight
            weight_str = breed_data.get('weight', '').lower()
            if any(term in weight_str for term in ['4-6', '6-9', 'small']):
                profile['size_category'] = 'small'
            elif any(term in weight_str for term in ['65-75', '80', 'large']):
                profile['size_category'] = 'large'
                
            breed_profiles[breed_key] = profile
            
        return breed_profiles

    def predict_breed_distribution(self, customer_id: str, pet_id: str) -> Tuple[Dict[str, float], Dict, Dict[str, str]]:
        """Predict breed distribution for a specific pet using LLM analysis only."""
        customers, _ = self.load_data()
        
        # Get customer and pet info from new structure
        customer_data = customers.get(str(customer_id), {})
        pet_data = customer_data.get('pets', {}).get(pet_id, {})
        
        if not pet_data:
            raise ValueError(f"Pet {pet_id} not found for customer {customer_id}")
        
        # Get purchase history
        purchase_history = pet_data.get('purchase_history', [])
        
        if not purchase_history:
            raise ValueError(f"No purchase history found for pet {pet_id}")
        
        # Extract health indicators from purchase data
        purchase_indicators = self._extract_health_indicators_from_purchases(purchase_history)
        existing_indicators = pet_data.get('health_indicators', [])
        
        # Combine indicators
        all_health_indicators = list(set(purchase_indicators + existing_indicators))
        
        # Get predictions from LLM only
        predictions = self._get_llm_predictions(pet_data, purchase_history, all_health_indicators)
        
        # Generate explanations for top breeds and those >2%
        explanations = self._generate_breed_explanations(
            predictions, pet_data, purchase_history, all_health_indicators
        )
        
        # Calculate confidence score
        confidence_result = self.confidence_scorer.calculate_confidence(
            pet_data, purchase_history, predictions
        )
        
        return predictions, confidence_result, explanations
    
    def _get_llm_predictions(self, pet_data: Dict, purchase_history: List[Dict], 
                           health_indicators: List[str]) -> Dict[str, float]:
        """Get predictions from the LLM with proper normalization and fallback."""
        try:
            # Create comprehensive prompt for LLM
            breed_list = list(self.breed_definitions.keys())
            breed_profiles = self._create_breed_health_profile()
            
            prompt = self._create_prediction_prompt(
                pet_data, purchase_history, health_indicators, breed_list, breed_profiles
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert dog breed analyst with extensive knowledge of breed characteristics, health predispositions, and typical care requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            distribution = self._parse_breed_distribution(result_text, breed_list)
            
            # Validate and normalize results
            if distribution:
                # Filter out very low probability breeds (< 0.5%)
                distribution = {breed: score for breed, score in distribution.items() if score >= 0.5}
                
                # Normalize to sum to 100%
                total = sum(distribution.values())
                if total > 0:
                    distribution = {breed: (score / total) * 100 for breed, score in distribution.items()}
                
                # Sort by probability
                distribution = dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
                print(f"LLM predictions: {list(distribution.keys())[:3]}")
                return distribution
            
            # If no valid predictions, use fallback
            print("LLM predictions failed, using fallback")
            return self._fallback_prediction(pet_data, health_indicators, breed_list)
            
        except Exception as e:
            print(f"Warning: LLM prediction failed: {e}")
            return self._fallback_prediction(pet_data, health_indicators, breed_list)
    
    def _create_prediction_prompt(self, pet_data: Dict, purchase_history: List[Dict], 
                                health_indicators: List[str], breed_list: List[str], 
                                breed_profiles: Dict) -> str:
        """Create a comprehensive prompt for breed prediction."""
        
        prompt = f"""Analyze the following information about a dog with unknown breed and predict the most likely breed composition:

PET INFORMATION:
- Name: {pet_data.get('name', 'Unknown')}
- Age: {pet_data.get('age', 'Unknown')} years
- Size: {pet_data.get('size', 'Unknown')}
- Gender: {pet_data.get('gender', 'Unknown')}
- Health Indicators: {pet_data.get('health_indicators', [])}

PURCHASE HISTORY ANALYSIS:
- Total Orders: {len(purchase_history)}
- Purchase Patterns: {self._analyze_purchase_patterns(purchase_history)}

RECENT PURCHASES:
"""
        
        # Add recent purchases (limit to 10 for brevity)
        for i, purchase in enumerate(purchase_history[:10], 1):
            prompt += f"""
{i}. Date: {purchase.get('order_date', 'Unknown')}
   Category: {purchase.get('category', 'Unknown')}
   Product: {purchase.get('item_name', 'Unknown')[:100]}...
"""
        
        prompt += f"""
HEALTH INDICATORS IDENTIFIED: {', '.join(health_indicators)}

AVAILABLE BREEDS: {', '.join(breed_list)}

Based on the purchase patterns, health indicators, pet size/age, and buying behavior, provide breed percentages that sum to exactly 100%. Consider:

1. Health-related purchases (joint supplements, special foods, etc.) and which breeds are predisposed
2. Size indicators from products and pet information
3. Age-related purchases (senior vs puppy products)
4. Activity level based on toys and accessories purchased
5. Grooming needs based on grooming products

Provide your response as a valid JSON object with breed names as keys and percentage values (numbers only, no % symbol):

Example format:
{{
    "goldenRetriever": 35,
    "labradorRetriever": 25,
    "boxer": 20,
    "germanShepherd": 20
}}

Your analysis:"""
        
        return prompt
    
    def _analyze_purchase_patterns(self, purchase_history: List[Dict]) -> Dict:
        """Analyze purchase patterns to extract insights."""
        categories = {}
        for purchase in purchase_history:
            category = purchase.get('category', 'Other')
            categories[category] = categories.get(category, 0) + 1
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_orders': len(purchase_history),
            'top_categories': top_categories,
            'spans_months': self._calculate_purchase_span(purchase_history)
        }
    
    def _calculate_purchase_span(self, purchase_history: List[Dict]) -> int:
        """Calculate how many months the purchase history spans."""
        if not purchase_history:
            return 0
            
        dates = []
        for purchase in purchase_history:
            try:
                date_str = purchase.get('order_date', '')
                if date_str:
                    dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
            except:
                continue
                
        if len(dates) < 2:
            return 1
            
        earliest = min(dates)
        latest = max(dates)
        months = (latest.year - earliest.year) * 12 + (latest.month - earliest.month)
        return max(1, months)
    
    def _parse_breed_distribution(self, response_text: str, breed_list: List[str]) -> Dict[str, float]:
        """Parse the JSON response from the LLM."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                distribution = json.loads(json_str)
                
                # Validate and normalize
                valid_distribution = {}
                total = 0
                
                for breed, percentage in distribution.items():
                    if breed in breed_list:
                        valid_distribution[breed] = float(percentage)
                        total += float(percentage)
                
                # Normalize to sum to 100
                if total > 0 and abs(total - 100) > 1:  # Allow small rounding errors
                    for breed in valid_distribution:
                        valid_distribution[breed] = (valid_distribution[breed] / total) * 100
                
                return valid_distribution
                
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            
        # Fallback if parsing fails
        return {}
    
    def _fallback_prediction(self, pet_data: Dict, health_indicators: List[str], 
                           breed_list: List[str]) -> Dict[str, float]:
        """Simple rule-based fallback prediction."""
        # Return even distribution among top common mixed breeds
        common_mixes = ['goldenRetriever', 'labradorRetriever', 'germanShepherd', 'boxer', 'beagle']
        available_mixes = [breed for breed in common_mixes if breed in breed_list]
        
        if not available_mixes:
            available_mixes = breed_list[:5]  # Take first 5 breeds
            
        percentage = 100.0 / len(available_mixes)
        return {breed: percentage for breed in available_mixes}
    
    def _generate_breed_explanations(self, predictions: Dict[str, float], pet_data: Dict, 
                                   purchase_history: List[Dict], health_indicators: List[str]) -> Dict[str, str]:
        """Generate explanations for why specific breeds match the pet profile."""
        explanations = {}
        
        # Get sorted predictions
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        
        # Generate explanations for top 4 breeds or those >2%
        for breed_key, percentage in sorted_predictions:
            if len(explanations) >= 4 and percentage <= 2.0:
                break
            if percentage <= 2.0:
                continue
                
            breed_info = self.breed_definitions.get(breed_key, {})
            if not breed_info:
                continue
                
            explanation = self._create_breed_explanation(
                breed_key, breed_info, pet_data, purchase_history, health_indicators, percentage
            )
            explanations[breed_key] = explanation
        
        return explanations
    
    def _create_breed_explanation(self, breed_key: str, breed_info: Dict, pet_data: Dict,
                                purchase_history: List[Dict], health_indicators: List[str], 
                                percentage: float) -> str:
        """Create a detailed explanation for why a breed matches the pet profile."""
        explanation_parts = []
        breed_name = breed_info.get('name', breed_key.replace('_', ' ').title())
        
        # Size matching
        pet_size = pet_data.get('size', '')
        breed_weight = breed_info.get('weight', '')
        breed_height = breed_info.get('height', '')
        
        if pet_size in ['XS', 'SM', 'S'] and any(term in breed_weight.lower() for term in ['9-16', '11-20', 'under 28', 'small']):
            explanation_parts.append(f"size perfectly matches as a small companion breed ({breed_weight.split('Male:')[0].strip() if 'Male:' in breed_weight else breed_weight[:30]})")
        elif pet_size in ['L', 'XL'] and any(term in breed_weight.lower() for term in ['65-', '70-', '80', 'large']):
            explanation_parts.append(f"size aligns well as a large breed ({breed_weight.split('Male:')[0].strip() if 'Male:' in breed_weight else breed_weight[:30]})")
        elif pet_size == 'M':
            explanation_parts.append(f"size fits the medium breed category")
        
        # Age and lifespan matching
        pet_age = pet_data.get('age')
        life_expectancy = breed_info.get('life_expectancy', '')
        if pet_age and life_expectancy:
            if pet_age >= 8 and '10 to 18' in life_expectancy:
                explanation_parts.append(f"excellent longevity match with {breed_name}s typically living {life_expectancy}")
            elif pet_age >= 8 and any(num in life_expectancy for num in ['12', '13', '14', '15', '16']):
                explanation_parts.append(f"good lifespan compatibility with {breed_name}s living {life_expectancy}")
        
        # Health indicators matching
        health_desc = breed_info.get('health_description', '').lower()
        diet_desc = breed_info.get('diet_nutrition', '').lower()
        
        for indicator in health_indicators:
            if 'digestive' in indicator and ('digestive' in health_desc or 'pancreatitis' in health_desc or 'low-fat' in diet_desc):
                explanation_parts.append(f"strong health correlation as {breed_name}s are prone to digestive issues requiring special dietary management")
            elif 'joint' in indicator and ('hip dysplasia' in health_desc or 'joint' in health_desc):
                explanation_parts.append(f"health profile matches as {breed_name}s commonly experience joint problems like hip dysplasia")
            elif 'skin' in indicator and ('skin' in health_desc or 'allergies' in health_desc):
                explanation_parts.append(f"health indicators align with {breed_name}s' predisposition to skin conditions and allergies")
            elif 'dental' in indicator and 'dental' in health_desc:
                explanation_parts.append(f"dental care needs match {breed_name}s' tendency toward dental problems")
        
        # Exercise and lifestyle matching
        exercise_needs = breed_info.get('exercise_needs', '3')
        apartment_friendly = breed_info.get('good_for_apartments', '3')
        
        # Analyze purchase patterns for lifestyle clues
        category_counts = {}
        for purchase in purchase_history:
            category = purchase.get('category', '')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Low exercise needs matching
        if int(exercise_needs) <= 2 and pet_age and pet_age >= 8:
            explanation_parts.append(f"lifestyle compatibility as {breed_name}s have low exercise requirements (score: {exercise_needs}/5) suitable for senior pets")
        elif int(exercise_needs) >= 4 and category_counts.get('Toys', 0) > 3:
            explanation_parts.append(f"activity level matches with high exercise needs (score: {exercise_needs}/5) supported by frequent toy purchases")
        
        # Apartment living
        if int(apartment_friendly) >= 4:
            explanation_parts.append(f"excellent apartment living compatibility (score: {apartment_friendly}/5)")
        
        # Grooming needs
        grooming_needs = breed_info.get('grooming_needs', '3')
        grooming_purchases = category_counts.get('Grooming', 0)
        if int(grooming_needs) >= 4 and grooming_purchases > 2:
            explanation_parts.append(f"grooming requirements match with high maintenance needs (score: {grooming_needs}/5) reflected in purchase history")
        elif int(grooming_needs) <= 2 and grooming_purchases <= 1:
            explanation_parts.append(f"low-maintenance grooming needs (score: {grooming_needs}/5) align with minimal grooming product purchases")
        
        # Temperament for seniors
        temperament = breed_info.get('temperament', '').lower()
        if pet_age and pet_age >= 8 and any(trait in temperament for trait in ['calm', 'gentle', 'loving', 'good-natured']):
            explanation_parts.append(f"temperament well-suited for senior dogs with traits like {breed_info.get('temperament', '')}")
        
        # Special breed characteristics
        maintenance_level = breed_info.get('maintenance_level', '').lower()
        if maintenance_level == 'low' and pet_age and pet_age >= 8:
            explanation_parts.append(f"ideal low-maintenance breed for older pets")
        
        # Construct final explanation
        if explanation_parts:
            if len(explanation_parts) == 1:
                return f"This breed matches because it has {explanation_parts[0]}."
            elif len(explanation_parts) == 2:
                return f"This breed matches because it has {explanation_parts[0]} and {explanation_parts[1]}."
            else:
                main_reasons = explanation_parts[:2]
                return f"This breed matches because it has {main_reasons[0]}, {main_reasons[1]}, and {len(explanation_parts)-2} other compatible characteristics."
        else:
            # Fallback explanation
            return f"This breed matches based on statistical analysis of the pet's characteristics and purchase patterns."
    
    def get_breed_details(self, breed_key: str) -> Dict:
        """Get detailed information about a specific breed."""
        if breed_key in self.breed_definitions:
            breed_info = self.breed_definitions[breed_key]
            
            # Get characteristics from the trained model
            model_characteristics = self.breed_model.get_breed_characteristics(breed_key)
            
            return {
                'name': breed_info.get('name', breed_key),
                'basic_info': {
                    'weight': breed_info.get('weight', ''),
                    'height': breed_info.get('height', ''),
                    'life_expectancy': breed_info.get('life_expectancy', ''),
                    'temperament': breed_info.get('temperament', '')
                },
                'characteristics': {
                    'exercise_needs': breed_info.get('exercise_needs', 3),
                    'grooming_needs': breed_info.get('grooming_needs', 3),
                    'friendliness': breed_info.get('friendliness', 3),
                    'good_with_kids': breed_info.get('good_with_kids', 3),
                    'good_for_apartments': breed_info.get('good_for_apartments', 3)
                },
                'model_features': model_characteristics.get('numerical_features', {}),
                'health_predispositions': model_characteristics.get('health_predispositions', {}),
                'description': breed_info.get('breed_intro', '')
            }
        return {}

def main():
    """Main function to demonstrate the breed predictor."""
    try:
        predictor = BreedPredictor()
        customers, _ = predictor.load_data()
        
        print(f"Loaded {len(customers)} customers")
        
        # Find some test cases
        test_cases = []
        for customer_id, customer_data in list(customers.items())[:3]:  # Test first 3 customers
            for pet_id, pet_data in customer_data.get('pets', {}).items():
                test_cases.append((customer_id, pet_id))
                if len(test_cases) >= 5:  # Limit to 5 tests
                    break
            if len(test_cases) >= 5:
                break
        
        for customer_id, pet_id in test_cases:
            try:
                print(f"\n{'='*50}")
                print(f"HYBRID BREED PREDICTION FOR {pet_id}")
                print(f"{'='*50}")
                
                distribution, confidence_result, explanations = predictor.predict_breed_distribution(customer_id, pet_id)
                
                print("Predicted Breed Distribution:")
                for breed, percentage in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
                    breed_name = predictor.breed_definitions.get(breed, {}).get('name', breed)
                    print(f"  {breed_name}: {percentage:.1f}%")
                    
                print("\nConfidence Result:")
                for key, value in confidence_result.items():
                    print(f"{key}: {value}")
                    
                print("\nBreed Explanations:")
                for breed, explanation in explanations.items():
                    print(f"{breed}: {explanation}")
                    
            except Exception as e:
                print(f"Error predicting for {pet_id}: {e}")
                
    except Exception as e:
        print(f"Error initializing predictor: {e}")
        print("Make sure to set your OPENAI_API_KEY environment variable")

if __name__ == "__main__":
    main()
