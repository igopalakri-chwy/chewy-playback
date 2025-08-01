#!/usr/bin/env python3
"""
Chewy Playback Pipeline (Unified Version with Snowflake Integration)
Orchestrates the flow of data through all agents, pulling data directly from Snowflake:
1. Review and Order Intelligence Agent (when reviews available)
2. Order Intelligence Agent (when no reviews available)
3. Narrative Generation Agent  
4. Image Generation Agent
"""

import os
import sys
import json
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Add agent directories to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / 'Agents/Review_and_Order_Intelligence_Agent'))
sys.path.append(str(current_dir / 'Agents/Narrative_Generation_Agent'))
sys.path.append(str(current_dir / 'Agents/Image_Generation_Agent'))
sys.path.append(str(current_dir / 'Agents/Breed_Predictor_Agent'))

from Agents.Review_and_Order_Intelligence_Agent.review_order_intelligence_agent import ReviewOrderIntelligenceAgent
from Agents.Narrative_Generation_Agent.pet_letter_llm_system import PetLetterLLMSystem
from Agents.Review_and_Order_Intelligence_Agent.add_confidence_score import ConfidenceScoreCalculator
from Agents.Breed_Predictor_Agent.breed_predictor_agent import BreedPredictorAgent
from Agents.Review_and_Order_Intelligence_Agent.unknowns_analyzer import UnknownsAnalyzer
from Agents.Image_Generation_Agent.image_generation_agent import generate_image_from_prompt
from snowflake_data_connector import SnowflakeDataConnector
import openai
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime

# Custom JSON encoder to handle Decimal and datetime objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)



class ChewyPlaybackPipeline:
    """
    Unified pipeline that orchestrates all agents and pulls data directly from Snowflake.
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the pipeline with all agents and Snowflake connector."""
        # Load environment variables
        load_dotenv()
        
        # Get OpenAI API key
        if openai_api_key:
            self.openai_api_key = openai_api_key
        else:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it as a parameter.")
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Initialize Snowflake connector
        self.snowflake_connector = SnowflakeDataConnector()
        
        # Initialize agents
        self.review_agent = ReviewOrderIntelligenceAgent(self.openai_api_key)
        self.narrative_agent = PetLetterLLMSystem(self.openai_api_key)
        self.breed_predictor_agent = BreedPredictorAgent()
        
        # Set up output directory
        self.output_dir = Path(__file__).parent / "Output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Data caching to avoid running the same Snowflake queries multiple times
        self._customer_data_cache = {}
        
        print("✅ Pipeline initialized with all agents and Snowflake connector")
    
    def _get_all_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """
        Get ALL customer data from Snowflake once and cache it.
        This prevents redundant queries by fetching everything in one go.
        """
        cache_key = (customer_id, None)  # Single cache entry per customer
        
        if cache_key not in self._customer_data_cache:
            print(f"    🔍 Fetching ALL data from Snowflake for customer {customer_id}...")
            # Fetch all queries at once
            customer_data = self.snowflake_connector.get_customer_data(customer_id)
            self._customer_data_cache[cache_key] = customer_data
            print(f"    ✅ Cached ALL data for customer {customer_id} ({len(customer_data)} query results)")
        else:
            print(f"    📋 Using cached ALL data for customer {customer_id}")
        
        return self._customer_data_cache[cache_key]

    def _get_cached_customer_data(self, customer_id: str, query_keys: list = None) -> Dict[str, Any]:
        """
        Get customer data from cache or fetch from Snowflake if not cached.
        This prevents running the same queries multiple times for the same customer.
        """
        # Use the optimized method that fetches all data once
        all_customer_data = self._get_all_customer_data(customer_id)
        
        # If specific query keys requested, filter the data
        if query_keys:
            filtered_data = {}
            for key in query_keys:
                if key in all_customer_data:
                    filtered_data[key] = all_customer_data[key]
            return filtered_data
        else:
            return all_customer_data
    
    def _get_cached_customer_orders_dataframe(self, customer_id: str, query_keys: list = None) -> pd.DataFrame:
        """Get customer orders dataframe from cached data."""
        customer_data = self._get_cached_customer_data(customer_id, query_keys=query_keys or ['get_cust_orders'])
        formatted_data = self.snowflake_connector.format_data_for_pipeline(customer_id, customer_data)
        if formatted_data['order_data'] and len(formatted_data['order_data']) > 0:
            return pd.DataFrame(formatted_data['order_data'])
        else:
            return pd.DataFrame()
    
    def _get_cached_customer_reviews_dataframe(self, customer_id: str, query_keys: list = None) -> pd.DataFrame:
        """Get customer reviews dataframe from cached data."""
        customer_data = self._get_cached_customer_data(customer_id, query_keys=query_keys or ['get_cust_reviews'])
        formatted_data = self.snowflake_connector.format_data_for_pipeline(customer_id, customer_data)
        if formatted_data['review_data'] and len(formatted_data['review_data']) > 0:
            return pd.DataFrame(formatted_data['review_data'])
        else:
            return pd.DataFrame()
    
    def _get_cached_customer_pets_dataframe(self, customer_id: str, query_keys: list = None) -> pd.DataFrame:
        """Get customer pets dataframe from cached data."""
        customer_data = self._get_cached_customer_data(customer_id, query_keys=query_keys or ['get_pet_profiles'])
        formatted_data = self.snowflake_connector.format_data_for_pipeline(customer_id, customer_data)
        if formatted_data['pet_data'] and len(formatted_data['pet_data']) > 0:
            return pd.DataFrame(formatted_data['pet_data'])
        else:
            return pd.DataFrame()
    
    def _get_cached_customer_address(self, customer_id: str, query_keys: list = None) -> Dict[str, str]:
        """Get customer address from cached data."""
        customer_data = self._get_cached_customer_data(customer_id, query_keys=query_keys or ['get_cust_zipcode'])
        address_data = customer_data.get('get_cust_zipcode', [])
        if address_data:
            return {
                'zip_code': str(address_data[0].get('CUSTOMER_ADDRESS_ZIP', '')),
                'city': str(address_data[0].get('CUSTOMER_ADDRESS_CITY', ''))
            }
        return {'zip_code': '', 'city': ''}
    
    def clear_cache(self):
        """Clear the customer data cache."""
        self._customer_data_cache.clear()
        print("✅ Customer data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total_queries_saved = 0
        for cache_key, cache_data in self._customer_data_cache.items():
            customer_id, query_keys = cache_key
            if query_keys is None:  # Single entry per customer
                total_queries_saved += 10  # All 10 queries saved
            else:  # Legacy multiple entries
                total_queries_saved += len(query_keys)
        
        return {
            'cached_customers': len(self._customer_data_cache),
            'total_queries_saved': total_queries_saved,
            'cache_efficiency': f"{(total_queries_saved / (len(self._customer_data_cache) * 10)) * 100:.1f}%" if self._customer_data_cache else "0%"
        }
    
    def preprocess_data(self):
        """Data preprocessing is no longer needed - data comes directly from Snowflake."""
        print("✅ Data preprocessing skipped - using Snowflake data connector")
    
    def _check_customer_has_reviews(self, customer_id: str) -> bool:
        """Check if a customer has any reviews using cached data."""
        try:
            reviews_df = self._get_cached_customer_reviews_dataframe(customer_id, query_keys=['get_cust_reviews'])
            return not reviews_df.empty
        except Exception as e:
            print(f"Error checking reviews for customer {customer_id}: {e}")
            return False
    
    def run_intelligence_agent(self, customer_ids: List[str] = None) -> Dict[str, Any]:
        """Run the appropriate intelligence agent based on whether customers have reviews."""
        print("\n🧠 Running Intelligence Agent...")
        
        if customer_ids:
            print(f"Processing {len(customer_ids)} specified customers...")
            results = {}
            
            for customer_id in customer_ids:
                try:
                    has_reviews = self._check_customer_has_reviews(customer_id)
                    
                    if has_reviews:
                        print(f"  🐾 Customer {customer_id} has reviews - using Review and Order Intelligence Agent")
                        # Use the review-based agent
                        customer_result = self._run_review_agent_for_customer(customer_id)
                        # Add agent type indicator
                        if isinstance(customer_result, dict):
                            customer_result['_agent_type'] = 'review_based'
                        # Always add the result, even if empty (no pets)
                        results[customer_id] = customer_result
                    else:
                        print(f"  🐾 Customer {customer_id} has no reviews - using Order Intelligence Agent")
                        # Use the order-only agent
                        customer_result = self._run_order_agent_for_customer(customer_id)
                        # Add agent type indicator
                        if isinstance(customer_result, dict):
                            customer_result['_agent_type'] = 'order_based'
                        # Always add the result, even if empty (no pets)
                        results[customer_id] = customer_result
                    
                except Exception as e:
                    print(f"  ❌ Error processing customer {customer_id}: {e}")
                    continue
        else:
            # Process all customers - this would be more complex, so for now we'll skip
            print("Processing all customers is not supported in this version. Please specify individual customer IDs.")
            results = {}
        
        print(f"✅ Generated profiles for {len(results)} customers")
        
        # Add confidence scores to all results
        print("\n🎯 Adding confidence scores to profiles...")
        calculator = ConfidenceScoreCalculator()
        
        for customer_id, customer_data in results.items():
            # Handle different data structures
            if isinstance(customer_data, dict) and 'pets' in customer_data:
                pets_data = customer_data['pets']
                customer_confidence_score = customer_data.get('cust_confidence_score', 0.0)
            else:
                pets_data = customer_data
                customer_confidence_score = 0.0
            
            # Calculate confidence scores for this customer's pets
            pet_confidence_scores = []
            for pet_name, pet_data in pets_data.items():
                # Handle special case: generic playback eligible customers
                if pet_name == '_generic_playback_eligible':
                    generic_confidence = pet_data.get('confidence_score', 0.4)
                    pet_confidence_scores.append(generic_confidence)
                    print(f"  📊 {customer_id}/{pet_name}: generic playback confidence = {generic_confidence:.3f}")
                    continue
                
                # Skip other metadata fields that start with underscore
                if pet_name.startswith('_'):
                    print(f"  📊 {customer_id}/{pet_name}: skipping metadata field")
                    continue
                
                # Ensure pet_data is a dictionary
                if not isinstance(pet_data, dict):
                    print(f"  ⚠️ {customer_id}/{pet_name}: pet_data is not a dictionary, skipping")
                    continue
                
                confidence_score = calculator.calculate_confidence_score(pet_data)
                pet_data['confidence_score'] = confidence_score
                pet_confidence_scores.append(confidence_score)
                print(f"  📊 {customer_id}/{pet_name}: confidence_score = {confidence_score:.3f}")
            
            # Calculate customer confidence score
            if pet_confidence_scores:
                customer_confidence_score = sum(pet_confidence_scores) / len(pet_confidence_scores)
            else:
                customer_confidence_score = 0.0

            # Set gets_playback and gets_personalized flags
            if customer_confidence_score > 0.6:
                gets_playback = True
                # Check if customer has enough orders for personalized playback
                try:
                    orders_df = self._get_cached_customer_orders_dataframe(customer_id, query_keys=['get_cust_orders'])
                    order_count = len(orders_df)
                    if order_count >= 5:
                        gets_personalized = True
                        print(f"    ✅ Customer {customer_id} has {order_count} orders - eligible for personalized playback")
                    else:
                        gets_personalized = False
                        print(f"    ⚠️ Customer {customer_id} has only {order_count} orders - using generic playback (minimum 5 required)")
                except Exception as e:
                    print(f"    ⚠️ Could not check order count for customer {customer_id}: {e}")
                    gets_personalized = False
            elif customer_confidence_score > 0.3:
                gets_playback = True
                gets_personalized = False
            else:
                gets_playback = False
                gets_personalized = False

            results[customer_id] = {
                'pets': pets_data,
                'cust_confidence_score': customer_confidence_score,
                'gets_playback': gets_playback,
                'gets_personalized': gets_personalized
            }
            print(f"  🏠 {customer_id}: customer_confidence_score = {customer_confidence_score:.3f}, gets_playback = {gets_playback}, gets_personalized = {gets_personalized}")
        
        print("✅ Confidence scores added to all profiles")
        return results
    
    def _run_review_agent_for_customer(self, customer_id: str) -> Dict[str, Any]:
        """Run the Review and Order Intelligence Agent for a specific customer using cached data, always using structured Snowflake pet profile fields as primary source."""
        print(f"    📋 Using cached data for customer {customer_id}...")
        
        # Get customer pets from cached data
        pets_df = self._get_cached_customer_pets_dataframe(customer_id, query_keys=['get_pet_profiles'])
        if pets_df.empty:
            print(f"    ⚠️ No pets found for customer {customer_id}")
            # Return empty pet profile instead of None
            return {}
        
        customer_pets = pets_df['PetName'].unique().tolist()
        
        # Get customer orders from cached data
        orders_df = self._get_cached_customer_orders_dataframe(customer_id, query_keys=['get_cust_orders'])
        
        # Get customer reviews from cached data
        reviews_df = self._get_cached_customer_reviews_dataframe(customer_id, query_keys=['get_cust_reviews'])
        
        # Use the new cached data method
        customer_results = self.review_agent.analyze_customer_with_cached_data(
            customer_id, pets_df, orders_df, reviews_df
        )
        return customer_results
    
    def _analyze_orders_with_llm(self, orders_df: pd.DataFrame, customer_id: str) -> Dict[str, Any]:
        """Analyze customer orders using LLM to generate pet insights."""
        if orders_df.empty:
            raise ValueError(f"No order data available for customer {customer_id}. LLM analysis requires order data.")
        
        # Prepare context from order data
        context = self._prepare_order_context(orders_df)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(context, customer_id)
        
        try:
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI expert at analyzing pet product orders to understand pets and their preferences. Provide insights based only on order history data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return self._parse_llm_response(result, customer_id)
            
        except Exception as e:
            print(f"❌ CRITICAL: LLM analysis failed for customer {customer_id}: {e}")
            raise RuntimeError(f"LLM analysis failed for customer {customer_id}. This pipeline requires LLM analysis to function properly.")
    
    def _prepare_order_context(self, orders_df: pd.DataFrame) -> str:
        """Prepare context data from order history for LLM analysis."""
        context_parts = []
        
        # Add order summary
        context_parts.append("Customer Order History:")
        context_parts.append(f"Total Orders: {len(orders_df)}")
        
        # Most ordered products (using Snowflake format)
        if 'ProductName' in orders_df.columns:
            products = orders_df['ProductName'].value_counts().head(10)
            context_parts.append(f"Most Ordered Products: {dict(products)}")
        
        # Product categories (if available)
        if 'ProductCategory' in orders_df.columns:
            categories = orders_df['ProductCategory'].value_counts().head(10)
            context_parts.append(f"Top Product Categories: {dict(categories)}")
        
        # Brands (if available)
        if 'Brand' in orders_df.columns:
            brands = orders_df['Brand'].value_counts().head(10)
            context_parts.append(f"Top Brands: {dict(brands)}")
        
        # Order dates (if available)
        if 'OrderDate' in orders_df.columns:
            context_parts.append(f"Order Date Range: {orders_df['OrderDate'].min()} to {orders_df['OrderDate'].max()}")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, context: str, customer_id: str) -> str:
        """Create prompt for LLM analysis of order data."""
        return f"""Analyze the following customer order history and provide insights about their pets. Since we don't have review data, focus on inferring pet characteristics from product choices.

Customer ID: {customer_id}

{context}

Based on this order history, please provide insights in the following JSON format:

{{
    "PetType": "dog/cat/other (inferred from products)",
    "PetTypeScore": 0.8,
    "Breed": "inferred breed or 'Mixed'",
    "BreedScore": 0.6,
    "LifeStage": "puppy/kitten/adult/senior",
    "LifeStageScore": 0.7,
    "Gender": "male/female/unknown",
    "GenderScore": 0.5,
    "SizeCategory": "small/medium/large",
    "SizeScore": 0.6,
    "Weight": "estimated weight range",
    "WeightScore": 0.4,
    "Birthday": "unknown",
    "BirthdayScore": 0.0,
    "PersonalityTraits": ["playful", "curious", "affectionate"],
    "PersonalityScores": {{"playful": 0.8, "curious": 0.7, "affectionate": 0.9}},
    "FavoriteProductCategories": ["toys", "food", "treats"],
    "CategoryScores": {{"toys": 0.9, "food": 0.8, "treats": 0.7}},
    "BrandPreferences": ["Chewy", "Blue Buffalo"],
    "BrandScores": {{"Chewy": 0.9, "Blue Buffalo": 0.8}},
    "DietaryPreferences": ["grain-free", "high-protein"],
    "DietaryScores": {{"grain-free": 0.8, "high-protein": 0.7}},
    "BehavioralCues": ["loves toys", "enjoys treats"],
    "BehavioralScores": {{"loves toys": 0.9, "enjoys treats": 0.8}},
    "HealthMentions": ["healthy", "active"],
    "HealthScores": {{"healthy": 0.8, "active": 0.7}},
    "MostOrderedProducts": ["product1", "product2", "product3"]
}}

Focus on:
1. Product categories that indicate pet type (dog food vs cat food)
2. Product types that suggest life stage (puppy food, senior care)
3. Brand preferences and quality indicators
4. Product variety that suggests personality traits
5. Order frequency and patterns

Provide realistic scores (0.0-1.0) based on confidence in the inference."""

    def _parse_llm_response(self, response: str, customer_id: str) -> Dict[str, Any]:
        """Parse LLM response into structured insights."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                print(f"❌ CRITICAL: Could not parse JSON from LLM response for customer {customer_id}")
                raise RuntimeError(f"Failed to parse LLM response for customer {customer_id}. This pipeline requires LLM analysis to function properly.")
        except Exception as e:
            print(f"❌ CRITICAL: Error parsing LLM response for customer {customer_id}: {e}")
            raise RuntimeError(f"Failed to parse LLM response for customer {customer_id}. This pipeline requires LLM analysis to function properly.")
    
    def _run_order_agent_for_customer(self, customer_id: str) -> Dict[str, Any]:
        """Run the Order Intelligence Agent for a specific customer using cached data."""
        print(f"    📋 Using cached data for customer {customer_id}...")
        
        # Get customer orders from cached data
        orders_df = self._get_cached_customer_orders_dataframe(customer_id, query_keys=['get_cust_orders'])
        
        if orders_df.empty:
            print(f"    ⚠️ No orders found for customer {customer_id}")
            return {}
        
        # Get customer pets from cached data
        pets_df = self._get_cached_customer_pets_dataframe(customer_id, query_keys=['get_pet_profiles'])
        
        # Use consolidated LLM analysis method for order-based insights
        insights = self._analyze_orders_with_llm(orders_df, customer_id)
        
        # Order Agent focuses on product-based insights, not behavioral analysis
        # Set personality traits to minimal since we don't have review data
        if 'PersonalityTraits' in insights:
            insights['PersonalityTraits'] = ['Product-focused analysis']
        if 'PersonalityScores' in insights:
            insights['PersonalityScores'] = {'Product-focused analysis': 0.3}
        if 'BehavioralCues' in insights:
            insights['BehavioralCues'] = ['Inferred from product choices']
        if 'BehavioralScores' in insights:
            insights['BehavioralScores'] = {'Inferred from product choices': 0.3}
        
        # Use pet profile data from Snowflake instead of extracting from order data
        customer_results = {}
        if not pets_df.empty:
            for _, pet_row in pets_df.iterrows():
                pet_name = pet_row.get('PetName', 'Unknown Pet')
                customer_results[pet_name] = {
                    "PetName": pet_name,
                    "PetType": pet_row.get("PetType", "UNK"),
                    "PetTypeScore": 1.0 if pet_row.get("PetType") != "UNK" else 0.0,
                    "Breed": pet_row.get("PetBreed", "UNK"),
                    "BreedScore": 1.0 if pet_row.get("PetBreed") != "UNK" else 0.0,
                    "LifeStage": pet_row.get("PetAge", "UNK"),
                    "LifeStageScore": 1.0 if pet_row.get("PetAge") != "UNK" else 0.0,
                    "Gender": pet_row.get("Gender", "UNK"),
                    "GenderScore": 1.0 if pet_row.get("Gender") != "UNK" else 0.0,
                    "SizeCategory": "UNK",  # Not available in current Snowflake data
                    "SizeScore": 0.0,
                    "Weight": pet_row.get("Weight", "UNK"),
                    "WeightScore": 1.0 if pet_row.get("Weight") != "UNK" else 0.0,
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
                    "MostOrderedProducts": insights.get("MostOrderedProducts", []),
                    "ConfidenceScore": insights.get("ConfidenceScore", 0.0)
                }
        else:
            # No pet profiles available - check if customer qualifies for generic playback
            print(f"    ⚠️ No pet profiles found for customer {customer_id}")
            order_count = len(orders_df)
            
            if order_count >= 5:
                print(f"    ✅ Customer has {order_count} orders - eligible for generic playback")
                print(f"    💡 Suggesting profile completion for personalized experience")
                
                # Create a placeholder profile that signals generic playback eligibility
                return {
                    "_generic_playback_eligible": {
                        "reason": "no_pet_profiles_but_active_customer",
                        "order_count": order_count,
                        "message": "Complete your pet profiles for personalized insights!",
                        "confidence_score": 0.4  # Above 0.3 threshold for generic playback
                    }
                }
            else:
                print(f"    ⚠️ Customer has only {order_count} orders - insufficient for generic playback (minimum 5 required)")
                return {}
        
        return customer_results
    
    def run_narrative_generation_agent(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Narrative Generation Agent to create letters, image prompts, and personality badges."""
        print("\n✍️ Running Narrative Generation Agent...")
        
        narrative_results = {}
        
        for customer_id, customer_data in enriched_profiles.items():
            print(f"  📝 Generating narratives for customer {customer_id}...")
            
            # Skip generic customers - they shouldn't get personalized content
            if not customer_data.get('gets_personalized', False):
                print(f"  ⏭️ Skipping narrative generation for generic customer {customer_id}")
                continue
            
            # Handle new structure where pets data might be nested
            if isinstance(customer_data, dict) and 'pets' in customer_data:
                pets_data = customer_data['pets']
                customer_confidence_score = customer_data.get('cust_confidence_score', 0.0)
            else:
                # Handle old structure for backward compatibility
                pets_data = customer_data
                customer_confidence_score = 0.0
            
            try:
                # Prepare data for the new narrative agent
                pet_data = {customer_id: pets_data}
                
                # Always get order data for ZIP code extraction
                orders = self._get_customer_orders_for_narrative(customer_id)
                
                # Check if customer has reviews
                has_reviews = self._check_customer_has_reviews(customer_id)
                
                if has_reviews:
                    # Get review data for this customer
                    reviews = self._get_customer_reviews(customer_id)
                    secondary_data = {"reviews": reviews, "order_history": orders}
                else:
                    # Use order data for narrative generation
                    secondary_data = {"order_history": orders}
                
                # Generate narrative using the new agent
                narrative_output = self.narrative_agent.generate_output(pet_data, secondary_data)
                
                # Extract ZIP aesthetics from the narrative agent
                zip_aesthetics = narrative_output.get('zip_aesthetics', {})
                
                customer_narratives = {
                    'customer_id': customer_id,
                    'pets': pets_data,
                    'collective_letter': narrative_output.get('letter', ''),
                    'collective_visual_prompt': narrative_output.get('visual_prompt', ''),
                    'personality_badge': narrative_output.get('personality_badge', {}),
                    'zip_aesthetics': zip_aesthetics,
                    'cust_confidence_score': customer_confidence_score
                }
                
                print(f"    ✅ Generated collective letter from all pets")
                print(f"    ✅ Generated collective visual prompt for all pets")
                print(f"    🏆 Assigned personality badge: {narrative_output.get('personality_badge', {}).get('badge', 'Unknown')}")
                
            except Exception as e:
                print(f"    ❌ Error generating narratives: {e}")
                # Don't create fake narratives - return empty results
                customer_narratives = {
                    'customer_id': customer_id,
                    'pets': pets_data,
                    'collective_letter': None,
                    'collective_visual_prompt': None,
                    'personality_badge': None,
                    'zip_aesthetics': None,
                    'cust_confidence_score': customer_confidence_score
                }
            
            narrative_results[customer_id] = customer_narratives
        
        print(f"✅ Generated narratives for {len(narrative_results)} customers")
        return narrative_results
    
    def run_breed_predictor_agent(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Breed Predictor Agent for dogs with unknown/mixed breeds using pipeline data."""
        print("\n🐕 Running Breed Predictor Agent...")
        
        breed_predictions = {}
        total_pets_checked = 0
        eligible_pets_found = 0
        
        for customer_id, customer_data in enriched_profiles.items():
            print(f"  🔍 Checking pets for customer {customer_id}...")
            
            # Handle different data structures
            if isinstance(customer_data, dict) and 'pets' in customer_data:
                pets_data = customer_data['pets']
            else:
                pets_data = customer_data
            
            customer_predictions = []
            
            # Get order history from cached data (already loaded by pipeline)
            orders_df = self._get_cached_customer_orders_dataframe(customer_id)
            customer_orders = []
            
            if not orders_df.empty:
                # Convert to format expected by breed predictor
                for _, row in orders_df.iterrows():
                    order = {
                        'item_name': row.get('ProductName', 'Unknown'),
                        'category': 'Unknown',
                        'order_date': '',
                        'quantity': row.get('Quantity', 1),
                        'brand': 'Chewy'
                    }
                    customer_orders.append(order)
            
            # Check each pet in the enriched profile
            for pet_name, pet_data in pets_data.items():
                # Skip metadata fields that start with underscore (including generic playback)
                if pet_name.startswith('_'):
                    if pet_name == '_generic_playback_eligible':
                        print(f"    ⏭️ {pet_name}: Skipped (generic playback customer - no breed prediction needed)")
                    else:
                        print(f"    ⏭️ {pet_name}: Skipped (metadata field)")
                    continue
                
                # Ensure pet_data is a dictionary
                if not isinstance(pet_data, dict):
                    print(f"    ⏭️ {pet_name}: Skipped (not a dictionary)")
                    continue
                
                total_pets_checked += 1
                
                # Check if this pet qualifies for breed prediction
                pet_type = pet_data.get('PetType', '').lower()
                pet_breed = pet_data.get('Breed', '').lower()
                
                # Only predict for dogs with unknown/mixed breeds
                is_dog = pet_type == 'dog'
                unknown_indicators = ['mixed', 'unknown', 'mix', 'unk', 'null']
                has_unknown_breed = (
                    any(indicator in pet_breed.lower() for indicator in unknown_indicators) or 
                    pet_breed.strip() == '' or
                    pet_breed.lower() == 'unk'
                )
                
                if is_dog and has_unknown_breed:
                    eligible_pets_found += 1
                    print(f"    🐕 {pet_name}: Eligible for breed prediction (Type: {pet_type}, Breed: {pet_breed})")
                    
                    try:
                        # Prepare pet data for breed predictor
                        pet_profile = {
                            'PetName': pet_name,
                            'PetType': pet_data.get('PetType', 'UNK'),
                            'Breed': pet_data.get('Breed', 'UNK'),
                            'Gender': pet_data.get('Gender', 'UNK'),
                            'LifeStage': pet_data.get('LifeStage', 'UNK'),
                            'SizeCategory': pet_data.get('SizeCategory', 'UNK'),
                            'Weight': pet_data.get('Weight', 'UNK'),
                            'confidence_score': pet_data.get('confidence_score', 0.0)
                        }
                        
                        # Run breed prediction for this specific pet
                        prediction_result = self.breed_predictor_agent.predict_breed_for_pet_with_orders(
                            customer_id=customer_id,
                            pet_name=pet_name,
                            pet_data=pet_profile,
                            customer_orders=customer_orders
                        )
                        
                        if prediction_result:
                            customer_predictions.append({
                                'pet_name': pet_name,
                                'customer_id': customer_id,
                                'prediction': prediction_result,
                                'timestamp': prediction_result.get('timestamp', ''),
                                'predicted_breed': prediction_result.get('predicted_breed', 'Unknown'),
                                'breed_percentages': prediction_result.get('breed_percentages', {}),
                                'confidence_score': prediction_result.get('confidence', {}).get('score', 0),
                                'confidence_level': prediction_result.get('confidence', {}).get('level', 'Unknown'),
                                'reasoning': prediction_result.get('reasoning', 'No reasoning provided'),
                                'data_used': prediction_result.get('data_used', {})
                            })
                            print(f"      ✅ Prediction completed for {pet_name}")
                        else:
                            print(f"      ⚠️ No prediction result for {pet_name}")
                            
                    except Exception as e:
                        print(f"      ❌ Error predicting breed for {pet_name}: {e}")
                        continue
                        
                else:
                    # Log why pet was skipped
                    if not is_dog:
                        print(f"    ⏭️ {pet_name}: Skipped (not a dog, type: {pet_type})")
                    elif not has_unknown_breed:
                        print(f"    ⏭️ {pet_name}: Skipped (known breed: {pet_breed})")
            
            # Save customer predictions if any were made
            if customer_predictions:
                # Use the first prediction for backward compatibility, but save all
                if len(customer_predictions) == 1:
                    breed_predictions[customer_id] = customer_predictions[0]
                else:
                    # Multiple predictions - save as list
                    breed_predictions[customer_id] = {
                        'customer_id': customer_id,
                        'multiple_predictions': customer_predictions,
                        'total_predictions': len(customer_predictions)
                    }
                print(f"    ✅ Saved {len(customer_predictions)} breed prediction(s) for customer {customer_id}")
            else:
                print(f"    ℹ️ No eligible pets found for customer {customer_id}")
        
        print(f"\n📊 Breed Prediction Summary:")
        print(f"   Total pets checked: {total_pets_checked}")
        print(f"   Eligible pets found: {eligible_pets_found}")
        print(f"   Customers with predictions: {len(breed_predictions)}")
        print(f"✅ Breed predictions completed")
        return breed_predictions
    
    def _get_customer_reviews(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get review data for a specific customer from cached data."""
        try:
            reviews_df = self._get_cached_customer_reviews_dataframe(customer_id, query_keys=['get_cust_reviews'])
            
            # Convert to list of dictionaries
            reviews_list = []
            for _, row in reviews_df.iterrows():
                review = {
                    'product_name': 'Unknown',  # Not available in current query
                    'review_text': row.get('ReviewText', ''),
                    'rating': 0,  # Not available in current query
                    'pet_name': ''  # Not available in current query
                }
                reviews_list.append(review)
            
            return reviews_list
        except Exception as e:
            print(f"Error getting reviews for customer {customer_id}: {e}")
            return []
    
    def _get_customer_orders_for_narrative(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer orders for narrative generation."""
        try:
            orders_df = self._get_cached_customer_orders_dataframe(customer_id, query_keys=['get_cust_orders'])
            # Get customer address from cached data
            address_data = self._get_cached_customer_address(customer_id, query_keys=['get_cust_zipcode'])

            # Convert to list of dictionaries
            orders_list = []
            for _, row in orders_df.iterrows():
                order = {
                    'product_name': row.get('ProductName', 'Unknown'),
                    'zip_code': address_data.get('zip_code', ''),
                    'pet_name': ''  # Not available in current query structure
                }
                orders_list.append(order)

            return orders_list
        except Exception as e:
            print(f"Error getting orders for customer {customer_id}: {e}")
            return []
    
    def run_image_generation_agent(self, narrative_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Image Generation Agent using the modular image_generation_agent.py approach."""
        print("\n🎨 Running Image Generation Agent...")
        
        image_results = {}
        
        for customer_id, customer_data in narrative_results.items():
            print(f"  🖼️ Generating collective image for customer {customer_id}...")
            
            collective_visual_prompt = customer_data.get('collective_visual_prompt', '')
            zip_aesthetics = customer_data.get('zip_aesthetics', {})
            
            if collective_visual_prompt:
                try:
                    # Extract specific pet data for hyper-specific instructions
                    pets_data = customer_data.get('pets', {})
                    pet_details = []
                    for pet_name, pet_info in pets_data.items():
                        if not pet_name.startswith('_'):  # Skip metadata fields
                            pet_type = pet_info.get('PetType', 'unknown')
                            breed = pet_info.get('Breed', 'unknown')
                            weight = pet_info.get('Weight', 'unknown')
                            age = pet_info.get('LifeStage', 'unknown')
                            pet_details.append({
                                'name': pet_name,
                                'type': pet_type,
                                'breed': breed,
                                'weight': weight,
                                'age': age
                            })
                    
                    # Use the superior image_generation_agent.py approach without visual prompt
                    image_url = generate_image_from_prompt(
                        api_key=self.openai_api_key,
                        output_path=None,  # Don't save to file here, handle that in save_outputs
                        zip_aesthetics=zip_aesthetics,
                        pet_details=pet_details  # All pet data handled dynamically
                    )
                    
                    if image_url:
                        image_results[customer_id] = image_url
                        print(f"    ✅ Generated collective image for all pets")
                    else:
                        print(f"    ❌ Failed to generate image for customer {customer_id}")
                        image_results[customer_id] = None
                    
                except Exception as e:
                    print(f"    ❌ Error generating collective image: {e}")
                    image_results[customer_id] = None
            else:
                print(f"    ❌ No collective visual prompt found for customer {customer_id}")
                image_results[customer_id] = None
        
        print(f"✅ Generated collective images for {len(image_results)} customers")
        return image_results
    
    def save_outputs(self, enriched_profiles: Dict[str, Any], 
                    narrative_results: Dict[str, Any], 
                    image_results: Dict[str, Any],
                    breed_predictions: Dict[str, Any] = None):
        """Save all outputs to the Output directory structure."""
        print("\n💾 Saving outputs...")
        
        for customer_id in enriched_profiles.keys():
            # Create customer directory
            customer_dir = self.output_dir / customer_id
            customer_dir.mkdir(exist_ok=True)
            
            # Handle new structure where pets data might be nested
            customer_data = enriched_profiles[customer_id]
            if isinstance(customer_data, dict) and 'pets' in customer_data:
                pets_data = customer_data['pets']
                customer_confidence_score = customer_data.get('cust_confidence_score', 0.0)
            else:
                # Handle old structure for backward compatibility
                pets_data = customer_data
                customer_confidence_score = 0.0
            
            # Save enriched pet profile JSON (include customer confidence score and flags)
            profile_data = {
                **pets_data,
                'cust_confidence_score': customer_confidence_score,
                'gets_playback': customer_data.get('gets_playback', False),
                'gets_personalized': customer_data.get('gets_personalized', False)
            }
            
            # Handle pet count analysis metadata from enhanced detection
            if '_pet_count_analysis' in pets_data:
                pet_count_analysis = pets_data.pop('_pet_count_analysis')
                profile_data['pet_count_analysis'] = {
                    'original_counts': pet_count_analysis.get('original_counts', {}),
                    'detected_counts': pet_count_analysis.get('detected_counts', {}),
                    'updated_counts': pet_count_analysis.get('updated_counts', {}),
                    'additional_pets_detected': len(pet_count_analysis.get('additional_pets', []))
                }
            profile_path = customer_dir / "enriched_pet_profile.json"
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            # Save letters (only for personalized playback)
            if narrative_results[customer_id] and 'collective_letter' in narrative_results[customer_id]:
                letters_path = customer_dir / "pet_letters.txt"
                with open(letters_path, 'w') as f:
                    f.write(narrative_results[customer_id]['collective_letter'])
                    f.write("\n\n")
            
            # Save visual prompt (only for personalized playback)
            if narrative_results[customer_id] and 'collective_visual_prompt' in narrative_results[customer_id]:
                visual_prompt_path = customer_dir / "visual_prompt.txt"
                with open(visual_prompt_path, 'w') as f:
                    f.write(f"Visual Prompt for Customer {customer_id}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(narrative_results[customer_id]['collective_visual_prompt'])
                    f.write("\n\n")
            
            # Save personality badge information (only for personalized playback)
            if narrative_results[customer_id] and 'personality_badge' in narrative_results[customer_id]:
                badge_info = narrative_results[customer_id]['personality_badge']
                if badge_info:
                    badge_path = customer_dir / "personality_badge.json"
                    with open(badge_path, 'w') as f:
                        json.dump(badge_info, f, indent=2)
                    
                    # Copy the badge image if it exists
                    badge_icon = badge_info.get('icon_png', '')
                    if badge_icon:
                        source_badge_path = Path("Agents/Narrative_Generation_Agent") / badge_icon
                        if source_badge_path.exists():
                            dest_badge_path = customer_dir / badge_icon
                            shutil.copy2(source_badge_path, dest_badge_path)
                            print(f"    🏆 Saved personality badge: {badge_info.get('badge', 'Unknown')}")
            
            # Save ZIP aesthetics information (only for personalized playback)
            if narrative_results[customer_id] and 'zip_aesthetics' in narrative_results[customer_id]:
                zip_aesthetics = narrative_results[customer_id]['zip_aesthetics']
                if zip_aesthetics:
                    zip_aesthetics_path = customer_dir / "zip_aesthetics.json"
                    with open(zip_aesthetics_path, 'w') as f:
                        json.dump(zip_aesthetics, f, indent=2)
                    print(f"    🗺️ Saved ZIP aesthetics: {zip_aesthetics.get('visual_style', 'Unknown')}, {zip_aesthetics.get('color_texture', 'Unknown')}, {zip_aesthetics.get('art_style', 'Unknown')}")
            
            # Save consolidated queries for ALL customers (both generic and personalized)
            if customer_data.get('gets_playback', False):
                try:
                    # Get all 6 query data from cache
                    query_data = self._get_cached_customer_data(customer_id, query_keys=[
                        'get_amt_donated',
                        'get_cudd_month', 
                        'get_total_months',
                        'get_autoship_savings',
                        'get_most_ordered',
                        'get_yearly_food_count'
                    ])
                    
                    # Save consolidated queries to single JSON file
                    self._save_consolidated_queries(customer_id, query_data, customer_dir)
                        
                except Exception as e:
                    print(f"    ⚠️ Error saving consolidated queries for customer {customer_id}: {e}")
            
            # Save breed predictions if available
            if breed_predictions and customer_id in breed_predictions:
                breed_path = customer_dir / "predicted_breed.json"
                with open(breed_path, 'w') as f:
                    json.dump(breed_predictions[customer_id], f, indent=2)
                
                # Handle new simplified format
                if isinstance(breed_predictions[customer_id], dict) and 'pet_name' in breed_predictions[customer_id]:
                    # New simplified format - single prediction
                    pet_name = breed_predictions[customer_id]['pet_name']
                    predicted_breed = breed_predictions[customer_id]['predicted_breed']
                    # Handle nested confidence structure
                    if 'prediction' in breed_predictions[customer_id] and 'confidence' in breed_predictions[customer_id]['prediction']:
                        confidence = breed_predictions[customer_id]['prediction']['confidence'].get('score', 0)
                    else:
                        confidence = breed_predictions[customer_id].get('confidence_score', 0)
                    print(f"    🐕 Saved breed prediction for {pet_name}: {predicted_breed} (confidence: {confidence})")
                else:
                    # Old format - multiple predictions
                    print(f"    🐕 Saved breed predictions for {len(breed_predictions[customer_id])} pets")
            
            # Save collective image (handle both URL and base64 data)
            if customer_id in image_results and image_results[customer_id]:
                images_dir = customer_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                try:
                    image_path = images_dir / "collective_pet_portrait.png"
                    
                    if isinstance(image_results[customer_id], str):
                        # Could be URL or base64 string
                        if image_results[customer_id].startswith('http'):
                            # URL response - download the image
                            response = requests.get(image_results[customer_id])
                            if response.status_code == 200:
                                with open(image_path, 'wb') as f:
                                    f.write(response.content)
                                print(f"    💾 Saved collective image for all pets")
                            else:
                                print(f"    ❌ Failed to download image for customer {customer_id} (Status: {response.status_code})")
                        else:
                            # Base64 string - decode and save
                            import base64
                            image_bytes = base64.b64decode(image_results[customer_id])
                            with open(image_path, 'wb') as f:
                                f.write(image_bytes)
                            print(f"    💾 Saved collective image for all pets")
                    elif isinstance(image_results[customer_id], bytes):
                        # Base64 bytes - save directly
                        with open(image_path, 'wb') as f:
                            f.write(image_results[customer_id])
                        print(f"    💾 Saved collective image for all pets")
                    else:
                        print(f"    ❌ Unknown image data type for customer {customer_id}: {type(image_results[customer_id])}")
                except Exception as e:
                    print(f"    ❌ Error saving collective image: {e}")
            

            print(f"  ✅ Saved outputs for customer {customer_id}")
    
    def _save_consolidated_queries(self, customer_id: str, customer_data: Dict[str, Any], customer_dir: Path):
        """Save all 6 query outputs into a single JSON file named with the customer ID."""
        try:
            consolidated_data = {}
            
            # 1. Amount Donated
            donation_results = customer_data.get('get_amt_donated', [])
            amt_donated = 0.0
            if donation_results and isinstance(donation_results, list):

                
                try:
                    amt = donation_results[0].get('AMT_DONATED')
                    if amt is not None:
                        amt_donated = float(amt)
                except Exception:
                    amt_donated = 0.0
            consolidated_data['amount_donated'] = amt_donated
            
            # 2. Cuddliest Month
            cuddliest_results = customer_data.get('get_cudd_month', [])
            cuddliest_month = None
            if cuddliest_results and isinstance(cuddliest_results, list):
                try:
                    month = cuddliest_results[0].get('MONTH')
                    if month:
                        cuddliest_month = month
                except Exception:
                    cuddliest_month = None
            consolidated_data['cuddliest_month'] = cuddliest_month
            
            # 3. Total Months
            months_results = customer_data.get('get_total_months', [])
            months_with_chewy = None
            if months_results and isinstance(months_results, list):
                try:
                    months = months_results[0].get('MONTHS_WITH_CHEWY')
                    if months is not None:
                        months_with_chewy = int(months)
                except Exception:
                    months_with_chewy = None
            consolidated_data['total_months'] = months_with_chewy
            
            # 4. Autoship Savings
            autoship_results = customer_data.get('get_autoship_savings', [])
            amt_saved = 0.0
            if autoship_results and isinstance(autoship_results, list):
                try:
                    savings = autoship_results[0].get('LIFETIME_SAVINGS')
                    if savings is not None:
                        amt_saved = float(savings)
                except Exception:
                    amt_saved = 0.0
            consolidated_data['autoship_savings'] = amt_saved
            
            # 5. Most Ordered Product
            most_reordered_results = customer_data.get('get_most_ordered', [])
            most_reordered_product = None
            if most_reordered_results and isinstance(most_reordered_results, list):
                try:
                    product = most_reordered_results[0].get('NAME')
                    if product:
                        most_reordered_product = product
                except Exception:
                    most_reordered_product = None
            consolidated_data['most_ordered'] = most_reordered_product
            
            # 6. Yearly Food Count
            yearly_food_results = customer_data.get('get_yearly_food_count', [])
            yearly_food_count = None
            if yearly_food_results and isinstance(yearly_food_results, list):
                try:
                    # Get the total lbs consumed by customer from the first row
                    total_lbs = yearly_food_results[0].get('TOTAL_LBS_CONSUMED_BY_CUSTOMER')
                    if total_lbs is not None:
                        yearly_food_count = float(total_lbs)
                except Exception:
                    yearly_food_count = None
            consolidated_data['yearly_food_count'] = yearly_food_count
            
            # 7. Zip Code
            address_data = self._get_cached_customer_address(customer_id)
            zip_code = address_data.get('zip_code', '') if address_data else ''
            consolidated_data['zip_code'] = zip_code
            
            # Save consolidated data to single JSON file
            consolidated_path = customer_dir / f"{customer_id}.json"
            with open(consolidated_path, 'w') as f:
                json.dump(consolidated_data, f, indent=2, cls=DecimalEncoder)
            
            print(f"    📊 Saved consolidated queries to {customer_id}.json")
            
        except Exception as e:
            print(f"    ❌ Error saving consolidated queries for customer {customer_id}: {e}")
    
    def run_unknowns_analyzer(self, customer_ids: List[str] = None):
        """Run the Unknowns Analyzer to identify unknown attributes in pet profile data."""
        print("\n🔍 Running Unknowns Analyzer...")
        try:
            analyzer = UnknownsAnalyzer(self.snowflake_connector)
            analyzer.pipeline = self  # Pass pipeline reference for cached data access
            
            # If no specific customers provided, analyze all processed customers
            if not customer_ids:
                # Get all customer directories that have enriched profiles
                customer_ids = []
                for customer_dir in self.output_dir.iterdir():
                    if customer_dir.is_dir() and customer_dir.name.isdigit():
                        profile_path = customer_dir / "enriched_pet_profile.json"
                        if profile_path.exists():
                            customer_ids.append(customer_dir.name)
            
            total_unknowns = 0
            customers_with_unknowns = 0
            
            for customer_id in customer_ids:
                analysis_results = analyzer.analyze_single_customer(customer_id, self.output_dir)
                if analysis_results and analysis_results['total_unknowns'] > 0:
                    # Save unknowns.json in the customer's directory
                    customer_dir = self.output_dir / customer_id
                    unknowns_path = customer_dir / "unknowns.json"
                    success = analyzer.save_unknowns_json(analysis_results, unknowns_path)
                    
                    if success:
                        total_unknowns += analysis_results['total_unknowns']
                        customers_with_unknowns += 1
                        print(f"  ✅ Customer {customer_id}: {analysis_results['total_unknowns']} unknowns")
                        
                        # Print details for each pet with unknowns
                        for pet_name, pet_unknowns in analysis_results['unknown_attributes'].items():
                            print(f"    🐾 {pet_name}:")
                            if pet_unknowns['unknown_fields']:
                                print(f"      Unknown fields: {', '.join(pet_unknowns['unknown_fields'])}")
                    else:
                        print(f"  ❌ Failed to save unknowns analysis for customer {customer_id}")
                else:
                    print(f"  ✅ Customer {customer_id}: No unknown attributes found")
            
            if customers_with_unknowns > 0:
                print(f"\n📊 Unknowns Analysis Summary:")
                print(f"   Customers with unknowns: {customers_with_unknowns}")
                print(f"   Total unknown attributes: {total_unknowns}")
            else:
                print(f"\n✅ No unknown attributes found in any customer profiles")
                
        except Exception as e:
            print(f"❌ Error running unknowns analyzer: {e}")

    def run_food_consumption_analyzer(self, customer_ids: List[str] = None):
        """Run the Food Consumption Analyzer to generate fun facts about food consumption."""
        print("\n🍽️ Running Food Consumption Analyzer...")
        
        try:
            # Import the food consumption analyzer
            from Agents.Review_and_Order_Intelligence_Agent.food_consumption_analyzer import generate_food_fun_fact_json
            
            # If no specific customers provided, analyze all processed customers
            if not customer_ids:
                # Get all customer directories that have enriched profiles
                customer_ids = []
                for customer_dir in self.output_dir.iterdir():
                    if customer_dir.is_dir() and customer_dir.name.isdigit():
                        profile_path = customer_dir / "enriched_pet_profile.json"
                        if profile_path.exists():
                            customer_ids.append(customer_dir.name)
            
            customers_analyzed = 0
            
            for customer_id in customer_ids:
                try:
                    print(f"  🍖 Analyzing food consumption for customer {customer_id}...")
                    
                    # Get food consumption data from cached data
                    customer_data = self._get_all_customer_data(customer_id)
                    food_data = customer_data.get('get_yearly_food_count', [])
                    
                    # Get customer zip code for location-based fun facts from cached data
                    address_data = self._get_cached_customer_address(customer_id)
                    zip_code = address_data.get('zip_code', '') if address_data else None
                    
                    if food_data and len(food_data) > 0:
                        # Generate food fun facts with location data
                        food_fun_fact_json = generate_food_fun_fact_json(food_data, zip_code)
                        
                        # Save to customer directory
                        customer_dir = self.output_dir / customer_id
                        food_fun_fact_path = customer_dir / "food_fun_fact.json"
                        
                        with open(food_fun_fact_path, 'w') as f:
                            f.write(food_fun_fact_json)
                        
                        # Parse the JSON to get the message for display
                        import json
                        analysis_data = json.loads(food_fun_fact_json)
                        total_lbs = analysis_data.get('total_food_lbs', 0)
                        
                        print(f"    ✅ Generated food fun facts: {total_lbs} lbs consumed")
                        customers_analyzed += 1
                    else:
                        print(f"    ⚠️ No food consumption data found for customer {customer_id}")
                        
                except Exception as e:
                    print(f"    ❌ Error analyzing food consumption for customer {customer_id}: {e}")
            
            if customers_analyzed > 0:
                print(f"\n🍽️ Food Consumption Analysis Summary:")
                print(f"   Customers analyzed: {customers_analyzed}")
                print(f"   Food fun facts generated and saved to food_fun_fact.json files")
            else:
                print(f"\n⚠️ No food consumption data found for any customers")
                
        except Exception as e:
            print(f"❌ Error running food consumption analyzer: {e}")

    def run_pipeline(self, customer_ids: List[str] = None):
        """Run the complete pipeline for specified customers or all customers."""
        print("🚀 Starting Chewy Playback Pipeline (Unified)")
        print("=" * 50)
        try:
            # Clear cache to ensure fresh data
            self.clear_cache()
            # Step 1: Preprocess data
            self.preprocess_data()
            # Step 2: Run Intelligence Agent (Review-based or Order-based)
            enriched_profiles = self.run_intelligence_agent(customer_ids)

            # Prepare per-customer outputs
            narrative_results = {}
            image_results = {}
            breed_predictions = {}
            eligible_for_narrative = []
            
            for customer_id, profile in enriched_profiles.items():
                gets_playback = profile.get('gets_playback', False)
                gets_personalized = profile.get('gets_personalized', False)
                
                print(f"\n🎯 Processing customer {customer_id}: gets_playback={gets_playback}, gets_personalized={gets_personalized}")
                
                if not gets_playback:
                    print(f"  ⏭️ Skipping further processing for customer {customer_id} (no playback)")
                    # Initialize empty results for customers with no playback
                    narrative_results[customer_id] = {}
                    image_results[customer_id] = None
                    breed_predictions[customer_id] = {}
                    continue
                
                # Determine which queries to run
                if gets_personalized:
                    # Personalized playback: only run queries needed for full pipeline
                    query_keys = [
                        'get_cust_orders',
                        'get_pet_profiles',
                        'get_cust_reviews',
                        'get_cust_zipcode',
                        'get_yearly_food_count'
                    ]
                    print(f"  🎨 Running personalized playback queries for customer {customer_id}")
                else:
                    # Generic playback: only run queries needed for generic outputs
                    query_keys = [
                        'get_amt_donated',
                        'get_cudd_month',
                        'get_total_months',
                        'get_autoship_savings',
                        'get_most_ordered',
                        'get_yearly_food_count'
                    ]
                    print(f"  📊 Running generic playback queries for customer {customer_id}")
                
                # Run breed predictor only for customers with playback
                print(f"  🐕 Running breed predictor for customer {customer_id}")
                breed_pred = self.run_breed_predictor_agent({customer_id: profile})
                breed_predictions[customer_id] = breed_pred.get(customer_id, {})
                
                if gets_personalized:
                    # Run narrative and image generation for personalized playback
                    print(f"  ✍️ Running narrative generation for customer {customer_id}")
                    narrative = self.run_narrative_generation_agent({customer_id: profile})
                    narrative_results[customer_id] = narrative.get(customer_id, {})
                    
                    print(f"  🎨 Running image generation for customer {customer_id}")
                    image = self.run_image_generation_agent({customer_id: narrative_results[customer_id]})
                    image_results[customer_id] = image.get(customer_id, None)
                    eligible_for_narrative.append(customer_id)
                else:
                    # Generic playback: no narrative/image/badge, just run required queries
                    print(f"  📊 Running generic playback queries for customer {customer_id}")
                    narrative_results[customer_id] = {}
                    image_results[customer_id] = None
                    # Run only the required queries for generic playback
                    customer_data = self._get_cached_customer_data(customer_id, query_keys=query_keys)
                    # ... (rest of the code for generic playback outputs remains unchanged)
            # Step 6: Save all outputs
            self.save_outputs(enriched_profiles, narrative_results, image_results, breed_predictions)
            # Ensure output folder and default profile for customers with no data
            if customer_ids:
                for customer_id in customer_ids:
                    if customer_id not in enriched_profiles:
                        customer_dir = self.output_dir / str(customer_id)
                        customer_dir.mkdir(exist_ok=True)
                        default_profile = {
                            "pets": {},
                            "cust_confidence_score": 0.0,
                            "gets_playback": False,
                            "gets_personalized": False
                        }
                        profile_path = customer_dir / "enriched_pet_profile.json"
                        with open(profile_path, 'w') as f:
                            json.dump(default_profile, f, indent=2)
            # Run unknowns analyzer and food consumption analyzer only for customers with playback
            playback_customer_ids = [cid for cid, profile in enriched_profiles.items() if profile.get('gets_playback', False)]
            
            if playback_customer_ids:
                print(f"\n🔍 Running analyzers for {len(playback_customer_ids)} customers with playback...")
                # Run unknowns analyzer after saving outputs
                self.run_unknowns_analyzer(playback_customer_ids)
                # Run food consumption analyzer after unknowns analyzer
                self.run_food_consumption_analyzer(playback_customer_ids)
            else:
                print(f"\n⏭️ Skipping analyzers - no customers eligible for playback")
            # Show cache statistics
            cache_stats = self.get_cache_stats()
            print(f"\n📊 Cache Statistics:")
            print(f"   Customers cached: {cache_stats['cached_customers']}")
            print(f"   Queries saved: {cache_stats['total_queries_saved']}")
            print("\n🎉 Pipeline completed successfully!")
            print(f"📁 Check the 'Output' directory for results")
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            raise


def main():
    """Main function to run the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chewy Playback Pipeline (Unified)")
    parser.add_argument("--customers", nargs="+", help="Specific customer IDs to process")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use environment variable)")
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipeline(openai_api_key=args.api_key)
        
        # Run pipeline
        pipeline.run_pipeline(customer_ids=args.customers)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 