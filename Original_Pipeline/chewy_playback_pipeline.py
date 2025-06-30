#!/usr/bin/env python3
"""
Chewy Playback Pipeline
Orchestrates the flow of data through all three agents:
1. Review and Order Intelligence Agent
2. Narrative Generation Agent  
3. Image Generation Agent
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

# Add agent directories to path
sys.path.append('Agents/Review_and_Order_Intelligence_Agent')
sys.path.append('Agents/Narrative_Generation_Agent')
sys.path.append('Agents/Image_Generation_Agent')

from review_order_intelligence_agent import ReviewOrderIntelligenceAgent
from letter_prompt_generation import generate_letter_with_openai, generate_visual_prompt_for_pet, generate_collective_letter_with_openai
from add_confidence_score import ConfidenceScoreCalculator
import openai
from dotenv import load_dotenv


class ChewyPlaybackPipeline:
    """Main pipeline class that orchestrates all three agents."""
    
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
        self.output_dir = Path("Output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents
        self.review_agent = ReviewOrderIntelligenceAgent(openai_api_key=self.openai_api_key)
        
    def preprocess_data(self):
        """Preprocess the raw CSV data for the Review and Order Intelligence Agent."""
        print("🔄 Preprocessing data...")
        
        # Check if preprocessed files exist
        preprocessed_order_path = "Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv"
        preprocessed_review_path = "Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv"
        
        if not (os.path.exists(preprocessed_order_path) and os.path.exists(preprocessed_review_path)):
            print("📊 Running data preprocessing...")
            import subprocess
            
            # Run the preprocessing script from the agent directory
            agent_dir = "Agents/Review_and_Order_Intelligence_Agent"
            subprocess.run([
                sys.executable, 
                "preprocess_data.py"
            ], cwd=agent_dir, check=True)
        else:
            print("✅ Preprocessed data already exists")
    
    def run_review_intelligence_agent(self, customer_ids: List[str] = None) -> Dict[str, Any]:
        """Run the Review and Order Intelligence Agent to generate enriched pet profiles."""
        print("\n🧠 Running Review and Order Intelligence Agent...")
        
        # Load preprocessed data
        success = self.review_agent.load_data(
            order_history_path="Agents/Review_and_Order_Intelligence_Agent/processed_orderhistory.csv",
            qualifying_reviews_path="Agents/Review_and_Order_Intelligence_Agent/processed_qualifyingreviews.csv"
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
    
    def run_narrative_generation_agent(self, enriched_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Narrative Generation Agent to create letters and image prompts."""
        print("\n✍️ Running Narrative Generation Agent...")
        
        narrative_results = {}
        
        for customer_id, customer_data in enriched_profiles.items():
            print(f"  📝 Generating narratives for customer {customer_id}...")
            customer_narratives = {
                'customer_id': customer_id,
                'pets': {},
                'collective_letter': '',
                'visual_prompts': {}
            }
            
            # Handle new structure where pets data might be nested
            if isinstance(customer_data, dict) and 'pets' in customer_data:
                pets_data = customer_data['pets']
                customer_confidence_score = customer_data.get('cust_confidence_score', 0.0)
            else:
                # Handle old structure for backward compatibility
                pets_data = customer_data
                customer_confidence_score = 0.0
            
            # Generate one collective letter from all pets
            try:
                collective_letter = generate_collective_letter_with_openai(pets_data, self.openai_api_key)
                customer_narratives['collective_letter'] = collective_letter
                print(f"    ✅ Generated collective letter from all pets")
            except Exception as e:
                print(f"    ❌ Error generating collective letter: {e}")
                # Use fallback collective letter
                from letter_prompt_generation import generate_collective_fallback_letter
                collective_letter = generate_collective_fallback_letter(pets_data)
                customer_narratives['collective_letter'] = collective_letter
            
            # Generate collective visual prompt for all pets
            try:
                from letter_prompt_generation import generate_collective_visual_prompt
                collective_visual_prompt = generate_collective_visual_prompt(pets_data)
                
                customer_narratives['pets'] = pets_data
                customer_narratives['collective_visual_prompt'] = collective_visual_prompt
                
                print(f"    ✅ Generated collective visual prompt for all pets")
                
            except Exception as e:
                print(f"    ❌ Error generating collective visual prompt: {e}")
                customer_narratives['pets'] = pets_data
                customer_narratives['collective_visual_prompt'] = ""
            
            # Store customer confidence score in narrative results
            customer_narratives['cust_confidence_score'] = customer_confidence_score
            
            narrative_results[customer_id] = customer_narratives
        
        print(f"✅ Generated narratives for {len(narrative_results)} customers")
        return narrative_results
    
    def run_image_generation_agent(self, narrative_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Image Generation Agent to create collective images from visual prompts."""
        print("\n🎨 Running Image Generation Agent...")
        
        image_results = {}
        
        for customer_id, customer_data in narrative_results.items():
            print(f"  🖼️ Generating collective image for customer {customer_id}...")
            
            collective_visual_prompt = customer_data.get('collective_visual_prompt', '')
            
            if collective_visual_prompt:
                try:
                    # Generate collective image using OpenAI DALL-E
                    response = self.openai_client.images.generate(
                        model="dall-e-3",
                        prompt=collective_visual_prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1,
                    )
                    
                    # Get image URL
                    image_url = response.data[0].url
                    image_results[customer_id] = image_url
                    
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
                    image_results: Dict[str, Any]):
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
            
            # Save collective image (download and save)
            if customer_id in image_results and image_results[customer_id]:
                images_dir = customer_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                try:
                    import requests
                    response = requests.get(image_results[customer_id])
                    if response.status_code == 200:
                        image_path = images_dir / "collective_pet_portrait.png"
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                        print(f"    💾 Saved collective image for all pets")
                except Exception as e:
                    print(f"    ❌ Error saving collective image: {e}")
            
            print(f"  ✅ Saved outputs for customer {customer_id}")
    
    def run_pipeline(self, customer_ids: List[str] = None):
        """Run the complete pipeline for specified customers or all customers."""
        print("🚀 Starting Chewy Playback Pipeline")
        print("=" * 50)
        
        try:
            # Step 1: Preprocess data
            self.preprocess_data()
            
            # Step 2: Run Review and Order Intelligence Agent
            enriched_profiles = self.run_review_intelligence_agent(customer_ids)
            
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
    
    parser = argparse.ArgumentParser(description="Chewy Playback Pipeline")
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