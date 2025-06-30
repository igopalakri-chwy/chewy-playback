#!/usr/bin/env python3
"""
Chewy Playback Pipeline with Boyue Narrative Generation Agent
A pipeline that processes customer data and generates personalized pet content.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import openai
from openai import OpenAI

# Add agent paths
sys.path.append('../Agents/Review_and_Order_Intelligence_Agent')
sys.path.append('../Agents/Narrative_Generation_Agent_Boyue')
sys.path.append('../Agents/Image_Generation_Agent')

from review_order_intelligence_agent import ReviewOrderIntelligenceAgent
from pet_letter_llm_system import PetLetterLLMSystem


class ChewyPlaybackPipelineBoyue:
    """Pipeline that uses Boyue's Narrative Generation Agent."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the pipeline with OpenAI API key."""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required. Provide via parameter or OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Set up paths
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "Data"
        self.output_dir = self.base_dir / "Output_Boyue"
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents
        self.review_agent = ReviewOrderIntelligenceAgent()
        self.narrative_agent = PetLetterLLMSystem(openai_api_key=self.openai_api_key)
        
        print(f"📁 Data directory: {self.data_dir}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def preprocess_data(self):
        """Preprocess the data files."""
        print("\n📊 Preprocessing data...")
        
        # Check if data files exist
        order_history_path = self.data_dir / "order_history.csv"
        qualifying_reviews_path = self.data_dir / "qualifying_reviews.csv"
        
        if not order_history_path.exists():
            raise FileNotFoundError(f"Order history file not found: {order_history_path}")
        if not qualifying_reviews_path.exists():
            raise FileNotFoundError(f"Qualifying reviews file not found: {qualifying_reviews_path}")
        
        print("✅ Data files found and validated")
    
    def run_review_intelligence_agent(self, customer_ids: List[str] = None) -> Dict[str, Any]:
        """Run the Review and Order Intelligence Agent to enrich pet profiles."""
        print("\n🧠 Running Review and Order Intelligence Agent...")
        
        # Load preprocessed data
        success = self.review_agent.load_data(
            order_history_path="../Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv",
            qualifying_reviews_path="../Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv"
        )
        
        if not success:
            raise RuntimeError("Failed to load data for Review and Order Intelligence Agent")
        
        # Process only specified customers or all customers
        if customer_ids:
            print(f"Processing {len(customer_ids)} specified customers...")
            results = {}
            for customer_id in customer_ids:
                try:
                    # Get customer pets
                    customer_pets = self.review_agent._get_customer_pets(customer_id)
                    if not customer_pets:
                        print(f"  ⚠️ No pets found for customer {customer_id}")
                        continue
                    
                    # Get customer orders
                    customer_orders = self.review_agent._get_customer_orders(customer_id)
                    
                    # Process each pet
                    customer_results = {}
                    for pet_name in customer_pets:
                        print(f"  🐾 Analyzing pet {pet_name} for customer {customer_id}...")
                        pet_reviews = self.review_agent._get_pet_reviews(customer_id, pet_name)
                        insights = self.review_agent._analyze_pet_attributes_with_llm(pet_reviews, customer_orders, pet_name)
                        
                        # Format the insights
                        pet_insight = {
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
                            "MostOrderedProducts": insights.get("MostOrderedProducts", []),
                            "ConfidenceScore": insights.get("ConfidenceScore", 0.0)
                        }
                        customer_results[pet_name] = pet_insight
                    
                    results[customer_id] = customer_results
                    print(f"  ✅ Completed customer {customer_id}")
                    
                except Exception as e:
                    print(f"  ❌ Error processing customer {customer_id}: {e}")
                    continue
        else:
            # Process all customers
            print("Processing all customers...")
            results = self.review_agent.process_customer_data()
        
        print(f"✅ Generated enriched profiles for {len(results)} customers")
        
        # Add confidence scores to all results
        print("\n🎯 Adding confidence scores to enriched profiles...")
        from add_confidence_score import ConfidenceScoreCalculator
        calculator = ConfidenceScoreCalculator()
        
        for customer_id, pets_data in results.items():
            # Calculate confidence scores for this customer's pets
            pet_confidence_scores = []
            for pet_name, pet_data in pets_data.items():
                confidence_score = calculator.calculate_confidence_score(pet_data)
                pet_data['confidence_score'] = confidence_score
                pet_confidence_scores.append(confidence_score)
                print(f"  📊 {customer_id}/{pet_name}: confidence_score = {confidence_score:.3f}")
            
            # Calculate customer confidence score and store it at customer level
            if pet_confidence_scores:
                customer_confidence_score = sum(pet_confidence_scores) / len(pet_confidence_scores)
                # Store customer confidence score at the customer level, not within pets data
                results[customer_id] = {
                    'pets': pets_data,
                    'cust_confidence_score': customer_confidence_score
                }
                print(f"  🏠 {customer_id}: customer_confidence_score = {customer_confidence_score:.3f}")
        
        print("✅ Confidence scores added to all enriched profiles")
        return results
    
    def run_narrative_generation_agent_boyue(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Boyue Narrative Generation Agent to create letters and image prompts."""
        print("\n✍️ Running Boyue Narrative Generation Agent...")
        
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
                # Prepare data for Boyue agent
                # The Boyue agent expects pet_data in format: {customer_id: {pet_name: pet_info}}
                pet_data_for_boyue = {customer_id: pets_data}
                
                # Load review data to get customer-specific reviews
                qualifying_reviews_path = self.data_dir / "qualifying_reviews.csv"
                qualifying_reviews = pd.read_csv(qualifying_reviews_path)
                
                # Filter reviews for this customer
                customer_reviews = qualifying_reviews[qualifying_reviews['CUSTOMER_ID'] == int(customer_id)]

                # Rename columns to match Boyue agent expectations
                customer_reviews = customer_reviews.rename(columns={
                    "CUSTOMER_ID": "customer_id",
                    "REVIEW_TXT": "review_text",
                    "PRODUCT_NAME": "product_name",
                    "PET_NAME1": "pet_name"
                })

                # Select only the expected columns
                expected_cols = ["customer_id", "review_text", "product_name", "pet_name"]
                customer_reviews = customer_reviews[expected_cols]

                # Convert to the format expected by Boyue agent
                review_data_for_boyue = {
                    'reviews': customer_reviews.to_dict('records')
                }
                
                # Generate letter and visual prompt using Boyue agent
                boyue_output = self.narrative_agent.generate_output(pet_data_for_boyue, review_data_for_boyue)
                
                customer_narratives = {
                    'customer_id': customer_id,
                    'pets': pets_data,
                    'collective_letter': boyue_output.get('letter', ''),
                    'visual_prompt': boyue_output.get('visual_prompt', ''),
                    'cust_confidence_score': customer_confidence_score
                }
                
                narrative_results[customer_id] = customer_narratives
                print(f"    ✅ Generated collective letter and visual prompt")
                
            except Exception as e:
                print(f"    ❌ Error generating narratives for customer {customer_id}: {e}")
                # Create fallback structure
                customer_narratives = {
                    'customer_id': customer_id,
                    'pets': pets_data,
                    'collective_letter': f"Dear Human,\n\nWe love you!\n\nFrom: Your pets",
                    'visual_prompt': "A cozy home with pets",
                    'cust_confidence_score': customer_confidence_score
                }
                narrative_results[customer_id] = customer_narratives
        
        print(f"✅ Generated narratives for {len(narrative_results)} customers")
        return narrative_results
    
    def run_image_generation_agent(self, narrative_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Image Generation Agent to create images from visual prompts."""
        print("\n🎨 Running Image Generation Agent...")
        
        image_results = {}
        
        for customer_id, customer_data in narrative_results.items():
            print(f"  🖼️ Generating images for customer {customer_id}...")
            customer_images = {}
            
            # Get the collective visual prompt from Boyue agent
            visual_prompt = customer_data.get('visual_prompt', '')
            
            if visual_prompt:
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
                    customer_images['collective_image'] = image_url
                    
                    print(f"    ✅ Generated collective image")
                    
                except Exception as e:
                    print(f"    ❌ Error generating collective image: {e}")
                    customer_images['collective_image'] = None
            else:
                print(f"    ⚠️ No visual prompt available for customer {customer_id}")
                customer_images['collective_image'] = None
            
            image_results[customer_id] = customer_images
        
        print(f"✅ Generated images for {len(image_results)} customers")
        return image_results
    
    def save_outputs(self, enriched_profiles: Dict[str, Any], 
                    narrative_results: Dict[str, Any], 
                    image_results: Dict[str, Any]):
        """Save all outputs to the Output_Boyue directory structure."""
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
            
            # Save letter
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
                f.write(narrative_results[customer_id]['visual_prompt'])
                f.write("\n\n")
            
            # Save images (download and save)
            if customer_id in image_results:
                images_dir = customer_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                for image_name, image_url in image_results[customer_id].items():
                    if image_url:
                        try:
                            import requests
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                image_path = images_dir / f"{image_name}.png"
                                with open(image_path, 'wb') as f:
                                    f.write(response.content)
                                print(f"    💾 Saved {image_name}")
                        except Exception as e:
                            print(f"    ❌ Error saving {image_name}: {e}")
            
            print(f"  ✅ Saved outputs for customer {customer_id}")
    
    def run_pipeline(self, customer_ids: List[str] = None):
        """Run the complete pipeline for specified customers or all customers."""
        print("🚀 Starting Chewy Playback Pipeline with Boyue Agent")
        print("=" * 60)
        
        try:
            # Step 1: Preprocess data
            self.preprocess_data()
            
            # Step 2: Run Review and Order Intelligence Agent
            enriched_profiles = self.run_review_intelligence_agent(customer_ids)
            
            # Step 3: Run Boyue Narrative Generation Agent
            narrative_results = self.run_narrative_generation_agent_boyue(enriched_profiles)
            
            # Step 4: Run Image Generation Agent
            image_results = self.run_image_generation_agent(narrative_results)
            
            # Step 5: Save all outputs
            self.save_outputs(enriched_profiles, narrative_results, image_results)
            
            print("\n🎉 Pipeline completed successfully!")
            print(f"📁 Check the 'Output_Boyue' directory for results")
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            raise


def main():
    """Main function to run the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chewy Playback Pipeline with Boyue Agent")
    parser.add_argument("--customers", nargs="+", help="Specific customer IDs to process")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use environment variable)")
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = ChewyPlaybackPipelineBoyue(openai_api_key=args.api_key)
        
        # Run pipeline
        pipeline.run_pipeline(customer_ids=args.customers)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 