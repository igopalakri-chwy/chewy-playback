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

from review_order_intelligence_agent import ReviewOrderIntelligenceAgent
from pet_letter_llm_system import PetLetterLLMSystem
from add_confidence_score import ConfidenceScoreCalculator
from breed_predictor_agent import BreedPredictorAgent
from unknowns_analyzer import UnknownsAnalyzer
from snowflake_data_connector import SnowflakeDataConnector
import openai
from dotenv import load_dotenv


class OrderIntelligenceAgent:
    """
    Simplified AI agent that derives pet insights from order history only
    using LLM analysis to generate basic pet profiles.
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize the Order Intelligence Agent."""
        self.openai_api_key = openai_api_key
        self.order_data = None
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
    
    def load_data(self, order_history_path: str) -> bool:
        """Load order history data from CSV file."""
        try:
            print("Loading order history data...")
            self.order_data = pd.read_csv(order_history_path)
            print(f"Loaded {len(self.order_data)} order records")
            self._validate_data()
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def _validate_data(self) -> None:
        """Validate that required columns exist in the data."""
        # Check for main order history format (Agents directory)
        if 'CustomerID' in self.order_data.columns:
            required_order_cols = ['CustomerID', 'ProductID', 'ProductName']
            missing_order_cols = [col for col in required_order_cols if col not in self.order_data.columns]
            if missing_order_cols:
                raise ValueError(f"Missing required columns in order history: {missing_order_cols}")
        # Check for Data directory processed format
        elif 'customer_id' in self.order_data.columns:
            required_order_cols = ['customer_id', 'product_id', 'item_name']
            missing_order_cols = [col for col in required_order_cols if col not in self.order_data.columns]
            if missing_order_cols:
                raise ValueError(f"Missing required columns in Data processed order history: {missing_order_cols}")
        # Check for zero_reviews format
        elif 'CUSTOMER_ID' in self.order_data.columns:
            required_order_cols = ['CUSTOMER_ID', 'PRODUCT_ID', 'ITEM_NAME']
            missing_order_cols = [col for col in required_order_cols if col not in self.order_data.columns]
            if missing_order_cols:
                raise ValueError(f"Missing required columns in zero_reviews: {missing_order_cols}")
        else:
            raise ValueError("Order data must have either CustomerID/ProductID/ProductName, customer_id/product_id/item_name, or CUSTOMER_ID/PRODUCT_ID/ITEM_NAME columns")
    
    def _get_customer_orders(self, customer_id: str):
        """Get all orders for a specific customer."""
        if self.order_data is None:
            return None
        
        # Handle all three column formats
        if 'CustomerID' in self.order_data.columns:
            return self.order_data[self.order_data['CustomerID'].astype(str) == str(customer_id)]
        elif 'customer_id' in self.order_data.columns:
            return self.order_data[self.order_data['customer_id'].astype(str) == str(customer_id)]
        elif 'CUSTOMER_ID' in self.order_data.columns:
            return self.order_data[self.order_data['CUSTOMER_ID'].astype(str) == str(customer_id)]
        else:
            return None
    
    def _analyze_customer_orders_with_llm(self, customer_orders, customer_id: str) -> Dict[str, Any]:
        """Analyze customer orders to generate pet insights using LLM."""
        if customer_orders is None or customer_orders.empty:
            return self._get_default_insights()
        
        # Prepare context from order data
        context = self._prepare_order_context(customer_orders)
        
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
            return self._parse_llm_response(result)
            
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return self._get_default_insights()
    
    def _prepare_order_context(self, customer_orders) -> str:
        """Prepare context data from order history for LLM analysis."""
        context_parts = []
        
        # Add order summary
        context_parts.append("Customer Order History:")
        context_parts.append(f"Total Orders: {len(customer_orders)}")
        
        # Handle different column formats
        if 'ProductName' in customer_orders.columns:
            # Main order history format (Agents directory)
            # Product categories and brands
            if 'ProductCategory' in customer_orders.columns:
                categories = customer_orders['ProductCategory'].value_counts().head(10)
                context_parts.append(f"Top Product Categories: {dict(categories)}")
            
            if 'Brand' in customer_orders.columns:
                brands = customer_orders['Brand'].value_counts().head(10)
                context_parts.append(f"Top Brands: {dict(brands)}")
            
            # Most ordered products
            products = customer_orders['ProductName'].value_counts().head(10)
            context_parts.append(f"Most Ordered Products: {dict(products)}")
            
            # Order dates (if available)
            if 'OrderDate' in customer_orders.columns:
                context_parts.append(f"Order Date Range: {customer_orders['OrderDate'].min()} to {customer_orders['OrderDate'].max()}")
        
        elif 'item_name' in customer_orders.columns:
            # Data directory processed format
            # Most ordered products
            products = customer_orders['item_name'].value_counts().head(10)
            context_parts.append(f"Most Ordered Products: {dict(products)}")
            
            # Order dates
            if 'order_date' in customer_orders.columns:
                context_parts.append(f"Order Date Range: {customer_orders['order_date'].min()} to {customer_orders['order_date'].max()}")
            
            # Pet names (if available)
            pet_names = set()
            if 'pet_name_1' in customer_orders.columns:
                pet_names.update(customer_orders['pet_name_1'].dropna().unique())
            if 'pet_name_2' in customer_orders.columns:
                pet_names.update(customer_orders['pet_name_2'].dropna().unique())
            if pet_names:
                context_parts.append(f"Pet Names: {', '.join(pet_names)}")
        
        elif 'ITEM_NAME' in customer_orders.columns:
            # Zero reviews format
            # Most ordered products
            products = customer_orders['ITEM_NAME'].value_counts().head(10)
            context_parts.append(f"Most Ordered Products: {dict(products)}")
            
            # Order dates
            if 'ORDER_DATE' in customer_orders.columns:
                context_parts.append(f"Order Date Range: {customer_orders['ORDER_DATE'].min()} to {customer_orders['ORDER_DATE'].max()}")
            
            # Pet names (if available)
            pet_names = set()
            if 'PET_NAME1' in customer_orders.columns:
                pet_names.update(customer_orders['PET_NAME1'].dropna().unique())
            if 'PET_NAME2' in customer_orders.columns:
                pet_names.update(customer_orders['PET_NAME2'].dropna().unique())
            if pet_names:
                context_parts.append(f"Pet Names: {', '.join(pet_names)}")
        
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

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured insights."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                print("Could not parse JSON from LLM response")
                return self._get_default_insights()
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return self._get_default_insights()
    
    def _get_default_insights(self) -> Dict[str, Any]:
        """Return default insights when analysis fails."""
        return {
            "PetType": "Pet",
            "PetTypeScore": 0.5,
            "Breed": "Mixed",
            "BreedScore": 0.3,
            "LifeStage": "adult",
            "LifeStageScore": 0.5,
            "Gender": "unknown",
            "GenderScore": 0.0,
            "SizeCategory": "medium",
            "SizeScore": 0.5,
            "Weight": "unknown",
            "WeightScore": 0.0,
            "PersonalityTraits": ["friendly"],
            "PersonalityScores": {"friendly": 0.7},
            "FavoriteProductCategories": ["food"],
            "CategoryScores": {"food": 0.8},
            "BrandPreferences": ["Chewy"],
            "BrandScores": {"Chewy": 0.8},
            "DietaryPreferences": ["standard"],
            "DietaryScores": {"standard": 0.7},
            "BehavioralCues": ["eats well"],
            "BehavioralScores": {"eats well": 0.8},
            "HealthMentions": ["healthy"],
            "HealthScores": {"healthy": 0.7},
            "MostOrderedProducts": ["Pet Food"]
        }
    
    def _extract_pet_info(self, customer_orders) -> List[Dict[str, Any]]:
        """Extract pet information including names, types, breeds, etc. from customer order data."""
        pets_info = []
        
        # Check for the new detailed pet information format
        if 'PET1_NAME' in customer_orders.columns and 'PET1_SPECIES' in customer_orders.columns:
            # New format with detailed pet information
            for i in range(1, 3):  # Check for PET1 and PET2
                pet_name_col = f'PET{i}_NAME'
                pet_species_col = f'PET{i}_SPECIES'
                pet_breed_col = f'PET{i}_BREED'
                pet_size_col = f'PET{i}_SIZE'
                pet_gender_col = f'PET{i}_GENDER'
                pet_life_stage_col = f'PET{i}_LIFE_STAGE'
                
                if pet_name_col in customer_orders.columns:
                    # Get the first non-null value for this pet
                    pet_name = customer_orders[pet_name_col].dropna().iloc[0] if not customer_orders[pet_name_col].dropna().empty else None
                    
                    if pet_name and str(pet_name).strip() and str(pet_name).strip().lower() not in ['nan', 'none', '']:
                        pet_info = {
                            'name': str(pet_name).strip(),
                            'type': customer_orders[pet_species_col].dropna().iloc[0] if pet_species_col in customer_orders.columns and not customer_orders[pet_species_col].dropna().empty else 'unknown',
                            'breed': customer_orders[pet_breed_col].dropna().iloc[0] if pet_breed_col in customer_orders.columns and not customer_orders[pet_breed_col].dropna().empty else 'unknown',
                            'size': customer_orders[pet_size_col].dropna().iloc[0] if pet_size_col in customer_orders.columns and not customer_orders[pet_size_col].dropna().empty else 'unknown',
                            'gender': customer_orders[pet_gender_col].dropna().iloc[0] if pet_gender_col in customer_orders.columns and not customer_orders[pet_gender_col].dropna().empty else 'unknown',
                            'life_stage': customer_orders[pet_life_stage_col].dropna().iloc[0] if pet_life_stage_col in customer_orders.columns and not customer_orders[pet_life_stage_col].dropna().empty else 'unknown'
                        }
                        pets_info.append(pet_info)
        
        # Fallback to old format if new format not found
        else:
            # Check different possible column names for pet names
            pet_name_columns = ['pet_name_1', 'pet_name_2', 'PetName1', 'PetName2', 'PetName', 'Pet1', 'Pet2']
            
            for col in pet_name_columns:
                if col in customer_orders.columns:
                    # Get unique non-null pet names
                    names = customer_orders[col].dropna().unique()
                    for name in names:
                        if pd.notna(name) and str(name).strip() and str(name).strip().lower() not in ['nan', 'none', '']:
                            pet_info = {
                                'name': str(name).strip(),
                                'type': 'unknown',
                                'breed': 'unknown',
                                'size': 'unknown',
                                'gender': 'unknown',
                                'life_stage': 'unknown'
                            }
                            pets_info.append(pet_info)
            
            # If no pet name columns found, try to extract from product descriptions
            if not pets_info:
                # Look for patterns like "for [PetName]" or "[PetName]'s" in product names
                product_col = None
                for col in ['ProductName', 'Product', 'ItemName']:
                    if col in customer_orders.columns:
                        product_col = col
                        break
                
                if product_col:
                    for product_name in customer_orders[product_col].dropna():
                        if pd.notna(product_name):
                            # Look for patterns that might indicate pet names
                            # This is a simple heuristic - could be enhanced
                            words = str(product_name).split()
                            for word in words:
                                # Skip common product words
                                if word.lower() in ['dog', 'cat', 'pet', 'toy', 'food', 'treat', 'chew', 'ball']:
                                    continue
                                # If word looks like a name (capitalized, not too long)
                                if (word[0].isupper() and len(word) > 1 and len(word) < 15 and 
                                    word.isalpha() and word.lower() not in ['chewy', 'wellness', 'dr', 'core']):
                                    pet_info = {
                                        'name': word,
                                        'type': 'unknown',
                                        'breed': 'unknown',
                                        'size': 'unknown',
                                        'gender': 'unknown',
                                        'life_stage': 'unknown'
                                    }
                                    pets_info.append(pet_info)
        
        return pets_info
    
    def _map_size_category(self, size_code: str) -> str:
        """Map size codes to readable size categories."""
        size_mapping = {
            'XS': 'extra small',
            'S': 'small', 
            'M': 'medium',
            'L': 'large',
            'XL': 'extra large',
            'UNK': 'unknown'
        }
        return size_mapping.get(size_code.upper(), 'medium')
    
    def _extract_pet_names(self, customer_orders) -> List[str]:
        """Extract unique pet names from customer order data."""
        pets_info = self._extract_pet_info(customer_orders)
        return [pet['name'] for pet in pets_info]
    
    def process_customer_data(self, customer_ids: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """Process customer data to generate pet insights."""
        results = {}
        
        # Get list of customers to process
        if customer_ids:
            customers_to_process = customer_ids
        else:
            # Get unique customer IDs from order data
            customers_to_process = self.order_data['CustomerID'].astype(str).unique().tolist()
        
        print(f"Processing {len(customers_to_process)} customers...")
        
        for customer_id in customers_to_process:
            try:
                print(f"  🐾 Analyzing customer {customer_id}...")
                
                # Get customer orders
                customer_orders = self._get_customer_orders(customer_id)
                
                if customer_orders is None or customer_orders.empty:
                    print(f"    ⚠️ No orders found for customer {customer_id}")
                    continue
                
                # Analyze orders to generate insights
                insights = self._analyze_customer_orders_with_llm(customer_orders, customer_id)
                
                # Extract pet information from order data
                pets_info = self._extract_pet_info(customer_orders)
                
                # Create pet profiles for each pet
                customer_pets = {}
                
                if pets_info:
                    # Create individual profiles for each pet using actual data
                    for pet_info in pets_info:
                        pet_name = pet_info['name']
                        
                        # Use actual data from CSV when available, fallback to LLM insights
                        pet_type = pet_info['type'].lower() if pet_info['type'] != 'unknown' else insights.get("PetType", "Pet")
                        pet_type_score = 0.9 if pet_info['type'] != 'unknown' else insights.get("PetTypeScore", 0.5)
                        
                        breed = pet_info['breed'] if pet_info['breed'] != 'unknown' else insights.get("Breed", "Mixed")
                        breed_score = 0.9 if pet_info['breed'] != 'unknown' else insights.get("BreedScore", 0.3)
                        
                        life_stage = pet_info['life_stage'].lower() if pet_info['life_stage'] != 'unknown' else insights.get("LifeStage", "adult")
                        life_stage_score = 0.9 if pet_info['life_stage'] != 'unknown' else insights.get("LifeStageScore", 0.5)
                        
                        gender = pet_info['gender'].lower() if pet_info['gender'] != 'unknown' else insights.get("Gender", "unknown")
                        gender_score = 0.9 if pet_info['gender'] != 'unknown' else insights.get("GenderScore", 0.0)
                        
                        # Map size categories
                        size_category = self._map_size_category(pet_info['size']) if pet_info['size'] != 'unknown' else insights.get("SizeCategory", "medium")
                        size_score = 0.9 if pet_info['size'] != 'unknown' else insights.get("SizeScore", 0.5)
                        
                        pet_profile = {
                            "PetName": pet_name,
                            "PetType": pet_type,
                            "PetTypeScore": pet_type_score,
                            "Breed": breed,
                            "BreedScore": breed_score,
                            "LifeStage": life_stage,
                            "LifeStageScore": life_stage_score,
                            "Gender": gender,
                            "GenderScore": gender_score,
                            "SizeCategory": size_category,
                            "SizeScore": size_score,
                            "Weight": insights.get("Weight", "unknown"),
                            "WeightScore": insights.get("WeightScore", 0.0),
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
                            "ConfidenceScore": 0.5  # Default confidence for order-only analysis
                        }
                        customer_pets[pet_name] = pet_profile
                else:
                    # Fallback to generic pet profile if no names found
                    pet_profile = {
                        "PetName": "Pet",
                        "PetType": insights.get("PetType", "Pet"),
                        "PetTypeScore": insights.get("PetTypeScore", 0.5),
                        "Breed": insights.get("Breed", "Mixed"),
                        "BreedScore": insights.get("BreedScore", 0.3),
                        "LifeStage": insights.get("LifeStage", "adult"),
                        "LifeStageScore": insights.get("LifeStageScore", 0.5),
                        "Gender": insights.get("Gender", "unknown"),
                        "GenderScore": insights.get("GenderScore", 0.0),
                        "SizeCategory": insights.get("SizeCategory", "medium"),
                        "SizeScore": insights.get("SizeScore", 0.5),
                        "Weight": insights.get("Weight", "unknown"),
                        "WeightScore": insights.get("WeightScore", 0.0),
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
                        "ConfidenceScore": 0.5  # Default confidence for order-only analysis
                    }
                    customer_pets["Pet"] = pet_profile
                
                results[customer_id] = customer_pets
                print(f"    ✅ Completed customer {customer_id}")
                
            except Exception as e:
                print(f"    ❌ Error processing customer {customer_id}: {e}")
                continue
        
        return results


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
        self.order_agent = OrderIntelligenceAgent(self.openai_api_key)
        self.narrative_agent = PetLetterLLMSystem(self.openai_api_key)
        self.breed_predictor_agent = BreedPredictorAgent()
        
        # Set up output directory
        self.output_dir = Path(__file__).parent / "Output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Data caching to avoid running the same Snowflake queries multiple times
        self._customer_data_cache = {}
        
        print("✅ Pipeline initialized with all agents and Snowflake connector")
    
    def _get_cached_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer data from cache or fetch from Snowflake if not cached.
        This prevents running the same queries multiple times for the same customer.
        """
        if customer_id not in self._customer_data_cache:
            print(f"    🔍 Fetching data from Snowflake for customer {customer_id}...")
            customer_data = self.snowflake_connector.get_customer_data(customer_id)
            self._customer_data_cache[customer_id] = customer_data
            print(f"    ✅ Cached data for customer {customer_id}")
        else:
            print(f"    📋 Using cached data for customer {customer_id}")
        
        return self._customer_data_cache[customer_id]
    
    def _get_cached_customer_orders_dataframe(self, customer_id: str) -> pd.DataFrame:
        """Get customer orders dataframe from cached data."""
        customer_data = self._get_cached_customer_data(customer_id)
        formatted_data = self.snowflake_connector.format_data_for_pipeline(customer_id, customer_data)
        if formatted_data['order_data'] and len(formatted_data['order_data']) > 0:
            return pd.DataFrame(formatted_data['order_data'])
        else:
            return pd.DataFrame()
    
    def _get_cached_customer_reviews_dataframe(self, customer_id: str) -> pd.DataFrame:
        """Get customer reviews dataframe from cached data."""
        customer_data = self._get_cached_customer_data(customer_id)
        formatted_data = self.snowflake_connector.format_data_for_pipeline(customer_id, customer_data)
        if formatted_data['review_data'] and len(formatted_data['review_data']) > 0:
            return pd.DataFrame(formatted_data['review_data'])
        else:
            return pd.DataFrame()
    
    def _get_cached_customer_pets_dataframe(self, customer_id: str) -> pd.DataFrame:
        """Get customer pets dataframe from cached data."""
        customer_data = self._get_cached_customer_data(customer_id)
        formatted_data = self.snowflake_connector.format_data_for_pipeline(customer_id, customer_data)
        if formatted_data['pet_data'] and len(formatted_data['pet_data']) > 0:
            return pd.DataFrame(formatted_data['pet_data'])
        else:
            return pd.DataFrame()
    
    def _get_cached_customer_address(self, customer_id: str) -> Dict[str, str]:
        """Get customer address from cached data."""
        customer_data = self._get_cached_customer_data(customer_id)
        address_data = customer_data.get('query_4', [])
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
        return {
            'cached_customers': len(self._customer_data_cache),
            'total_queries_saved': len(self._customer_data_cache) * 4  # 4 queries per customer
        }
    
    def preprocess_data(self):
        """Data preprocessing is no longer needed - data comes directly from Snowflake."""
        print("✅ Data preprocessing skipped - using Snowflake data connector")
    
    def _check_customer_has_reviews(self, customer_id: str) -> bool:
        """Check if a customer has any reviews using cached data."""
        try:
            reviews_df = self._get_cached_customer_reviews_dataframe(customer_id)
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
                        if customer_result:
                            results[customer_id] = customer_result
                    else:
                        print(f"  🐾 Customer {customer_id} has no reviews - using Order Intelligence Agent")
                        # Use the order-only agent
                        customer_result = self._run_order_agent_for_customer(customer_id)
                        if customer_result:
                            results[customer_id] = customer_result
                    
                except Exception as e:
                    print(f"  ❌ Error processing customer {customer_id}: {e}")
                    continue
        else:
            # Process all customers - this would be more complex, so for now we'll use the review agent
            print("Processing all customers with Review and Order Intelligence Agent...")
            results = self.review_agent.process_customer_data()
        
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
                gets_personalized = True
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
        pets_df = self._get_cached_customer_pets_dataframe(customer_id)
        if pets_df.empty:
            print(f"    ⚠️ No pets found for customer {customer_id}")
            return None
        
        customer_pets = pets_df['PetName'].unique().tolist()
        
        # Get customer orders from cached data
        orders_df = self._get_cached_customer_orders_dataframe(customer_id)
        
        # Get customer reviews from cached data
        reviews_df = self._get_cached_customer_reviews_dataframe(customer_id)
        
        # Process each pet
        customer_results = {}
        for pet_name in customer_pets:
            print(f"    🐾 Analyzing pet {pet_name} for customer {customer_id}...")
            
            # Get structured pet profile row for this pet
            pet_profile_row = pets_df[pets_df['PetName'] == pet_name].iloc[0] if not pets_df[pets_df['PetName'] == pet_name].empty else None
            
            # Filter reviews for this pet (if any)
            pet_reviews = reviews_df[reviews_df['ReviewText'].str.contains(pet_name, case=False, na=False)]
            
            # Prepare structured fields from Snowflake
            structured_pet_type = pet_profile_row['PetType'] if pet_profile_row is not None and pd.notna(pet_profile_row['PetType']) else 'UNK'
            structured_breed = pet_profile_row['PetBreed'] if pet_profile_row is not None and pd.notna(pet_profile_row['PetBreed']) else 'UNK'
            structured_gender = pet_profile_row['Gender'] if pet_profile_row is not None and pd.notna(pet_profile_row['Gender']) else 'UNK'
            structured_lifestage = pet_profile_row['PetAge'] if pet_profile_row is not None and pd.notna(pet_profile_row['PetAge']) else 'UNK'
            structured_weight = pet_profile_row['Weight'] if pet_profile_row is not None and pd.notna(pet_profile_row['Weight']) else 'UNK'
            
            # Prepare structured pet data dictionary
            structured_pet_data = {}
            if pet_profile_row is not None:
                structured_pet_data = {
                    'PetType': pet_profile_row.get('PetType', 'UNK'),
                    'PetBreed': pet_profile_row.get('PetBreed', 'UNK'),
                    'Gender': pet_profile_row.get('Gender', 'UNK'),
                    'PetAge': pet_profile_row.get('PetAge', 'UNK'),
                    'Weight': pet_profile_row.get('Weight', 'UNK'),
                    'SizeCategory': 'UNK'  # Not available in current Snowflake data
                }
            
            # Use LLM only for additional insights or if fields are missing
            insights = self.review_agent._analyze_pet_attributes_with_llm(
                pet_reviews if not pet_reviews.empty else pd.DataFrame(),
                orders_df if not orders_df.empty else pd.DataFrame(),
                pet_name,
                structured_pet_data
            )
            
            # Patch insights with structured data as primary source
            pet_insight = {
                "PetName": pet_name,
                "PetType": structured_pet_type if structured_pet_type != 'UNK' else insights.get("PetType", "UNK"),
                "PetTypeScore": 1.0 if structured_pet_type != 'UNK' else insights.get("PetTypeScore", 0.0),
                "Breed": structured_breed if structured_breed != 'UNK' else insights.get("Breed", "UNK"),
                "BreedScore": 1.0 if structured_breed != 'UNK' else insights.get("BreedScore", 0.0),
                "LifeStage": structured_lifestage if structured_lifestage != 'UNK' else insights.get("LifeStage", "UNK"),
                "LifeStageScore": 1.0 if structured_lifestage != 'UNK' else insights.get("LifeStageScore", 0.0),
                "Gender": structured_gender if structured_gender != 'UNK' else insights.get("Gender", "UNK"),
                "GenderScore": 1.0 if structured_gender != 'UNK' else insights.get("GenderScore", 0.0),
                "SizeCategory": insights.get("SizeCategory", "UNK"),
                "SizeScore": insights.get("SizeScore", 0.0),
                "Weight": structured_weight if structured_weight != 'UNK' else insights.get("Weight", "UNK"),
                "WeightScore": 1.0 if structured_weight != 'UNK' else insights.get("WeightScore", 0.0),
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
            customer_results[pet_name] = pet_insight
        return customer_results
    
    def _run_order_agent_for_customer(self, customer_id: str) -> Dict[str, Any]:
        """Run the Order Intelligence Agent for a specific customer using cached data."""
        print(f"    📋 Using cached data for customer {customer_id}...")
        
        # Get customer orders from cached data
        orders_df = self._get_cached_customer_orders_dataframe(customer_id)
        
        if orders_df.empty:
            print(f"    ⚠️ No orders found for customer {customer_id}")
            return None
        
        # Get customer pets from cached data
        pets_df = self._get_cached_customer_pets_dataframe(customer_id)
        
        # Use the order agent's LLM analysis method
        customer_orders = orders_df.to_dict('records')
        insights = self.order_agent._analyze_customer_orders_with_llm(orders_df, customer_id)
        
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
            # Fallback to extracting from order data if no pet profile data available
            try:
                pet_info = self.order_agent._extract_pet_info(orders_df)
                for pet_data in pet_info:
                    pet_name = pet_data.get('name', 'Unknown Pet')
                    customer_results[pet_name] = {
                        "PetName": pet_name,
                        "PetType": pet_data.get("type", "UNK"),
                        "PetTypeScore": insights.get("PetTypeScore", 0.0),
                        "Breed": pet_data.get("breed", "UNK"),
                        "BreedScore": insights.get("BreedScore", 0.0),
                        "LifeStage": pet_data.get("life_stage", "UNK"),
                        "LifeStageScore": insights.get("LifeStageScore", 0.0),
                        "Gender": pet_data.get("gender", "UNK"),
                        "GenderScore": insights.get("GenderScore", 0.0),
                        "SizeCategory": pet_data.get("size", "UNK"),
                        "SizeScore": insights.get("SizeScore", 0.0),
                        "Weight": "UNK",
                        "WeightScore": insights.get("WeightScore", 0.0),
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
            except Exception as e:
                print(f"    ⚠️ Error extracting pet info: {e}")
                # Create a default "Unknown Pet" entry
                customer_results["Unknown Pet"] = {
                    "PetName": "Unknown Pet",
                    "PetType": "UNK",
                    "PetTypeScore": insights.get("PetTypeScore", 0.0),
                    "Breed": "UNK",
                    "BreedScore": insights.get("BreedScore", 0.0),
                    "LifeStage": "UNK",
                    "LifeStageScore": insights.get("LifeStageScore", 0.0),
                    "Gender": "UNK",
                    "GenderScore": insights.get("GenderScore", 0.0),
                    "SizeCategory": "UNK",
                    "SizeScore": insights.get("SizeScore", 0.0),
                    "Weight": "UNK",
                    "WeightScore": insights.get("WeightScore", 0.0),
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
        
        return customer_results
    
    def run_narrative_generation_agent(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Narrative Generation Agent to create letters, image prompts, and personality badges."""
        print("\n✍️ Running Narrative Generation Agent...")
        
        narrative_results = {}
        
        for customer_id, customer_data in enriched_profiles.items():
            print(f"  📝 Generating narratives for customer {customer_id}...")
            
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
                # Use fallback
                customer_narratives = {
                    'customer_id': customer_id,
                    'pets': pets_data,
                    'collective_letter': f"Dear Chewy,\n\nWe love our treats and toys! Thanks for everything.\n\nFrom: The pets",
                    'collective_visual_prompt': f"A warm scene with pets and Chewy products",
                    'personality_badge': {
                        'badge': 'The Cuddler',
                        'compatible_with': ['The Nurturer', 'The Daydreamer', 'The Scholar'],
                        'icon_png': 'FrontEnd_Mobile/badge_cuddler.png',
                        'description': 'A loving household of pets who enjoy comfort and companionship.'
                    },
                    'cust_confidence_score': customer_confidence_score
                }
            
            narrative_results[customer_id] = customer_narratives
        
        print(f"✅ Generated narratives for {len(narrative_results)} customers")
        return narrative_results
    
    def run_breed_predictor_agent(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Breed Predictor Agent for pets with unknown/mixed breeds."""
        print("\n🐕 Running Breed Predictor Agent...")
        
        breed_predictions = {}
        
        for customer_id, customer_data in enriched_profiles.items():
            # Handle different data structures
            if isinstance(customer_data, dict) and 'pets' in customer_data:
                pets_data = customer_data['pets']
            else:
                pets_data = customer_data
            
            # Get customer orders from Snowflake for breed prediction
            orders_df = self._get_cached_customer_orders_dataframe(customer_id)
            customer_orders = []
            
            if not orders_df.empty:
                # Convert to list of dictionaries for breed predictor
                for _, row in orders_df.iterrows():
                    order = {
                        'item_name': row.get('ProductName', 'Unknown'),
                        'category': 'Unknown',
                        'order_date': '',
                        'quantity': row.get('Quantity', 1),
                        'brand': 'Chewy'
                    }
                    customer_orders.append(order)
            
            # Get raw pet data from Snowflake for breed prediction
            raw_pets_df = self._get_cached_customer_pets_dataframe(customer_id)
            raw_pets_data = {}
            if not raw_pets_df.empty:
                for _, row in raw_pets_df.iterrows():
                    pet_name = row.get('PetName', 'Unknown')
                    raw_pets_data[pet_name] = {
                        'PetType': row.get('PetType', 'UNK'),
                        'Breed': row.get('PetBreed', 'UNK'),
                        'Gender': row.get('Gender', 'UNK'),
                        'PetAge': row.get('PetAge', 'UNK'),
                        'Weight': row.get('Weight', 'UNK'),
                        'Medication': row.get('Medication', 'UNK')
                    }
            
            # Run breed prediction for this customer's pets with order data
            customer_prediction = self.breed_predictor_agent.process_customer_pets_with_orders(
                customer_id, raw_pets_data, customer_orders
            )
            
            if customer_prediction:
                breed_predictions[customer_id] = customer_prediction
        
        print(f"✅ Breed predictions completed for {len(breed_predictions)} customers")
        return breed_predictions
    
    def _get_customer_reviews(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get review data for a specific customer from cached data."""
        try:
            reviews_df = self._get_cached_customer_reviews_dataframe(customer_id)
            
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
            orders_df = self._get_cached_customer_orders_dataframe(customer_id)
            # Get customer address from cached data
            address_data = self._get_cached_customer_address(customer_id)

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
        """Run the Image Generation Agent to create collective images from visual prompts."""
        print("\n🎨 Running Image Generation Agent...")
        
        image_results = {}
        
        for customer_id, customer_data in narrative_results.items():
            print(f"  🖼️ Generating collective image for customer {customer_id}...")
            
            collective_visual_prompt = customer_data.get('collective_visual_prompt', '')
            zip_aesthetics = customer_data.get('zip_aesthetics', {})
            
            if collective_visual_prompt:
                try:
                    # Base sophisticated artistic portrait style - wholesome, joyous, and refined
                    base_artistic_style = "Sophisticated artistic pet portrait, wholesome and warm, joyous energy, refined illustration style, pets as the main focus, inviting atmosphere, elegant colors, cozy and cheerful mood, bright and well-lit with vibrant lighting, NOT cartoonish, artistic interpretation"
                    
                    # Use ZIP aesthetics for background and overall style influence
                    if zip_aesthetics and zip_aesthetics.get('visual_style'):
                        # ZIP aesthetics influence background and color palette, not the main pet focus
                        background_style = f"Background influenced by {zip_aesthetics.get('visual_style', '')} with {zip_aesthetics.get('color_texture', '')} tones. {zip_aesthetics.get('art_style', '')} artistic elements in the setting."
                        art_style_prompt = f"{base_artistic_style}. {background_style}. {zip_aesthetics.get('tones', '')} overall mood."
                    else:
                        art_style_prompt = base_artistic_style
                    
                    # Combine art style with visual prompt, ensuring pets are the main focus
                    prompt = f"{art_style_prompt}. {collective_visual_prompt}. The pets should be the clear main subjects, with artistic interpretation and vibrant colors."
                    
                    # Truncate prompt to fit OpenAI's 1000 character limit
                    if len(prompt) > 1000:
                        prompt = prompt[:997] + "..."
                    
                    # Add timestamp to ensure unique generation
                    import time
                    timestamp = int(time.time())
                    unique_prompt = f"{prompt} [Generated at {timestamp}]"
                    
                    # Generate collective image using OpenAI gpt-image-1
                    response = self.openai_client.images.generate(
                        model="gpt-image-1",
                        prompt=unique_prompt,
                        size="1024x1024",
                        n=1,
                    )
                    
                    # Handle both URL and base64 responses
                    image_data = response.data[0]
                    if hasattr(image_data, 'url') and image_data.url:
                        # URL response
                        image_url = image_data.url
                        image_results[customer_id] = image_url
                    elif hasattr(image_data, 'b64_json') and image_data.b64_json:
                        # Base64 response - save directly
                        import base64
                        image_bytes = base64.b64decode(image_data.b64_json)
                        image_results[customer_id] = image_bytes
                    else:
                        print(f"    ❌ No image data found in response for customer {customer_id}")
                        image_results[customer_id] = None
                    
                    print(f"    ✅ Generated collective image for all pets")
                    
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
            profile_path = customer_dir / "enriched_pet_profile.json"
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            # Save letters
            letters_path = customer_dir / "pet_letters.txt"
            with open(letters_path, 'w') as f:
                f.write(f"Collective Letter from All Pets for Customer {customer_id}\n")
                f.write("=" * 60 + "\n\n")
                f.write(narrative_results[customer_id]['collective_letter'])
                f.write("\n\n")
            
            # Save visual prompt
            visual_prompt_path = customer_dir / "visual_prompt.txt"
            with open(visual_prompt_path, 'w') as f:
                f.write(f"Visual Prompt for Customer {customer_id}\n")
                f.write("=" * 60 + "\n\n")
                f.write(narrative_results[customer_id]['collective_visual_prompt'])
                f.write("\n\n")
            
            # Save personality badge information
            badge_info = narrative_results[customer_id].get('personality_badge', {})
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
            
            # Save ZIP aesthetics information
            zip_aesthetics = narrative_results[customer_id].get('zip_aesthetics', {})
            if zip_aesthetics:
                zip_aesthetics_path = customer_dir / "zip_aesthetics.json"
                with open(zip_aesthetics_path, 'w') as f:
                    json.dump(zip_aesthetics, f, indent=2)
                print(f"    🗺️ Saved ZIP aesthetics: {zip_aesthetics.get('visual_style', 'Unknown')}, {zip_aesthetics.get('color_texture', 'Unknown')}, {zip_aesthetics.get('art_style', 'Unknown')}")
            
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
                    confidence = breed_predictions[customer_id]['confidence']
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
                        # URL response - download the image
                        response = requests.get(image_results[customer_id])
                        if response.status_code == 200:
                            with open(image_path, 'wb') as f:
                                f.write(response.content)
                            print(f"    💾 Saved collective image for all pets")
                        else:
                            print(f"    ❌ Failed to download image for customer {customer_id} (Status: {response.status_code})")
                    elif isinstance(image_results[customer_id], bytes):
                        # Base64 response - save directly
                        with open(image_path, 'wb') as f:
                            f.write(image_results[customer_id])
                        print(f"    💾 Saved collective image for all pets")
                    else:
                        print(f"    ❌ Unknown image data type for customer {customer_id}")
                except Exception as e:
                    print(f"    ❌ Error saving collective image: {e}")
            
            # Run donation query and save output
            if customer_id in enriched_profiles and enriched_profiles[customer_id].get('gets_playback', False) and not enriched_profiles[customer_id].get('gets_personalized', False):
                print(f"  💰 Running donation query for customer {customer_id}...")
                try:
                    donation_results = self.snowflake_connector.get_customer_donations(customer_id)
                    amt_donated = 0.0
                    if donation_results and isinstance(donation_results, list):
                        try:
                            amt = donation_results[0].get('AMT_DONATED')
                            if amt is not None:
                                amt_donated = float(amt)
                        except Exception:
                            amt_donated = 0.0
                    # Save to customer_donations.json
                    donation_path = customer_dir / "customer_donations.json"
                    with open(donation_path, 'w') as f:
                        json.dump({"amt_donated": amt_donated}, f, indent=2)
                    print(f"    ✅ Saved donation results for customer {customer_id}: {amt_donated} USD")
                except Exception as e:
                    print(f"    ❌ Error running donation query for customer {customer_id}: {e}")
            
            print(f"  ✅ Saved outputs for customer {customer_id}")
    
    def run_unknowns_analyzer(self, customer_ids: List[str] = None):
        """Run the Unknowns Analyzer to identify unknown attributes in pet profile data."""
        print("\n🔍 Running Unknowns Analyzer...")
        try:
            analyzer = UnknownsAnalyzer(self.snowflake_connector)
            
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
                    
                    # Get food consumption data from Snowflake
                    food_data = self.snowflake_connector.get_customer_food_consumption(customer_id)
                    
                    if food_data:
                        # Generate food fun facts
                        food_fun_fact_json = generate_food_fun_fact_json(food_data)
                        
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
                # Always run breed predictor for gets_playback
                breed_pred = self.run_breed_predictor_agent({customer_id: profile})
                breed_predictions[customer_id] = breed_pred.get(customer_id, {})
                if gets_playback and gets_personalized:
                    # Run narrative and image generation
                    narrative = self.run_narrative_generation_agent({customer_id: profile})
                    narrative_results[customer_id] = narrative.get(customer_id, {})
                    image = self.run_image_generation_agent({customer_id: narrative_results[customer_id]})
                    image_results[customer_id] = image.get(customer_id, None)
                    eligible_for_narrative.append(customer_id)
                else:
                    # No narrative/image/badge for this customer
                    narrative_results[customer_id] = {}
                    image_results[customer_id] = None
                    # Run donation query and save output
                    customer_data = self._get_cached_customer_data(customer_id)
                    donation_results = customer_data.get('query_6', [])
                    amt_donated = 0.0
                    if donation_results and isinstance(donation_results, list):
                        try:
                            amt = donation_results[0].get('AMT_DONATED')
                            if amt is not None:
                                amt_donated = float(amt)
                        except Exception:
                            amt_donated = 0.0
                    # Save to customer_donations.json
                    customer_dir = self.output_dir / str(customer_id)
                    customer_dir.mkdir(exist_ok=True)
                    donation_path = customer_dir / "customer_donations.json"
                    with open(donation_path, 'w') as f:
                        json.dump({"amt_donated": amt_donated}, f, indent=2)
            # Step 6: Save all outputs
            self.save_outputs(enriched_profiles, narrative_results, image_results, breed_predictions)
            # Run unknowns analyzer after saving outputs
            self.run_unknowns_analyzer(customer_ids)
            # Run food consumption analyzer after unknowns analyzer
            self.run_food_consumption_analyzer(customer_ids)
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