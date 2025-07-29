#!/usr/bin/env python3
"""
Review and Order Intelligence Agent

Enhanced AI agent that derives comprehensive pet insights from order history and customer reviews
using LLM analysis with intelligent pet detection capabilities.

Features:
- Count-based pet detection (e.g., "my 3 cats" vs 2 known cats)
- Named pet detection (e.g., "Charlie loves this toy")
- Unnamed species detection (e.g., "my dog" with no dogs in profiles)
- Comprehensive LLM analysis for pet profiling
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

import openai
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for review analysis
PRIORITY_REVIEW_KEYWORDS = [
    'girl', 'boy', 'female', 'male', 'she', 'he', 'her', 'his',
    'lbs', 'pounds', 'weight', 'large', 'small', 'breed'
]

class ReviewOrderIntelligenceAgent:
    """
    Enhanced AI agent for comprehensive pet profile analysis.
    
    This agent processes customer review and order data to create detailed pet profiles
    using advanced LLM analysis and intelligent pet detection. It handles:
    
    - Count-based detection: Identifies discrepancies between known pets and review mentions
    - Named pet detection: Extracts specific pet names mentioned in reviews  
    - Unnamed species detection: Detects new pet types mentioned without names
    - Comprehensive profiling: Creates detailed pet attributes from review sentiment
    
    Designed for integration with the Chewy Playback Pipeline using cached Snowflake data.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the Review and Order Intelligence Agent.
        
        Args:
            openai_api_key: OpenAI API key for LLM analysis. If None, reads from environment.
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

    # ============================================================================
    # ENHANCED PET DETECTION METHODS
    # ============================================================================
    
    def _get_customer_pets_from_reviews(self, customer_reviews: pd.DataFrame, known_pet_profiles: List[Dict] = None, orders_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Get all pets for a customer from review data with enhanced detection."""
        if not known_pet_profiles:
            return {'pet_names': [], 'pet_count_analysis': {}}
        
        # Get registered pets from the known pet profiles (from Snowflake)
        registered_pets = [pet['PetName'] for pet in known_pet_profiles if pet.get('PetName')]
        
        # Enhanced detection of additional pets using LLM + hashmap approach
        pet_count_analysis = self._detect_additional_pets_with_llm(
            customer_reviews, known_pet_profiles or [], orders_df
        )
        
        # Get all pet names (registered + additional)
        all_pet_names = registered_pets + [pet['name'] for pet in pet_count_analysis.get('additional_pets', [])]
        
        return {
            'pet_names': list(set(all_pet_names)),
            'pet_count_analysis': pet_count_analysis
        }
    
    def _detect_additional_pets_with_llm(self, customer_reviews: pd.DataFrame, known_pet_profiles: List[Dict], orders_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Detect additional pets mentioned in reviews using LLM analysis and hashmap approach."""
        
        # Extract current pet counts from known profiles
        current_counts = {}
        for profile in known_pet_profiles:
            pet_type = profile.get('PetType', 'unknown').lower()
            if pet_type != 'unknown' and pet_type != 'unk':
                current_counts[pet_type] = current_counts.get(pet_type, 0) + 1
        
        # If no reviews, return current state
        if customer_reviews.empty:
            return {
                'additional_pets': [],
                'original_counts': current_counts,
                'detected_counts': current_counts.copy(),
                'updated_counts': current_counts.copy()
            }
        
        # Use LLM to detect pet ownership mentions in reviews
        review_text = " ".join(customer_reviews['ReviewText'].fillna('').tolist())
        
        try:
            llm_analysis = self._analyze_pet_ownership_with_llm(review_text, current_counts, orders_df)
            detected_counts = llm_analysis['pet_counts']
            named_pets = llm_analysis.get('named_pets', [])
        except Exception as e:
            logger.warning(f"🔄 LLM pet ownership analysis failed, using known counts: {e}")
            detected_counts = current_counts.copy()
            named_pets = []
        
        # Find discrepancies and create additional pet profiles
        additional_pets = []
        updated_counts = current_counts.copy()
        
        # Process count-based additional pets (e.g., "my 3 cats" when only 2 in profiles)
        for pet_type, detected_count in detected_counts.items():
            current_count = current_counts.get(pet_type, 0)
            if detected_count > current_count:
                # Create additional pets for the difference
                for i in range(detected_count - current_count):
                    additional_pets.append({
                        'name': f'Additional_{pet_type.title()}_{i+1}',
                        'type': pet_type,
                        'source': 'detected_from_reviews',
                        'confidence': 0.7,
                        'detection_method': 'count_based_detection'
                    })
                updated_counts[pet_type] = detected_count
        
        # Process named pets not in known profiles
        known_pet_names = [pet['PetName'].lower() for pet in known_pet_profiles]
        for named_pet in named_pets:
            pet_name = named_pet['name']
            pet_species = named_pet['species']
            
            # Skip if pet name already exists in known profiles
            if pet_name.lower() not in known_pet_names:
                # Adjust confidence based on species certainty
                if pet_species == 'unknown':
                    confidence = 0.5  # Lower confidence when species cannot be determined
                else:
                    confidence = 0.8  # Higher confidence when species is known or inferred
                
                additional_pets.append({
                    'name': pet_name,
                    'type': pet_species,
                    'source': 'detected_from_reviews',
                    'confidence': confidence,
                    'detection_method': 'named_pet_detection'
                })
                
                # Update count for this species if not already counted
                if pet_species != 'unknown' and pet_species not in updated_counts:
                    updated_counts[pet_species] = updated_counts.get(pet_species, 0) + 1
                
        # Handle "my cat" case - unnamed pets of new species
        for pet_type, detected_count in detected_counts.items():
            if pet_type not in current_counts and detected_count > 0 and pet_type != 'unknown':
                # This is a new species mentioned (e.g., "my cat" when no cats in profiles)
                additional_pets.append({
                    'name': f'UNK_{pet_type.upper()}',
                    'type': pet_type,
                    'source': 'detected_from_reviews',
                    'confidence': 0.6,
                    'detection_method': 'unnamed_species_detection'
                })
                updated_counts[pet_type] = detected_count
        
        return {
            'additional_pets': additional_pets,
            'original_counts': current_counts,
            'detected_counts': detected_counts,
            'updated_counts': updated_counts
        }
    
    def _analyze_pet_ownership_with_llm(self, review_text: str, known_counts: Dict[str, int], customer_orders: pd.DataFrame = None) -> Dict[str, Any]:
        """Use LLM to analyze review text for pet ownership indicators and specific pet names."""
        
        # Truncate review text to avoid token limits
        if len(review_text) > 3000:
            review_text = review_text[:3000] + "..."
        
        prompt = f"""Analyze these customer reviews and extract pet ownership information.

Known pets from profiles: {known_counts}

Review texts: {review_text}

Extract TWO types of information:

1. PET COUNTS by species:
- Look for phrases like: "my 3 cats", "both of my dogs", "all 4 of them"
- Count clear ownership statements by the reviewer
- IGNORE product descriptions, other people's pets, hypothetical scenarios

2. SPECIFIC PET NAMES mentioned:
- Look for capitalized names that appear to be pet names
- Examples: "Fluffy loves this", "Max and Bella enjoy", "my dog Charlie"
- Include the species if mentioned with the name, otherwise use "unknown"
- For names without explicit species, try to infer from context or use "unknown"
- ONLY include names that seem to belong to the reviewer's pets

Return ONLY a JSON object with this structure:
{{
    "pet_counts": {{"dog": 2, "cat": 3}},
    "named_pets": [
        {{"name": "Charlie", "species": "dog"}},
        {{"name": "Fluffy", "species": "cat"}},
        {{"name": "Max", "species": "unknown"}}
    ]
}}

If no clear information found, return:
{{
    "pet_counts": {known_counts},
    "named_pets": []
}}"""
        
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing text for pet ownership indicators. Return only valid JSON with pet counts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                detected_data = json.loads(json_match.group())
                
                # Extract and validate pet counts
                pet_counts = detected_data.get('pet_counts', known_counts)
                validated_counts = {}
                for pet_type, count in pet_counts.items():
                    if isinstance(count, int) and count >= 0 and pet_type.lower() in ['dog', 'cat', 'pet', 'bird', 'rabbit', 'fish', 'unknown']:
                        validated_counts[pet_type.lower()] = count
                
                # Extract named pets
                named_pets = detected_data.get('named_pets', [])
                validated_named_pets = []
                for pet in named_pets:
                    if isinstance(pet, dict) and 'name' in pet and 'species' in pet:
                        species = str(pet['species']).lower().strip()
                        # Try to infer species from order context if unknown
                        if species == 'unknown':
                            species = self._infer_species_from_orders(str(pet['name']).strip(), customer_orders or pd.DataFrame())
                        
                        validated_named_pets.append({
                            'name': str(pet['name']).strip(),
                            'species': species
                        })
                
                return {
                    'pet_counts': validated_counts if validated_counts else known_counts,
                    'named_pets': validated_named_pets
                }
            else:
                logger.warning("No JSON found in LLM response for pet ownership analysis")
                return {'pet_counts': known_counts, 'named_pets': []}
                
        except Exception as e:
            logger.error(f"❌ Error in LLM pet ownership analysis: {e}")
            return {'pet_counts': known_counts, 'named_pets': []}
    
    def analyze_customer_with_cached_data(self, customer_id: str, pets_df: pd.DataFrame, orders_df: pd.DataFrame, reviews_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze a single customer using cached Snowflake data with enhanced pet detection.
        This method is called by the pipeline with pre-fetched cached data.
        """
        logger.info(f"Analyzing customer {customer_id} with cached data...")
        
        if pets_df.empty:
            logger.warning(f"No pets found for customer {customer_id}")
            return {}
        
        # Convert pets DataFrame to list of dictionaries for the enhanced detection
        known_pet_profiles = []
        for _, pet_row in pets_df.iterrows():
            known_pet_profiles.append({
                'PetName': pet_row.get('PetName', 'Unknown'),
                'PetType': pet_row.get('PetType', 'UNK'),
                'PetBreed': pet_row.get('PetBreed', 'UNK'),
                'Gender': pet_row.get('Gender', 'UNK'),
                'PetAge': pet_row.get('PetAge', 'UNK'),
                'Weight': pet_row.get('Weight', 'UNK'),
                'Birthday': pet_row.get('Birthday', 'UNK')
            })
        
        # Use enhanced pet detection to get all pets (including additional ones from reviews)
        pet_detection_result = self._get_customer_pets_from_reviews(reviews_df, known_pet_profiles, orders_df)
        all_pet_names = pet_detection_result['pet_names']
        pet_count_analysis = pet_detection_result['pet_count_analysis']
        
        customer_results = {}
        
        # Log the pet count analysis results
        if pet_count_analysis.get('additional_pets'):
            logger.info(f"  🔍 Detected {len(pet_count_analysis['additional_pets'])} additional pets from reviews")
            logger.info(f"  📊 Pet count analysis: {pet_count_analysis['updated_counts']}")
        
        for pet_name in all_pet_names:
            logger.info(f"  🐾 Analyzing pet {pet_name} for customer {customer_id}...")
            
            # Get structured pet profile data for this pet
            structured_pet_data = None
            pet_profile_row = pets_df[pets_df['PetName'] == pet_name]
            if not pet_profile_row.empty:
                structured_pet_data = pet_profile_row.iloc[0].to_dict()
            else:
                # This is an additional pet detected from reviews
                additional_pet_info = next(
                    (pet for pet in pet_count_analysis.get('additional_pets', []) if pet['name'] == pet_name),
                    None
                )
                if additional_pet_info:
                    structured_pet_data = {
                        'PetName': pet_name,
                        'PetType': additional_pet_info['type'].title(),
                        'PetBreed': 'UNK',
                        'Gender': 'UNK',
                        'PetAge': 'UNK',
                        'Weight': 'UNK',
                        'Birthday': 'UNK',
                        'source': additional_pet_info['source'],
                        'confidence': additional_pet_info['confidence']
                    }
            
            # Filter reviews for this pet
            pet_reviews = pd.DataFrame()
            if not reviews_df.empty:
                if pet_name.startswith('Additional_') or pet_name.startswith('UNK_'):
                    # For additional pets or unnamed species, include all reviews for LLM analysis
                    pet_reviews = reviews_df.copy()
                elif structured_pet_data and structured_pet_data.get('source') == 'detected_from_reviews':
                    # For named pets detected from reviews, try to find specific mentions first
                    specific_reviews = reviews_df[
                        reviews_df['ReviewText'].str.contains(pet_name, case=False, na=False)
                    ]
                    if not specific_reviews.empty:
                        pet_reviews = specific_reviews
                    else:
                        # If no specific mentions, use all reviews for context
                        pet_reviews = reviews_df.copy()
                else:
                    # For registered pets, filter reviews that mention the pet name
                    pet_reviews = reviews_df[
                        reviews_df['ReviewText'].str.contains(pet_name, case=False, na=False)
                    ]
                    # If no specific reviews found, include all reviews for context
                    if pet_reviews.empty:
                        pet_reviews = reviews_df.copy()
            
            # Analyze pet attributes using LLM
            try:
                insights = self._analyze_pet_attributes_with_llm(
                    pet_reviews, orders_df, pet_name, structured_pet_data
                )
                
                # Create pet profile with enhanced information
                pet_insight = {
                    "PetName": pet_name,
                    "PetType": insights.get("PetType", "UNK"),
                    "PetTypeScore": insights.get("PetTypeScore", 0.0),
                    "Breed": insights.get("Breed", "UNK"),
                    "BreedScore": insights.get("BreedScore", 0.0),
                    "LifeStage": insights.get("LifeStage", "UNK"),
                    "LifeStageScore": insights.get("LifeStageScore", 0.0),
                    "Gender": insights.get("Gender", "UNK"),
                    "GenderScore": insights.get("GenderScore", 0.0),
                    "SizeCategory": insights.get("SizeCategory", "UNK"),
                    "SizeScore": insights.get("SizeScore", 0.0),
                    "Weight": insights.get("Weight", "UNK"),
                    "WeightScore": insights.get("WeightScore", 0.0),
                    "Birthday": insights.get("Birthday", "UNK"),
                    "BirthdayScore": insights.get("BirthdayScore", 0.0),
                    "PersonalityTraits": insights.get("PersonalityTraits", []),
                    "PersonalityScores": insights.get("PersonalityScores", {}),
                    "FavoriteProductCategories": insights.get("FavoriteProductCategories", []),
                    "CategoryScores": insights.get("CategoryScores", {}),
                    "BrandPreferences": insights.get("BrandPreferences", []),
                    "BrandScores": insights.get("BrandScores", {}),
                    "DietaryPreferences": insights.get("DietaryPreferences", []),
                    "DietaryScores": insights.get("DietaryScores", {}),
                    "BehavioralCues": insights.get("BehavioralCues", []),
                    "BehavioralScores": insights.get("BehavioralScores", {}),
                    "HealthMentions": insights.get("HealthMentions", []),
                    "HealthScores": insights.get("HealthScores", {}),
                    "MostOrderedProducts": insights.get("MostOrderedProducts", [])
                }
                
                # Add metadata for detected pets
                if structured_pet_data and structured_pet_data.get('source') == 'detected_from_reviews':
                    pet_insight["DetectionSource"] = "review_analysis"
                    pet_insight["DetectionConfidence"] = structured_pet_data.get('confidence', 0.7)
                    pet_insight["DetectionMethod"] = structured_pet_data.get('detection_method', 'enhanced_llm_detection')
                    
                    # Add specific metadata based on detection type
                    if pet_name.startswith('Additional_'):
                        pet_insight["DetectionType"] = "count_based"
                    elif pet_name.startswith('UNK_'):
                        pet_insight["DetectionType"] = "unnamed_species"
                    else:
                        pet_insight["DetectionType"] = "named_pet"
                
                customer_results[pet_name] = pet_insight
                logger.info(f"    ✅ Completed analysis for {pet_name}")
                
            except Exception as e:
                logger.error(f"    ❌ Error analyzing pet {pet_name}: {e}")
                continue
        
        # Add pet count analysis to the results metadata
        if pet_count_analysis:
            customer_results['_pet_count_analysis'] = pet_count_analysis
        
        logger.info(f"✅ Completed customer {customer_id} with {len(customer_results)} pets")
        return customer_results

    # ============================================================================
    # LLM CONTEXT PREPARATION AND ANALYSIS
    # ============================================================================
    
    def _prepare_llm_context(self, pet_reviews: pd.DataFrame, customer_orders: pd.DataFrame, pet_name: str, structured_pet_data: Dict[str, Any] = None) -> str:
        """Prepare context data for LLM analysis."""
        context_parts = []
        
        # Add structured pet data that's already available
        if structured_pet_data and pet_name != 'UNK':
            # Use the structured pet data passed from the pipeline
            context_parts.append(f"Pet Profile Data for {pet_name}:")
            context_parts.append(f"- Pet Type: {structured_pet_data.get('PetType', 'UNK')}")
            context_parts.append(f"- Breed: {structured_pet_data.get('PetBreed', structured_pet_data.get('Breed', 'UNK'))}")
            context_parts.append(f"- Gender: {structured_pet_data.get('Gender', 'UNK')}")
            context_parts.append(f"- Life Stage: {structured_pet_data.get('PetAge', structured_pet_data.get('LifeStage', 'UNK'))}")
            context_parts.append(f"- Size Category: {structured_pet_data.get('SizeCategory', 'UNK')}")
            context_parts.append(f"- Weight: {structured_pet_data.get('Weight', 'UNK')}")
            context_parts.append(f"- Birthday: {structured_pet_data.get('Birthday', 'UNK')}")
            context_parts.append("")
        elif not pet_reviews.empty and pet_name != 'UNK':
            # Fallback: try to get pet data from reviews (old method)
            try:
                pet_data = pet_reviews.iloc[0]
                context_parts.append(f"Pet Profile Data for {pet_name}:")
                context_parts.append(f"- Pet Type: {pet_data.get('PetType', 'UNK')}")
                context_parts.append(f"- Breed: {pet_data.get('Breed', 'UNK')}")
                context_parts.append(f"- Gender: {pet_data.get('Gender', 'UNK')}")
                context_parts.append(f"- Life Stage: {pet_data.get('LifeStage', 'UNK')}")
                context_parts.append(f"- Size Category: {pet_data.get('SizeCategory', 'UNK')}")
                context_parts.append(f"- Weight: {pet_data.get('Weight', 'UNK')}")
                context_parts.append(f"- Birthday: {pet_data.get('Birthday', 'UNK')}")
                context_parts.append("")
            except Exception as e:
                logger.warning(f"Could not extract pet data from reviews for {pet_name}: {e}")
                context_parts.append(f"Pet Profile Data for {pet_name}:")
                context_parts.append("- Pet Type: UNK")
                context_parts.append("- Breed: UNK")
                context_parts.append("- Gender: UNK")
                context_parts.append("- Life Stage: UNK")
                context_parts.append("- Size Category: UNK")
                context_parts.append("- Weight: UNK")
                context_parts.append("- Birthday: UNK")
            context_parts.append("")
        elif pet_name == 'UNK' or pet_name.startswith('Additional_') or pet_name.startswith('UNK_'):
            context_parts.append(f"Pet Profile Data for {pet_name}:")
            if structured_pet_data and structured_pet_data.get('PetType') and structured_pet_data.get('PetType') != 'UNK':
                context_parts.append(f"- Pet Type: {structured_pet_data.get('PetType', 'UNK')}")
            else:
                context_parts.append("- Pet Type: UNK")
            context_parts.append("- Breed: UNK")
            context_parts.append("- Gender: UNK")
            context_parts.append("- Life Stage: UNK")
            context_parts.append("- Size Category: UNK")
            context_parts.append("- Weight: UNK")
            context_parts.append("- Birthday: UNK")
            context_parts.append("")
            
            if pet_name.startswith('Additional_'):
                context_parts.append("NOTE: This pet was detected from count-based review analysis but has no registered profile data.")
                context_parts.append("FOCUS: Analyze all reviews to extract any information about this additional pet.")
            elif pet_name.startswith('UNK_'):
                context_parts.append("NOTE: This pet species was mentioned in reviews but no specific name was provided.")
                context_parts.append("FOCUS: Look for unnamed references like 'my cat' or 'our dog' in the reviews.")
            else:
                context_parts.append("NOTE: This pet is mentioned in reviews but has no registered profile data.")
            context_parts.append("")
        else:
            # No structured data available
            context_parts.append(f"Pet Profile Data for {pet_name}:")
            context_parts.append("- Pet Type: UNK")
            context_parts.append("- Breed: UNK")
            context_parts.append("- Gender: UNK")
            context_parts.append("- Life Stage: UNK")
            context_parts.append("- Size Category: UNK")
            context_parts.append("- Weight: UNK")
            context_parts.append("- Birthday: UNK")
            context_parts.append("")
            context_parts.append("NOTE: No structured profile data available for this pet.")
            context_parts.append("")
        
        # Add pet reviews context - prioritize reviews with gender/weight information
        if not pet_reviews.empty:
            context_parts.append(f"Pet Reviews for {pet_name}:")
            
            # For UNK pets, Additional pets, or named pets from review detection
            if pet_name == 'UNK' or pet_name.startswith('Additional_') or pet_name.startswith('UNK_') or (structured_pet_data and structured_pet_data.get('source') == 'detected_from_reviews'):
                if pet_name.startswith('Additional_'):
                    # For count-based additional pets, include all reviews
                    context_parts.append("All customer reviews (count-based detection):")
                    for i, review in enumerate(pet_reviews.iterrows()):
                        if i >= 15:  # Limit to avoid token overflow
                            break
                        _, review_data = review
                        context_parts.append(f"Review {i+1}: {review_data.get('ReviewText', '')}")
                elif pet_name.startswith('UNK_'):
                    # For unnamed species detection, focus on species-specific reviews
                    species = pet_name.split('_')[1].lower()
                    context_parts.append(f"Reviews mentioning {species}s (unnamed species detection):")
                    relevant_reviews = []
                    for _, review in pet_reviews.iterrows():
                        review_text = review.get('ReviewText', '').lower()
                        if species in review_text:
                            relevant_reviews.append(review)
                    
                    if relevant_reviews:
                        for i, review in enumerate(relevant_reviews[:12]):
                            context_parts.append(f"Review {i+1}: {review.get('ReviewText', '')}")
                    else:
                        context_parts.append(f"No reviews specifically mentioning {species}s found.")
                elif structured_pet_data and structured_pet_data.get('source') == 'detected_from_reviews':
                    # For named pets detected from reviews, look for the specific name
                    context_parts.append(f"Reviews mentioning '{pet_name}' (named pet detection):")
                    relevant_reviews = []
                    for _, review in pet_reviews.iterrows():
                        review_text = review.get('ReviewText', '')
                        if pet_name.lower() in review_text.lower():
                            relevant_reviews.append(review)
                    
                    if relevant_reviews:
                        for i, review in enumerate(relevant_reviews[:10]):
                            context_parts.append(f"Review {i+1}: {review.get('ReviewText', '')}")
                    else:
                        # If no specific mentions, include some general reviews for context
                        context_parts.append(f"No direct mentions of '{pet_name}' found. Including general reviews:")
                        for i, review in enumerate(pet_reviews.iterrows()):
                            if i >= 8:
                                break
                            _, review_data = review
                            context_parts.append(f"Review {i+1}: {review_data.get('ReviewText', '')}")
                else:
                    # For legacy UNK pets, look for specific patterns
                    relevant_reviews = []
                    for _, review in pet_reviews.iterrows():
                        review_text = review.get('ReviewText', '').lower()
                        if any(pattern in review_text for pattern in ['three cats', '3 cats', 'four cats', '4 cats', 'two cats', '2 cats']):
                            relevant_reviews.append(review)
                    
                    if relevant_reviews:
                        for i, review in enumerate(relevant_reviews[:10]):
                            context_parts.append(f"Review {i+1}: {review.get('ReviewText', '')}")
                    else:
                        context_parts.append("No specific reviews mentioning multiple pets found.")
            else:
                # For registered pets, use all their reviews
                # First, add reviews that mention gender/weight information
                priority_reviews = []
                other_reviews = []
                
                for _, review in pet_reviews.iterrows():
                    review_text = review.get('ReviewText', '')
                    if any(word in review_text.lower() for word in PRIORITY_REVIEW_KEYWORDS):
                        priority_reviews.append(review)
                    else:
                        other_reviews.append(review)
                
                # Add priority reviews first (up to 10)
                for i, review in enumerate(priority_reviews[:10]):
                    context_parts.append(f"Review {i+1}: {review.get('ReviewText', '')}")
                
                # Add other reviews if we have space (up to 10 total)
                remaining_slots = 10 - len(priority_reviews[:10])
                for i, review in enumerate(other_reviews[:remaining_slots]):
                    context_parts.append(f"Review {len(priority_reviews[:10])+i+1}: {review.get('ReviewText', '')}")
        
        # Add customer order context - filter by pet-appropriate products
        if not customer_orders.empty:
            context_parts.append(f"\nCustomer Order History:")
            
            # Determine pet type for filtering
            pet_type = "UNK"
            if structured_pet_data and structured_pet_data.get('PetType') and structured_pet_data.get('PetType') != 'UNK':
                pet_type = structured_pet_data.get('PetType')
            elif not pet_reviews.empty and pet_name != 'UNK':
                try:
                    pet_type = pet_reviews.iloc[0].get('PetType', 'UNK')
                except Exception:
                    pet_type = "UNK"
            elif pet_name == 'UNK':
                # For UNK pets, infer from context (reviews mention "three cats")
                pet_type = "Cat"
            
            # Filter orders by pet-appropriate products
            filtered_orders = customer_orders.copy()
            if pet_type == "Cat":
                # For cats, exclude dog-specific products
                cat_orders = customer_orders[~customer_orders['ProductName'].str.contains('Dog|dog', case=False, na=False)]
                filtered_orders = cat_orders
                context_parts.append("(Filtered to cat-appropriate products only - excluding dog products)")
            elif pet_type == "Dog":
                # For dogs, exclude cat-specific products
                dog_orders = customer_orders[~customer_orders['ProductName'].str.contains('Cat|cat', case=False, na=False)]
                filtered_orders = dog_orders
                context_parts.append("(Filtered to dog-appropriate products only - excluding cat products)")
            else:
                # For unknown pet types, include all products
                context_parts.append("(All products included - pet type unknown)")
            
            # Group by product and get top ordered products
            if not filtered_orders.empty:
                product_counts = filtered_orders.groupby('ProductName')['Quantity'].sum().sort_values(ascending=False)
                
                context_parts.append(f"Total products in filtered list: {len(filtered_orders)}")
                for i, (product, quantity) in enumerate(product_counts.head(10).items()):
                    context_parts.append(f"Product {i+1}: {product} (Quantity: {quantity})")
            else:
                context_parts.append("No pet-appropriate products found in order history.")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, context: str, pet_name: str) -> str:
        """Create the analysis prompt for the LLM."""
        unk_warning = ""
        if pet_name == 'UNK':
            unk_warning = """

CRITICAL WARNING FOR UNK PETS:
- This pet has NO structured profile data
- All structured fields (Breed, Gender, Birthday, etc.) should be "UNK" with score 0.0
- Only extract information that is EXPLICITLY mentioned in the review text
- DO NOT infer or guess any characteristics
- DO NOT use information from other pets' profiles
- If no specific information is found in reviews, use "UNK" with score 0.0
"""
        
        return f"""
Analyze the following data for pet '{pet_name}' and provide insights in JSON format:

{context}{unk_warning}

IMPORTANT EXTRACTION GUIDELINES:
- USE THE STRUCTURED DATA PROVIDED: If the "Pet Profile Data" section shows specific values (like Breed: Birman, Gender: MALE), use those exact values with high confidence scores (0.9-1.0)
- GENDER: Look for gender/physical indicator words in the review text, OR use the structured data if provided
- WEIGHT: Look for numbers followed by "lbs", "pounds", "weight" in the review text
- BREED: Use the structured data if provided (e.g., "Birman", "Himalayan"), OR look for breed mentions in review text
- SIZE: Infer from weight and breed information (e.g., "large breed", "125 lbs" = "Large")
- PET TYPE: Use the structured data if provided, otherwise infer from context
- MOST ORDERED PRODUCTS: ONLY include products that are appropriate for the pet type. The order history has been pre-filtered to show only pet-appropriate products:
  * For CATS: Only include cat food, cat litter, cat toys, cat treats, cat flea treatment, etc.
  * For DOGS: Only include dog food, dog treats, dog toys, dog dental chews, dog flea treatment, etc.
  * DO NOT include dog products for cats or cat products for dogs
  * DO NOT include generic products that could be for either pet type unless clearly specified
  * CRITICAL: Only categorize products that are actually listed in the "Customer Order History" section above

Please analyze and return a JSON object with the following structure:
{{
    "PetType": "string",
    "PetTypeScore": float,
    "Breed": "string", 
    "BreedScore": float,
    "LifeStage": "string",
    "LifeStageScore": float,
    "Gender": "string",
    "GenderScore": float,
    "SizeCategory": "string",
    "SizeScore": float,
    "Weight": "string",
    "WeightScore": float,
    "Birthday": "string",
    "BirthdayScore": float,
    "PersonalityTraits": ["string"],
    "PersonalityScores": {{"trait": float}},
    "FavoriteProductCategories": ["string"],
    "CategoryScores": {{"category": float}},
    "BrandPreferences": ["string"],
    "BrandScores": {{"brand": float}},
    "DietaryPreferences": ["string"],
    "DietaryScores": {{"preference": float}},
    "BehavioralCues": ["string"],
    "BehavioralScores": {{"behavior": float}},
    "HealthMentions": ["string"],
    "HealthScores": {{"health": float}},
    "MostOrderedProducts": ["string"]
}}

IMPORTANT: If structured data is provided (e.g., Breed: Birman, Gender: MALE), use those exact values with high confidence scores (0.9-1.0). Only use "UNK" if the information is truly not available.
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured format."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_response = json.loads(json_str)
                
                # Post-process to fix product categorization issues
                parsed_response = self._fix_product_categorization(parsed_response)
                
                return parsed_response
            else:
                logger.warning("No JSON found in LLM response")
                return self._get_default_insights()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            return self._get_default_insights()
    
    def _fix_product_categorization(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Fix product categorization to ensure pets only get appropriate products."""
        pet_type = parsed_response.get('PetType', '').lower()
        
        if pet_type == 'dog':
            # For dogs, remove cat-specific categories
            favorite_categories = parsed_response.get('FavoriteProductCategories', [])
            category_scores = parsed_response.get('CategoryScores', {})
            
            # Remove cat-specific categories
            cat_keywords = ['cat', 'litter', 'hairball']
            filtered_categories = []
            filtered_scores = {}
            
            for category in favorite_categories:
                category_lower = category.lower()
                if not any(keyword in category_lower for keyword in cat_keywords):
                    filtered_categories.append(category)
                    if category in category_scores:
                        filtered_scores[category] = category_scores[category]
            
            parsed_response['FavoriteProductCategories'] = filtered_categories
            parsed_response['CategoryScores'] = filtered_scores
            
            # FIX: Also filter MostOrderedProducts for dogs
            most_ordered = parsed_response.get('MostOrderedProducts', [])
            filtered_products = []
            
            for product in most_ordered:
                product_lower = product.lower()
                # Exclude products with cat-specific keywords
                if not any(keyword in product_lower for keyword in ['cat', 'feline', 'litter', 'kitty']):
                    filtered_products.append(product)
            
            parsed_response['MostOrderedProducts'] = filtered_products
            
        elif pet_type == 'cat':
            # For cats, remove dog-specific categories
            favorite_categories = parsed_response.get('FavoriteProductCategories', [])
            category_scores = parsed_response.get('CategoryScores', {})
            
            # Remove dog-specific categories
            dog_keywords = ['dog', 'poop']
            filtered_categories = []
            filtered_scores = {}
            
            for category in favorite_categories:
                category_lower = category.lower()
                if not any(keyword in category_lower for keyword in dog_keywords):
                    filtered_categories.append(category)
                    if category in category_scores:
                        filtered_scores[category] = category_scores[category]
            
            parsed_response['FavoriteProductCategories'] = filtered_categories
            parsed_response['CategoryScores'] = filtered_scores
            
            # FIX: Also filter MostOrderedProducts for cats
            most_ordered = parsed_response.get('MostOrderedProducts', [])
            filtered_products = []
            
            for product in most_ordered:
                product_lower = product.lower()
                # Exclude products with dog-specific keywords
                if not any(keyword in product_lower for keyword in ['dog', 'canine', 'puppy']):
                    filtered_products.append(product)
            
            parsed_response['MostOrderedProducts'] = filtered_products
        
        return parsed_response

    # ============================================================================
    # UTILITY AND HELPER METHODS
    # ============================================================================
    
    def _infer_species_from_orders(self, pet_name: str, orders_df: pd.DataFrame) -> str:
        """Infer pet species from order history when not explicitly mentioned."""
        if orders_df.empty:
            return 'unknown'
        
        # Analyze order products for species-specific items
        product_names = orders_df['ProductName'].fillna('').str.lower()
        
        # Count cat-specific indicators
        cat_indicators = ['cat', 'feline', 'litter', 'kitty']
        cat_score = sum(product_names.str.contains(indicator).sum() for indicator in cat_indicators)
        
        # Count dog-specific indicators  
        dog_indicators = ['dog', 'canine', 'puppy', 'poop', 'dental chew']
        dog_score = sum(product_names.str.contains(indicator).sum() for indicator in dog_indicators)
        
        # Count bird-specific indicators
        bird_indicators = ['bird', 'avian', 'seed', 'cage']
        bird_score = sum(product_names.str.contains(indicator).sum() for indicator in bird_indicators)
        
        # Return most likely species based on product evidence
        scores = {'cat': cat_score, 'dog': dog_score, 'bird': bird_score}
        max_species = max(scores, key=scores.get)
        
        # Only return if there's clear evidence (score > 0)
        if scores[max_species] > 0:
            logger.info(f"🔍 Inferred species '{max_species}' for pet '{pet_name}' from order history (score: {scores[max_species]})")
            return max_species
        
        return 'unknown'
    
    def _get_default_insights(self, pet_name: str = "Unknown") -> Dict[str, Any]:
        """Get default insights structure for pets with no data."""
        return {
            "PetType": "UNK",
            "PetTypeScore": 0.0,
            "Breed": "UNK",
            "BreedScore": 0.0,
            "LifeStage": "UNK",
            "LifeStageScore": 0.0,
            "Gender": "UNK",
            "GenderScore": 0.0,
            "SizeCategory": "UNK",
            "SizeScore": 0.0,
            "Weight": "UNK",
            "WeightScore": 0.0,
            "Birthday": "UNK",
            "BirthdayScore": 0.0,
            "PersonalityTraits": [],
            "PersonalityScores": {},
            "FavoriteProductCategories": [],
            "CategoryScores": {},
            "BrandPreferences": [],
            "BrandScores": {},
            "DietaryPreferences": [],
            "DietaryScores": {},
            "BehavioralCues": [],
            "BehavioralScores": {},
            "HealthMentions": [],
            "HealthScores": {},
            "MostOrderedProducts": []
        }
    
    def _analyze_pet_attributes_with_llm(self, pet_reviews: pd.DataFrame, customer_orders: pd.DataFrame, pet_name: str, structured_pet_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use LLM to analyze pet attributes from reviews and orders."""
        if not self.openai_api_key:
            logger.error("❌ CRITICAL: No OpenAI API key provided. LLM analysis is required for this pipeline.")
            raise ValueError("OpenAI API key is required for pet analysis. Please set OPENAI_API_KEY environment variable.")
        
        try:
            context = self._prepare_llm_context(pet_reviews, customer_orders, pet_name, structured_pet_data)
            prompt = self._create_analysis_prompt(context, pet_name)
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert pet behavior analyst specializing in review-based behavioral insights. Your focus is on extracting detailed personality traits, behavioral patterns, and emotional cues from customer reviews. IMPORTANT: If structured pet data is provided (like Breed, Gender, Pet Type), use those exact values with high confidence scores (0.9-1.0). Extract rich behavioral insights from review text including personality traits, behavioral patterns, emotional states, and owner-pet relationship dynamics. Look for clues like 'girl', 'boy', '125 lbs', 'large breed', 'loves to play', 'anxious', 'protective', etc. in review text. Only use information present in the data. If information is not available, use 'UNK' and score 0. CRITICAL: When categorizing products, ONLY assign products that are appropriate for the pet type. Dogs should only have dog products, cats should only have cat products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            llm_response = response.choices[0].message.content
            return self._parse_llm_response(llm_response)
        except Exception as e:
            logger.error(f"❌ CRITICAL: LLM analysis failed for pet {pet_name}: {e}")
            raise RuntimeError(f"LLM analysis failed for pet {pet_name}. This pipeline requires LLM analysis to function properly.")
    


if __name__ == "__main__":
    """Review and Order Intelligence Agent - Pipeline Integration Only"""
    print("🧠 Review and Order Intelligence Agent")
    print("=" * 50)
    print("This agent is integrated into the main pipeline and uses Snowflake data.")
    print("It cannot be run standalone. Use the main pipeline instead:")
    print("  python chewy_playback_pipeline.py --customers [customer_ids]")