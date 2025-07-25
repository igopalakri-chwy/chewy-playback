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
        
        # Try the dog_breed_data directory in the same folder as this file
        breeds_dir = os.path.join(os.path.dirname(__file__), 'dog_breed_data')
        
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
        predictions, explanations, llm_confidence = self._get_llm_predictions(pet_data, purchase_history, all_health_indicators)
        
        # Use LLM-generated confidence instead of confidence_scorer
        confidence_result = {
            'confidence_score': llm_confidence,
            'confidence_level': self._get_confidence_level_from_score(llm_confidence),
            'source': 'LLM-generated',
            'reliability_flags': [],
            'recommendations': []
        }
        
        return predictions, confidence_result, explanations
    
    def _get_llm_predictions(self, pet_data: Dict, purchase_history: List[Dict], 
                            health_indicators: List[str]) -> Tuple[Dict[str, float], Dict[str, str], float]:
        """Get predictions from the LLM with proper normalization, explanations, and LLM-generated confidence."""
        try:
            # Get breed list from breed definitions
            breed_list = list(self.breed_definitions.keys())
            breed_profiles = self._create_breed_health_profile()
            
            prompt = self._create_prediction_prompt(pet_data, purchase_history, health_indicators, breed_list, breed_profiles)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert canine geneticist and veterinary behaviorist with extensive experience in breed identification. Provide accurate, evidence-based breed predictions with detailed reasoning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            llm_response = response.choices[0].message.content
            distribution, explanations, llm_confidence = self._parse_breed_distribution_and_explanations(llm_response, breed_list)
            
            # Validate and normalize results
            if distribution and len(distribution) > 0:
                # Sort by percentage (highest first)
                distribution = dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
                print(f"LLM predictions: {list(distribution.keys())[:3]}")
                return distribution, explanations, llm_confidence
            
            # If no valid predictions, use fallback
            print("LLM predictions failed, using fallback")
            fallback_dist = self._fallback_prediction(pet_data, health_indicators, breed_list)
            fallback_explanations = {breed: f"Fallback prediction based on general breed characteristics." for breed in list(fallback_dist.keys())[:3]}
            return fallback_dist, fallback_explanations, 15.0  # Low confidence for fallback
            
        except Exception as e:
            print(f"Warning: LLM prediction failed: {e}")
            fallback_dist = self._fallback_prediction(pet_data, health_indicators, breed_list)
            fallback_explanations = {breed: f"Fallback prediction due to error: {str(e)[:50]}..." for breed in list(fallback_dist.keys())[:3]}
            return fallback_dist, fallback_explanations, 10.0  # Very low confidence for error fallback
    
    def _create_prediction_prompt(self, pet_data: Dict, purchase_history: List[Dict], 
                                health_indicators: List[str], breed_list: List[str], 
                                breed_profiles: Dict) -> str:
        """Create a comprehensive, detailed prompt for breed prediction with LLM-generated confidence."""
        
        # Analyze purchase patterns in detail
        purchase_analysis = self._analyze_purchase_patterns(purchase_history)
        
        # Get size-filtered breeds for efficiency
        filtered_breeds = self._filter_breeds_by_size(breed_list, pet_data.get('size', 'Unknown'))
        
        prompt = f"""You are an expert canine geneticist and veterinary behaviorist with 20+ years of experience in breed identification. Your task is to analyze comprehensive pet data and determine the most likely breed composition for a mixed-breed dog.

CRITICAL INSTRUCTIONS:
1. Percentages MUST sum to exactly 100% - this is mandatory
2. Provide exactly 3-5 breed predictions (no more, no less)
3. Generate a confidence score (0-100) based on data quality and certainty
4. Give one-sentence reasoning for each breed prediction

=== PET PROFILE ANALYSIS ===
Pet Name: {pet_data.get('name', 'Unknown')}
Physical Characteristics:
- Age: {pet_data.get('age', 'Unknown')} years old
- Size Category: {pet_data.get('size', 'Unknown')} 
- Weight: {pet_data.get('weight', 'Unknown')} lbs
- Gender: {pet_data.get('gender', 'Unknown')}
- Current Health Indicators: {', '.join(pet_data.get('health_indicators', []))}

=== PURCHASE BEHAVIOR ANALYSIS ===
Total Purchase History: {len(purchase_history)} orders analyzed
Purchase Patterns Identified: {purchase_analysis}

DETAILED PURCHASE BREAKDOWN:"""
        
        # Add detailed purchase analysis
        food_items = []
        treat_items = []
        toy_items = []
        health_items = []
        other_items = []
        
        for purchase in purchase_history[:15]:  # Show more detail
            item_name = purchase.get('product_name', purchase.get('item_name', 'Unknown'))
            category = purchase.get('category', 'Unknown')
            date = purchase.get('order_date', 'Unknown')
            
            if 'food' in category.lower() or 'food' in item_name.lower():
                food_items.append(f"• {item_name} (Date: {date})")
            elif 'treat' in category.lower() or 'treat' in item_name.lower():
                treat_items.append(f"• {item_name} (Date: {date})")
            elif 'toy' in category.lower() or 'toy' in item_name.lower():
                toy_items.append(f"• {item_name} (Date: {date})")
            elif any(health_word in item_name.lower() for health_word in ['joint', 'vitamin', 'supplement', 'dental', 'skin', 'coat']):
                health_items.append(f"• {item_name} (Date: {date})")
            else:
                other_items.append(f"• {item_name} (Date: {date})")
        
        if food_items:
            prompt += f"\n\nFOOD PURCHASES ({len(food_items)} items):\n" + '\n'.join(food_items[:5])
        if treat_items:
            prompt += f"\n\nTREAT PURCHASES ({len(treat_items)} items):\n" + '\n'.join(treat_items[:5])
        if toy_items:
            prompt += f"\n\nTOY PURCHASES ({len(toy_items)} items):\n" + '\n'.join(toy_items[:5])
        if health_items:
            prompt += f"\n\nHEALTH/SUPPLEMENT PURCHASES ({len(health_items)} items):\n" + '\n'.join(health_items[:5])
        if other_items:
            prompt += f"\n\nOTHER PURCHASES ({len(other_items)} items):\n" + '\n'.join(other_items[:3])
        
        prompt += f"""

=== HEALTH INDICATORS DETECTED ===
From Purchase Analysis: {', '.join(health_indicators) if health_indicators else 'None detected'}

=== BREED ANALYSIS FRAMEWORK ===
Consider these key factors in your analysis:

1. SIZE INDICATORS:
   - Product sizes (small/medium/large breed food)
   - Toy sizes (puppies vs large dogs)
   - Accessory sizes (collar, leash, crate dimensions)

2. HEALTH PREDISPOSITIONS:
   - Joint supplements → breeds prone to hip dysplasia
   - Skin/coat products → breeds with coat sensitivities
   - Dental products → breeds with dental issues
   - Special diets → breeds with food sensitivities

3. BEHAVIORAL CLUES:
   - Training treats → intelligent, trainable breeds
   - Puzzle toys → high-intelligence breeds
   - Chew toys → power chewers (bully breeds, working dogs)
   - Fetch toys → retrieving breeds

4. ACTIVITY LEVEL:
   - Exercise equipment → high-energy breeds
   - Interactive toys → active, engaged breeds
   - Calming products → anxious or high-strung breeds

5. GROOMING NEEDS:
   - Grooming tools → high-maintenance coats
   - Lack of grooming products → low-maintenance breeds
   - Specialized shampoos → specific coat types

=== AVAILABLE BREED OPTIONS ===
Focus your analysis on these size-appropriate breeds:
{', '.join(filtered_breeds[:50])}  # Top 50 most relevant breeds

=== RESPONSE FORMAT (MANDATORY) ===
Provide your response as a valid JSON object with exactly three sections:

{{
    "confidence_score": [YOUR_CONFIDENCE_0_TO_100],
    "breed_predictions": {{
        "breed1_name": percentage1,
        "breed2_name": percentage2,
        "breed3_name": percentage3,
        "breed4_name": percentage4
    }},
    "reasoning": {{
        "breed1_name": "One sentence explaining why this breed matches the evidence.",
        "breed2_name": "One sentence explaining why this breed matches the evidence.",
        "breed3_name": "One sentence explaining why this breed matches the evidence.",
        "breed4_name": "One sentence explaining why this breed matches the evidence."
    }}
}}

CONFIDENCE SCORING GUIDE:
- 90-100: Overwhelming evidence, very certain
- 70-89: Strong evidence, confident prediction
- 50-69: Moderate evidence, reasonable prediction
- 30-49: Limited evidence, educated guess
- 10-29: Very limited evidence, speculative
- 0-9: Almost no evidence, random guess

CRITICAL REMINDERS:
1. Percentages in breed_predictions MUST sum to exactly 100%
2. Include 3-5 breeds maximum
3. Base predictions on actual purchase evidence, not assumptions
4. Each reasoning sentence should reference specific purchase behaviors
5. Confidence score should reflect data quality and certainty

Your expert analysis:"""
        
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
    
    def _filter_breeds_by_size(self, breed_list: List[str], pet_size: str) -> List[str]:
        """Filter breeds by pet size to improve LLM efficiency."""
        if not pet_size or pet_size.lower() in ['unknown', 'unk', '']:
            return breed_list  # Return all breeds if size unknown
        
        # Define size categories (can be expanded based on breed_definitions)
        size_mapping = {
            'small': ['chihuahua', 'pomeranian', 'yorkshireTerrier', 'maltese', 'pug', 'frenchBulldog', 'bostonTerrier', 'cavalierKingCharlesSpaniel', 'bichonFrise', 'havanese'],
            'medium': ['beagle', 'borderCollie', 'australianShepherd', 'bulldog', 'cockerSpaniel', 'bassetHound', 'brittany', 'whippet', 'staffordshireBullTerrier'],
            'large': ['labradorRetriever', 'goldenRetriever', 'germanShepherd', 'boxer', 'rottweiler', 'dobermanPinscher', 'greyhound', 'pointer', 'weimaraner', 'vizsla'],
            'giant': ['greatDane', 'mastiff', 'saintBernard', 'newfoundland', 'bernieseMountainDog', 'leonberger', 'tibetanMastiff']
        }
        
        pet_size_lower = pet_size.lower()
        if pet_size_lower in size_mapping:
            # Return size-specific breeds + some common mixed breeds
            size_breeds = size_mapping[pet_size_lower]
            common_mixed = ['labradorRetriever', 'goldenRetriever', 'germanShepherd', 'beagle', 'boxer']
            return list(set(size_breeds + common_mixed))
        
        return breed_list  # Return all if size doesn't match categories
    
    def _parse_breed_distribution_and_explanations(self, llm_response: str, breed_list: List[str]) -> Tuple[Dict[str, float], Dict[str, str], float]:
        """Parse breed distribution, explanations, and confidence from LLM response."""
        try:
            # Try to parse the JSON response
            response_data = json.loads(llm_response.strip())
            
            # Extract data from new format
            breeds = response_data.get('breed_predictions', {})
            explanations = response_data.get('reasoning', {})
            llm_confidence = response_data.get('confidence_score', 50.0)  # Default 50 if missing
            
            # Validate and convert breed percentages
            distribution = {}
            for breed, percentage in breeds.items():
                if isinstance(percentage, (int, float)) and 0 <= percentage <= 100:
                    # Match breed name to internal keys
                    matched_breed = self._match_breed_name(breed, breed_list)
                    if matched_breed:
                        distribution[matched_breed] = float(percentage)
            
            # CRITICAL: Ensure percentages sum to exactly 100%
            total = sum(distribution.values())
            if total > 0:
                if abs(total - 100) > 0.1:  # If not close to 100%, normalize
                    print(f"    📊 Normalizing percentages: {total}% → 100%")
                    distribution = {breed: (pct/total) * 100 for breed, pct in distribution.items()}
                    
                # Final verification
                final_total = sum(distribution.values())
                print(f"    ✅ Final total: {final_total:.1f}%")
            
            # Match explanations to the same breed keys
            matched_explanations = {}
            for breed, explanation in explanations.items():
                matched_breed = self._match_breed_name(breed, breed_list)
                if matched_breed and matched_breed in distribution:
                    # Ensure explanations are concise (one sentence)
                    explanation = explanation.strip()
                    if '.' in explanation:
                        explanation = explanation.split('.')[0] + '.'
                    matched_explanations[matched_breed] = explanation
            
            return distribution, matched_explanations, float(llm_confidence)
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"    ⚠️ Failed to parse LLM response JSON: {e}")
            # Fall back to old parsing method for breeds only
            distribution = self._parse_breed_distribution(llm_response, breed_list)
            explanations = self._manual_extract_explanations(llm_response, distribution)
            return distribution, explanations, 25.0  # Default low confidence for fallback
    
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
    
    def _get_confidence_level_from_score(self, score: float) -> str:
        """Convert numerical confidence score to descriptive level."""
        if score >= 90:
            return 'Very High'
        elif score >= 70:
            return 'High'
        elif score >= 50:
            return 'Medium'
        elif score >= 30:
            return 'Low'
        elif score >= 10:
            return 'Very Low'
        else:
            return 'Minimal'
    
    def _match_breed_name(self, breed_name: str, breed_list: List[str]) -> str:
        """Match a breed name from LLM response to our internal breed keys."""
        breed_name_lower = breed_name.lower().replace(' ', '').replace('_', '').replace('-', '')
        
        # Try exact match first
        for breed_key in breed_list:
            if breed_name_lower == breed_key.lower():
                return breed_key
        
        # Try partial match
        for breed_key in breed_list:
            breed_key_lower = breed_key.lower()
            if breed_name_lower in breed_key_lower or breed_key_lower in breed_name_lower:
                return breed_key
        
        # Try fuzzy matching for common variations
        breed_mapping = {
            'golden': 'goldenRetriever', 'lab': 'labradorRetriever', 'labrador': 'labradorRetriever',
            'german': 'germanShepherd', 'shepherd': 'germanShepherd', 'retriever': 'goldenRetriever',
            'husky': 'siberianHusky', 'border': 'borderCollie', 'collie': 'borderCollie'
        }
        
        for key, value in breed_mapping.items():
            if key in breed_name_lower and value in breed_list:
                return value
        
        return None  # No match found
    
    def _manual_extract_explanations(self, llm_response: str, distribution: Dict[str, float]) -> Dict[str, str]:
        """Manually extract explanations from LLM response when JSON parsing fails."""
        explanations = {}
        
        try:
            # Look for explanations after breed names in the response
            lines = llm_response.split('\n')
            current_breed = None
            explanation_text = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line contains a breed name from our distribution
                breed_found = None
                for breed in distribution.keys():
                    if breed.lower() in line.lower() or any(part in line.lower() for part in breed.lower().split()):
                        breed_found = breed
                        break
                
                if breed_found:
                    # Save previous explanation if we have one
                    if current_breed and explanation_text:
                        explanations[current_breed] = ' '.join(explanation_text).strip()
                    
                    # Start new breed explanation
                    current_breed = breed_found
                    explanation_text = [line]
                elif current_breed and line:
                    # Continue building explanation for current breed
                    explanation_text.append(line)
            
            # Save the last explanation
            if current_breed and explanation_text:
                explanations[current_breed] = ' '.join(explanation_text).strip()
                
        except Exception as e:
            print(f"    ⚠️ Manual explanation extraction failed: {e}")
        
        # If we still don't have explanations, generate simple ones
        if not explanations:
            for breed in list(distribution.keys())[:3]:  # Top 3 breeds
                explanations[breed] = f"This breed was predicted based on the available pet data and purchase patterns."
        
        return explanations
    
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
        
        # Age and lifespan matching - convert pet_age to int safely
        pet_age_raw = pet_data.get('age')
        pet_age = None
        if pet_age_raw is not None:
            try:
                pet_age = int(pet_age_raw)
            except (ValueError, TypeError):
                pet_age = None
                
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
