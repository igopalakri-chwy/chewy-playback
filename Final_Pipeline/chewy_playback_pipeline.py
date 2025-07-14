#!/usr/bin/env python3
"""
Chewy Playback Pipeline (Unified Version)
Orchestrates the flow of data through all agents, handling both customers with and without reviews:
1. Review and Order Intelligence Agent (when reviews available)
2. Order Intelligence Agent (when no reviews available)
3. Narrative Generation Agent  
4. Image Generation Agent
"""

import os
import sys
import json
import shutil
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
    """Main pipeline class that orchestrates all agents, handling both review and no-review scenarios."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the pipeline with OpenAI API key."""
        load_dotenv()
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Setup directories
        self.data_dir = Path("Data")
        self.output_dir = Path("Final_Pipeline/Output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents
        self.review_agent = ReviewOrderIntelligenceAgent(openai_api_key=self.openai_api_key)
        self.order_agent = OrderIntelligenceAgent(openai_api_key=self.openai_api_key)
        self.narrative_agent = PetLetterLLMSystem(openai_api_key=self.openai_api_key)
        self.breed_predictor_agent = BreedPredictorAgent(openai_api_key=self.openai_api_key)
        
    def preprocess_data(self):
        """Preprocess the raw CSV data for the agents."""
        print("🔄 Preprocessing data...")
        
        # Get the current directory (Final_Pipeline)
        current_dir = Path(__file__).parent
        
        # Check if preprocessed files exist
        preprocessed_order_path = current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv"
        preprocessed_review_path = current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv"
        
        if not (preprocessed_order_path.exists() and preprocessed_review_path.exists()):
            print("📊 Running data preprocessing...")
            import subprocess
            
            # Run the preprocessing script from the agent directory
            agent_dir = current_dir / "Agents/Review_and_Order_Intelligence_Agent"
            subprocess.run([
                sys.executable, 
                "preprocess_data.py"
            ], cwd=str(agent_dir), check=True)
        else:
            print("✅ Preprocessed data already exists")
    
    def _check_customer_has_reviews(self, customer_id: str) -> bool:
        """Check if a customer has any reviews."""
        try:
            current_dir = Path(__file__).parent
            reviews_path = current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv"
            if not reviews_path.exists():
                return False
            
            reviews_df = pd.read_csv(reviews_path)
            # Check for the correct column name
            if 'CustomerID' in reviews_df.columns:
                customer_reviews = reviews_df[reviews_df['CustomerID'].astype(str) == str(customer_id)]
            elif 'CUSTOMER_ID' in reviews_df.columns:
                customer_reviews = reviews_df[reviews_df['CUSTOMER_ID'].astype(str) == str(customer_id)]
            else:
                return False
            return len(customer_reviews) > 0
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
                results[customer_id] = {
                    'pets': pets_data,
                    'cust_confidence_score': customer_confidence_score
                }
                print(f"  🏠 {customer_id}: customer_confidence_score = {customer_confidence_score:.3f}")
        
        print("✅ Confidence scores added to all profiles")
        return results
    
    def _run_review_agent_for_customer(self, customer_id: str) -> Dict[str, Any]:
        """Run the Review and Order Intelligence Agent for a specific customer."""
        # Load preprocessed data
        current_dir = Path(__file__).parent
        success = self.review_agent.load_data(
            order_history_path=str(current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv"),
            qualifying_reviews_path=str(current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv")
        )
        
        if not success:
            raise RuntimeError("Failed to load data for Review and Order Intelligence Agent")
        
        # Get customer pets
        customer_pets = self.review_agent._get_customer_pets(customer_id)
        if not customer_pets:
            print(f"    ⚠️ No pets found for customer {customer_id}")
            return None
        
        # Get customer orders
        customer_orders = self.review_agent._get_customer_orders(customer_id)
        
        # Process each pet
        customer_results = {}
        for pet_name in customer_pets:
            print(f"    🐾 Analyzing pet {pet_name} for customer {customer_id}...")
            pet_reviews = self.review_agent._get_pet_reviews(customer_id, pet_name)
            insights = self.review_agent._analyze_pet_attributes_with_llm(pet_reviews, customer_orders, pet_name)
            
            # Format the insights
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
            customer_results[pet_name] = pet_insight
        
        return customer_results
    
    def _run_order_agent_for_customer(self, customer_id: str) -> Dict[str, Any]:
        """Run the Order Intelligence Agent for a specific customer."""
        # First try zero_reviews.csv as it has the most detailed pet information
        print(f"    🔍 Trying zero_reviews.csv first for detailed pet information...")
        current_dir = Path(__file__).parent
        success = self.order_agent.load_data(str(current_dir / "Data/zero_reviews.csv"))
        
        if success:
            # Process the customer from zero_reviews.csv
            customer_results = self.order_agent.process_customer_data([customer_id])
            
            if customer_id in customer_results:
                print(f"    ✅ Found customer {customer_id} in zero_reviews.csv with detailed pet info")
                return customer_results[customer_id]
        
        # If customer not found in zero_reviews.csv, try Data directory's processed_orderhistory.csv
        print(f"    🔍 Customer {customer_id} not found in zero_reviews.csv, trying Data/processed_orderhistory.csv...")
        success = self.order_agent.load_data(str(current_dir / "Data/processed_orderhistory.csv"))
        
        if not success:
            print(f"    ❌ Failed to load Data/processed_orderhistory.csv data")
            return None
        
        # Process the customer from Data directory's processed_orderhistory.csv
        customer_results = self.order_agent.process_customer_data([customer_id])
        
        if customer_id in customer_results:
            print(f"    ✅ Found customer {customer_id} in Data/processed_orderhistory.csv")
            return customer_results[customer_id]
        
        # If customer not found in either file, try main order history (Agents directory)
        print(f"    🔍 Customer {customer_id} not found in Data files, trying main order history...")
        success = self.order_agent.load_data(str(current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv"))
        
        if not success:
            print(f"    ❌ Failed to load main order history data")
            return None
        
        # Process the customer from main order history
        customer_results = self.order_agent.process_customer_data([customer_id])
        
        if customer_id in customer_results:
            print(f"    ✅ Found customer {customer_id} in main order history")
            return customer_results[customer_id]
        else:
            print(f"    ❌ Customer {customer_id} not found in any order history file")
            return None
    
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
                
                # For customers with reviews, we need to get review data
                # For customers without reviews, we'll use order data
                secondary_data = {}
                
                # Check if customer has reviews
                has_reviews = self._check_customer_has_reviews(customer_id)
                
                if has_reviews:
                    # Get review data for this customer
                    reviews = self._get_customer_reviews(customer_id)
                    secondary_data = {"reviews": reviews}
                else:
                    # Get order data for this customer
                    orders = self._get_customer_orders_for_narrative(customer_id)
                    secondary_data = {"order_history": orders}
                
                # Generate narrative using the new agent
                narrative_output = self.narrative_agent.generate_output(pet_data, secondary_data)
                
                customer_narratives = {
                    'customer_id': customer_id,
                    'pets': pets_data,
                    'collective_letter': narrative_output.get('letter', ''),
                    'collective_visual_prompt': narrative_output.get('visual_prompt', ''),
                    'personality_badge': narrative_output.get('personality_badge', {}),
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
            
            # Run breed prediction for this customer's pets
            customer_predictions = self.breed_predictor_agent.process_customer_pets(
                customer_id, pets_data
            )
            
            if customer_predictions:
                breed_predictions[customer_id] = customer_predictions
        
        print(f"✅ Breed predictions completed for {len(breed_predictions)} customers")
        return breed_predictions
    
    def _get_customer_reviews(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get review data for a specific customer."""
        try:
            import pandas as pd
            current_dir = Path(__file__).parent
            reviews_path = current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv"
            if not reviews_path.exists():
                return []
            
            reviews_df = pd.read_csv(reviews_path)
            
            # Check for the correct column name
            if 'CustomerID' in reviews_df.columns:
                customer_reviews = reviews_df[reviews_df['CustomerID'].astype(str) == str(customer_id)]
            elif 'CUSTOMER_ID' in reviews_df.columns:
                customer_reviews = reviews_df[reviews_df['CUSTOMER_ID'].astype(str) == str(customer_id)]
            else:
                return []
            
            # Convert to list of dictionaries
            reviews_list = []
            for _, row in customer_reviews.iterrows():
                review = {
                    'product_name': row.get('ProductName', row.get('product', 'Unknown')),
                    'review_text': row.get('ReviewText', row.get('review_text', '')),
                    'rating': row.get('Rating', row.get('rating', 0)),
                    'pet_name': row.get('PetName', row.get('pet_name', ''))
                }
                reviews_list.append(review)
            
            return reviews_list
        except Exception as e:
            print(f"Error getting reviews for customer {customer_id}: {e}")
            return []
    
    def _get_customer_orders_for_narrative(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get order data for a specific customer for narrative generation."""
        try:
            import pandas as pd
            
            # Try different order history files
            current_dir = Path(__file__).parent
            order_files = [
                str(current_dir / "Data/zero_reviews.csv"),
                str(current_dir / "Data/processed_orderhistory.csv"),
                str(current_dir / "Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv")
            ]
            
            for order_file in order_files:
                if os.path.exists(order_file):
                    orders_df = pd.read_csv(order_file)
                    
                    # Check for customer ID in different column formats
                    customer_col = None
                    for col in ['CustomerID', 'CUSTOMER_ID', 'customer_id']:
                        if col in orders_df.columns:
                            customer_col = col
                            break
                    
                    if customer_col:
                        customer_orders = orders_df[orders_df[customer_col].astype(str) == str(customer_id)]
                        
                        if not customer_orders.empty:
                            # Convert to list of dictionaries
                            orders_list = []
                            for _, row in customer_orders.iterrows():
                                order = {
                                    'product_name': row.get('ProductName', row.get('item_name', row.get('ITEM_NAME', 'Unknown'))),
                                    'item_type': 'unknown',  # We'll need to infer this
                                    'brand': 'Chewy',  # Default brand
                                    'quantity': 1,
                                    'pet_name': row.get('PetName1', row.get('pet_name_1', ''))
                                }
                                orders_list.append(order)
                            
                            return orders_list
            
            return []
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
            
            if collective_visual_prompt:
                try:
                    # Art style prompt to ensure consistency
                    default_art_style = "Soft, blended brushstrokes that mimic traditional oil or gouache painting. Warm, glowing lighting with gentle ambient highlights and diffuse shadows. Vivid yet harmonious color palette, featuring saturated pastels and rich warm tones. Subtle texture that gives a hand-painted, storybook feel. Sparkle accents and light flares to add magical charm. Smooth gradients and soft edges, avoiding harsh lines or stark contrast. A dreamy, nostalgic tone evocative of classic children's book illustrations. "
                    
                    # Combine art style with visual prompt
                    prompt = default_art_style + collective_visual_prompt
                    
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
            
            # Save enriched pet profile JSON (include customer confidence score)
            profile_data = {
                **pets_data,
                'cust_confidence_score': customer_confidence_score
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
            
            # Save breed predictions if available
            if breed_predictions and customer_id in breed_predictions:
                breed_path = customer_dir / "predicted_breed.json"
                with open(breed_path, 'w') as f:
                    json.dump(breed_predictions[customer_id], f, indent=2)
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
            
            print(f"  ✅ Saved outputs for customer {customer_id}")
    
    def run_unknowns_analyzer(self, customer_ids: List[str] = None):
        """Run the Unknowns Analyzer to identify unknown attributes in enriched profiles."""
        print("\n🔍 Running Unknowns Analyzer...")
        try:
            analyzer = UnknownsAnalyzer()
            
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
                            if pet_unknowns['unknown_scores']:
                                print(f"      Unknown scores: {', '.join(pet_unknowns['unknown_scores'])}")
                            if pet_unknowns['unknown_lists']:
                                print(f"      Empty lists: {', '.join(pet_unknowns['unknown_lists'])}")
                            if pet_unknowns['unknown_dicts']:
                                print(f"      Empty dicts: {', '.join(pet_unknowns['unknown_dicts'])}")
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

    def run_pipeline(self, customer_ids: List[str] = None):
        """Run the complete pipeline for specified customers or all customers."""
        print("🚀 Starting Chewy Playback Pipeline (Unified)")
        print("=" * 50)
        
        try:
            # Step 1: Preprocess data
            self.preprocess_data()
            
            # Step 2: Run Intelligence Agent (Review-based or Order-based)
            enriched_profiles = self.run_intelligence_agent(customer_ids)
            
            # Step 3: Run Narrative Generation Agent
            narrative_results = self.run_narrative_generation_agent(enriched_profiles)
            
            # Step 4: Run Breed Predictor Agent
            breed_predictions = self.run_breed_predictor_agent(enriched_profiles)
            
            # Step 5: Run Image Generation Agent
            image_results = self.run_image_generation_agent(narrative_results)
            
            # Step 6: Save all outputs
            self.save_outputs(enriched_profiles, narrative_results, image_results, breed_predictions)
            # Run unknowns analyzer after saving outputs
            self.run_unknowns_analyzer(customer_ids)
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