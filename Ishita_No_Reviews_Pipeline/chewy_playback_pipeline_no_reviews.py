#!/usr/bin/env python3
"""
Chewy Playback Pipeline (No Reviews Version)
Orchestrates the flow of data through agents using only order history:
1. Order Intelligence Agent (simplified)
2. Narrative Generation Agent  
3. Image Generation Agent
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add agent directories to path
sys.path.append('Agents/Narrative_Generation_Agent')
sys.path.append('Agents/Image_Generation_Agent')

import openai
import pandas as pd
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
        if self.order_data is None:
            raise ValueError("No data loaded")
            
        required_order_cols = ['customer_id', 'order_date', 'order_id', 'product_id', 'item_name']
        missing_order_cols = [col for col in required_order_cols if col not in self.order_data.columns]
        if missing_order_cols:
            raise ValueError(f"Missing required columns in order history: {missing_order_cols}")
        
        # Check for optional pet name columns
        pet_name_cols = ['pet_name_1', 'pet_name_2']
        available_pet_cols = [col for col in pet_name_cols if col in self.order_data.columns]
        print(f"Available pet name columns: {available_pet_cols}")
    
    def _get_customer_orders(self, customer_id: str):
        """Get all orders for a specific customer."""
        if self.order_data is None:
            return None
        return self.order_data[self.order_data['customer_id'].astype(str) == str(customer_id)]
    
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
        
        # Pet names if available
        pet_names = []
        if 'pet_name_1' in customer_orders.columns:
            pet_names.extend(customer_orders['pet_name_1'].dropna().unique())
        if 'pet_name_2' in customer_orders.columns:
            pet_names.extend(customer_orders['pet_name_2'].dropna().unique())
        
        if pet_names:
            unique_pet_names = list(set([name for name in pet_names if pd.notna(name) and str(name).strip() != '']))
            if unique_pet_names:
                context_parts.append(f"Pet Names: {', '.join(unique_pet_names)}")
        
        # Most ordered products
        products = customer_orders['item_name'].value_counts().head(10)
        context_parts.append(f"Most Ordered Products: {dict(products)}")
        
        # Order dates
        if 'order_date' in customer_orders.columns:
            context_parts.append(f"Order Date Range: {customer_orders['order_date'].min()} to {customer_orders['order_date'].max()}")
        
        # Product IDs for variety analysis
        unique_products = customer_orders['product_id'].nunique()
        context_parts.append(f"Unique Products Ordered: {unique_products}")
        
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
1. Product names that indicate pet type (dog food vs cat food)
2. Product types that suggest life stage (puppy food, senior care)
3. Product variety that suggests personality traits
4. Order frequency and patterns
5. Pet names if available in the data

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
            "GenderScore": 0.3,
            "SizeCategory": "medium",
            "SizeScore": 0.4,
            "Weight": "unknown",
            "WeightScore": 0.2,
            "Birthday": "unknown",
            "BirthdayScore": 0.0,
            "PersonalityTraits": ["friendly"],
            "PersonalityScores": {"friendly": 0.5},
            "FavoriteProductCategories": ["food"],
            "CategoryScores": {"food": 0.5},
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
    
    def process_customer_data(self, customer_ids: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Process customer data to generate pet insights."""
        results = {}
        
        if customer_ids is not None:
            customers_to_process = customer_ids
        else:
            # Process all unique customers
            if self.order_data is not None:
                customers_to_process = self.order_data['customer_id'].unique().tolist()
            else:
                print("No order data available")
                return results
        
        for customer_id in customers_to_process:
            try:
                print(f"  🐾 Analyzing orders for customer {customer_id}...")
                
                # Get customer orders
                customer_orders = self._get_customer_orders(customer_id)
                
                # Analyze orders to generate insights
                insights = self._analyze_customer_orders_with_llm(customer_orders, customer_id)
                
                # Create a generic pet profile (since we don't have specific pet names)
                pet_insight = {
                    "PetName": "Pet",  # Generic name since no review data
                    "PetType": insights.get("PetType", "Pet"),
                    "PetTypeScore": insights.get("PetTypeScore", 0.5),
                    "Breed": insights.get("Breed", "Mixed"),
                    "BreedScore": insights.get("BreedScore", 0.3),
                    "LifeStage": insights.get("LifeStage", "adult"),
                    "LifeStageScore": insights.get("LifeStageScore", 0.5),
                    "Gender": insights.get("Gender", "unknown"),
                    "GenderScore": insights.get("GenderScore", 0.3),
                    "SizeCategory": insights.get("SizeCategory", "medium"),
                    "SizeScore": insights.get("SizeScore", 0.4),
                    "Weight": insights.get("Weight", "unknown"),
                    "WeightScore": insights.get("WeightScore", 0.2),
                    "Birthday": insights.get("Birthday", "unknown"),
                    "BirthdayScore": insights.get("BirthdayScore", 0.0),
                    "PersonalityTraits": insights.get("PersonalityTraits", ["friendly"]),
                    "PersonalityScores": insights.get("PersonalityScores", {"friendly": 0.5}),
                    "FavoriteProductCategories": insights.get("FavoriteProductCategories", ["food"]),
                    "CategoryScores": insights.get("CategoryScores", {"food": 0.5}),
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
                
                results[customer_id] = {"Pet": pet_insight}  # Single generic pet per customer
                print(f"  ✅ Completed customer {customer_id}")
                
            except Exception as e:
                print(f"  ❌ Error processing customer {customer_id}: {e}")
                continue
        
        return results


class ChewyPlaybackPipelineNoReviews:
    """Main pipeline class that orchestrates agents without review data."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the pipeline with OpenAI API key."""
        load_dotenv()
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Setup directories
        self.data_dir = Path("../Data")
        self.output_dir = Path("Output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents
        self.order_agent = OrderIntelligenceAgent(openai_api_key=self.openai_api_key)
        
    def preprocess_data(self):
        """Preprocess the raw CSV data for the Order Intelligence Agent."""
        print("🔄 Preprocessing data...")
        
        # Check if preprocessed files exist
        preprocessed_order_path = self.data_dir / "processed_orderhistory.csv"
        
        if not os.path.exists(preprocessed_order_path):
            print("📊 Running data preprocessing...")
            # Simple preprocessing - just copy the original file
            import shutil
            original_path = self.data_dir / "no_review.csv"
            if os.path.exists(original_path):
                shutil.copy2(original_path, preprocessed_order_path)
                print("✅ Created preprocessed order data")
            else:
                raise FileNotFoundError(f"Order history file not found: {original_path}")
        else:
            print("✅ Preprocessed data already exists")
    
    def run_order_intelligence_agent(self, customer_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the Order Intelligence Agent to generate basic pet profiles."""
        print("\n🧠 Running Order Intelligence Agent...")
        
        # Load preprocessed data
        success = self.order_agent.load_data(str(self.data_dir / "processed_orderhistory.csv"))
        
        if not success:
            raise RuntimeError("Failed to load data for Order Intelligence Agent")
        
        # Process customers
        results = self.order_agent.process_customer_data(customer_ids)
        
        print(f"✅ Generated basic profiles for {len(results)} customers")
        return results
    
    def run_narrative_generation_agent(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Narrative Generation Agent to create letters and image prompts."""
        print("\n✍️ Running Narrative Generation Agent...")
        
        narrative_results = {}
        
        for customer_id, pets_data in enriched_profiles.items():
            print(f"  📝 Generating narratives for customer {customer_id}...")
            customer_narratives = {
                'customer_id': customer_id,
                'pets': {},
                'letters': {},
                'visual_prompts': {}
            }
            
            for pet_name, pet_data in pets_data.items():
                try:
                    # Generate letter from pet to human
                    letter = self._generate_letter_with_openai(pet_data)
                    
                    # Generate visual prompt for image generation
                    visual_prompt = self._generate_visual_prompt_for_pet(pet_data)
                    
                    customer_narratives['pets'][pet_name] = pet_data
                    customer_narratives['letters'][pet_name] = letter
                    customer_narratives['visual_prompts'][pet_name] = visual_prompt
                    
                    print(f"    ✅ Generated letter and visual prompt for {pet_name}")
                    
                except Exception as e:
                    print(f"    ❌ Error generating narrative for {pet_name}: {e}")
                    # Use fallback letter
                    letter = self._generate_fallback_letter(pet_data)
                    visual_prompt = self._generate_visual_prompt_for_pet(pet_data)
                    
                    customer_narratives['pets'][pet_name] = pet_data
                    customer_narratives['letters'][pet_name] = letter
                    customer_narratives['visual_prompts'][pet_name] = visual_prompt
            
            narrative_results[customer_id] = customer_narratives
        
        print(f"✅ Generated narratives for {len(narrative_results)} customers")
        return narrative_results
    
    def _generate_letter_with_openai(self, pet_data: Dict[str, Any]) -> str:
        """Generate a unique letter using OpenAI API."""
        
        name = pet_data.get("PetName", "Friend")
        pet_type = pet_data.get("PetType", "Pet")
        breed = pet_data.get("Breed", "beautiful")
        personality_traits = pet_data.get("PersonalityTraits", [])
        favorite_products = pet_data.get("MostOrderedProducts", [])
        behavioral_cues = pet_data.get("BehavioralCues", [])
        health_mentions = pet_data.get("HealthMentions", [])
        dietary_prefs = pet_data.get("DietaryPreferences", [])
        life_stage = pet_data.get("LifeStage", "adult")
        gender = pet_data.get("Gender", "")
        size_category = pet_data.get("SizeCategory", "medium")
        weight = pet_data.get("Weight", "")
        
        # Create a detailed prompt for OpenAI
        prompt = f"""Write a completely unique, heartfelt letter from a pet to their human owner. 

Pet Details:
- Name: {name}
- Type: {pet_type}
- Breed: {breed}
- Life Stage: {life_stage}
- Gender: {gender}
- Size: {size_category}
- Weight: {weight}
- Personality Traits: {', '.join(personality_traits)}
- Favorite Products: {', '.join(favorite_products)}
- Behavioral Cues: {', '.join(behavioral_cues)}
- Health Mentions: {', '.join(health_mentions)}
- Dietary Preferences: {', '.join(dietary_prefs)}

Requirements:
- Start with "Human" instead of "Dear Human" - make it casual and funny
- Write in the pet's voice as if they're writing to their human
- Make it completely unique and different from any template
- Include specific details about their personality, products, and behaviors
- Make it emotional, heartfelt, and personal
- Use the pet's actual name and characteristics
- Make it whimsical and delightful
- Include a signature with the pet's name
- Keep it between 200-400 words
- Make it feel like a real letter from the pet to their human

Write the letter:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative writer who specializes in writing heartfelt letters from pets to their human companions. Make each letter unique, personal, and emotionally touching."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            letter = response.choices[0].message.content.strip()
            return letter
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._generate_fallback_letter(pet_data)

    def _generate_fallback_letter(self, pet_data: Dict[str, Any]) -> str:
        """Generate a fallback letter if API fails."""
        
        name = pet_data.get("PetName", "Friend")
        pet_type = pet_data.get("PetType", "Pet")
        breed = pet_data.get("Breed", "beautiful")
        personality_traits = pet_data.get("PersonalityTraits", [])
        favorite_products = pet_data.get("MostOrderedProducts", [])
        behavioral_cues = pet_data.get("BehavioralCues", [])
        health_mentions = pet_data.get("HealthMentions", [])
        dietary_prefs = pet_data.get("DietaryPreferences", [])
        
        return f"""Human,

I just had to write you this letter to tell you how much you mean to me! I'm {name}, your {breed.lower()} {pet_type.lower()}, and I'm so grateful for everything you do for me.

Every day with you is a gift. Whether we're playing with my {favorite_products[0].lower() if favorite_products else 'favorite things'}, going on adventures, or just spending quiet time together, I'm reminded of how lucky I am to have you as my human.

I know I can be a bit {personality_traits[0].lower() if personality_traits else 'unique'} sometimes - like when I {behavioral_cues[0].lower() if behavioral_cues else 'do my special things'} - but you always understand and love me for who I am. Your patience and understanding mean the world to me.

Thank you for always looking out for my {health_mentions[0].lower() if health_mentions else 'health'} and making sure I have the best {dietary_prefs[0].lower() if dietary_prefs else 'care'}. Your attention to my needs shows me how much you love me.

You've given me the most wonderful life filled with love, joy, and endless adventures. I promise to love you unconditionally, be your faithful companion, and bring happiness to your life every single day.

With all my love and gratitude,
{name} ❤️

P.S. I can't wait for our next adventure together!"""

    def _generate_visual_prompt_for_pet(self, pet_data: Dict[str, Any]) -> str:
        """Generate a unique visual prompt for any pet based on their individual data."""
        
        name = pet_data.get("PetName", "Pet")
        pet_type = pet_data.get("PetType", "Pet")
        breed = pet_data.get("Breed", "beautiful")
        personality_traits = pet_data.get("PersonalityTraits", [])
        size_category = pet_data.get("SizeCategory", "medium")
        weight = pet_data.get("Weight", "")
        life_stage = pet_data.get("LifeStage", "adult")
        gender = pet_data.get("Gender", "")
        favorite_products = pet_data.get("MostOrderedProducts", [])
        
        # Create personality-based visual elements
        personality_desc = ""
        if "playful" in [trait.lower() for trait in personality_traits]:
            personality_desc += "with a cheerful, playful expression, "
        if "curious" in [trait.lower() for trait in personality_traits]:
            personality_desc += "head tilted inquisitively, "
        if "affectionate" in [trait.lower() for trait in personality_traits]:
            personality_desc += "wearing a gentle, loving expression, "
        if "loyal" in [trait.lower() for trait in personality_traits]:
            personality_desc += "standing with devoted attention, "
        if "energetic" in [trait.lower() for trait in personality_traits]:
            personality_desc += "captured mid-motion with boundless energy, "
        if "intelligent" in [trait.lower() for trait in personality_traits]:
            personality_desc += "with an intelligent, thoughtful gaze, "
        if "alert" in [trait.lower() for trait in personality_traits]:
            personality_desc += "with alert, focused attention, "
        if "vocal" in [trait.lower() for trait in personality_traits]:
            personality_desc += "with an expressive, communicative face, "
        if "social" in [trait.lower() for trait in personality_traits]:
            personality_desc += "with a friendly, approachable expression, "
        
        if not personality_desc:
            personality_desc = "with a charming, endearing expression, "
        
        # Create artistic, cute environment based on pet type
        if pet_type.lower() == "dog":
            environment = "in a whimsical, cozy home setting with soft cushions and warm lighting"
        elif pet_type.lower() == "cat":
            environment = "in a magical, sunlit room with comfortable perches and floating cat toys"
        else:
            environment = "in a charming, loving home environment with artistic details"
        
        # Add favorite items in a cute way
        favorite_items = ""
        if favorite_products:
            items = [product.lower() for product in favorite_products[:2]]
            favorite_items = f", surrounded by their beloved {', '.join(items)} in cute packaging"
        
        prompt = f"""A delightful, artistic character portrait of {name}, a {size_category} {breed.lower()} {pet_type.lower()} {personality_desc}weighing {weight}. This {life_stage} {gender.lower() if gender else ''} is shown {environment}{favorite_items}. The background features soft, dreamy colors with gentle patterns, floating hearts, and warm, inviting lighting. The image should radiate happiness and unconditional love, with bright, cheerful lighting that highlights their unique personality. The style should be cute, shareable digital art with a wholesome, family-friendly aesthetic perfect for social media. The image should be heartwarming and adorable, with a warm color palette that makes people want to share it. IMPORTANT: The Chewy logo must be prominently displayed at the bottom center of the image in clear, readable text with warm, friendly colors, perfect for Chewy's brand of caring for pets and their families."""
        
        return prompt
    
    def run_image_generation_agent(self, narrative_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Image Generation Agent to create images from visual prompts."""
        print("\n🎨 Running Image Generation Agent...")
        
        image_results = {}
        
        for customer_id, customer_data in narrative_results.items():
            print(f"  🖼️ Generating images for customer {customer_id}...")
            customer_images = {}
            
            for pet_name, visual_prompt in customer_data['visual_prompts'].items():
                try:
                    # Generate image using OpenAI DALL-E
                    response = self.openai_client.images.generate(
                        model="dall-e-3",
                        prompt=visual_prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1,
                    )
                    
                    # Get image URL
                    image_url = response.data[0].url
                    customer_images[pet_name] = image_url
                    
                    print(f"    ✅ Generated image for {pet_name}")
                    
                except Exception as e:
                    print(f"    ❌ Error generating image for {pet_name}: {e}")
                    customer_images[pet_name] = None
            
            image_results[customer_id] = customer_images
        
        print(f"✅ Generated images for {len(image_results)} customers")
        return image_results
    
    def save_outputs(self, enriched_profiles: Dict[str, Any], 
                    narrative_results: Dict[str, Any], 
                    image_results: Dict[str, Any]):
        """Save all outputs to the Output directory structure."""
        print("\n💾 Saving outputs...")
        
        for customer_id in enriched_profiles.keys():
            # Create customer directory
            customer_dir = self.output_dir / customer_id
            customer_dir.mkdir(exist_ok=True)
            
            # Save enriched pet profile JSON
            profile_path = customer_dir / "enriched_pet_profile.json"
            with open(profile_path, 'w') as f:
                json.dump(enriched_profiles[customer_id], f, indent=2)
            
            # Save letters
            letters_path = customer_dir / "pet_letters.txt"
            with open(letters_path, 'w') as f:
                f.write(f"Letters from pets for customer {customer_id}\n")
                f.write("=" * 50 + "\n\n")
                
                for pet_name, letter in narrative_results[customer_id]['letters'].items():
                    f.write(f"From {pet_name}:\n")
                    f.write("-" * 30 + "\n")
                    f.write(letter)
                    f.write("\n\n")
            
            # Save images (download and save)
            if customer_id in image_results:
                images_dir = customer_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                for pet_name, image_url in image_results[customer_id].items():
                    if image_url:
                        try:
                            import requests
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                image_path = images_dir / f"{pet_name}_portrait.png"
                                with open(image_path, 'wb') as f:
                                    f.write(response.content)
                                print(f"    💾 Saved image for {pet_name}")
                        except Exception as e:
                            print(f"    ❌ Error saving image for {pet_name}: {e}")
            
            print(f"  ✅ Saved outputs for customer {customer_id}")
    
    def run_pipeline(self, customer_ids: Optional[List[str]] = None):
        """Run the complete pipeline for specified customers or all customers."""
        print("🚀 Starting Chewy Playback Pipeline (No Reviews Version)")
        print("=" * 60)
        
        try:
            # Step 1: Preprocess data
            self.preprocess_data()
            
            # Step 2: Run Order Intelligence Agent
            enriched_profiles = self.run_order_intelligence_agent(customer_ids)
            
            # Step 3: Run Narrative Generation Agent
            narrative_results = self.run_narrative_generation_agent(enriched_profiles)
            
            # Step 4: Run Image Generation Agent
            image_results = self.run_image_generation_agent(narrative_results)
            
            # Step 5: Save all outputs
            self.save_outputs(enriched_profiles, narrative_results, image_results)
            
            print("\n🎉 Pipeline completed successfully!")
            print(f"📁 Check the 'Output' directory for results")
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            raise


def main():
    """Main function to run the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chewy Playback Pipeline (No Reviews Version)")
    parser.add_argument("--customers", nargs="+", help="Specific customer IDs to process")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use environment variable)")
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipelineNoReviews(openai_api_key=args.api_key)
        
        # Run pipeline
        pipeline.run_pipeline(customer_ids=args.customers)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 