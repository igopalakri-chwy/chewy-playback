#!/usr/bin/env python3
"""
Pet Letter & Visual Prompt Generator
A system that generates playful letters and visual prompts from pets using LLM reasoning.
"""

import json
import argparse
from typing import Dict, List, Any, Optional
import openai
import os


class PetLetterLLMSystem:
    """A system that generates playful letters and visual prompts from pets."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.use_llm = True
        
        if openai_api_key:
            openai.api_key = openai_api_key
        elif os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
        else:
            raise ValueError("OpenAI API key required. Provide via --api-key or OPENAI_API_KEY environment variable.")
    
    def load_json_file(self, filepath: str) -> Dict[str, Any]:
        """Load and parse a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error reading {filepath}: {e}")
    
    def extract_data(self, pet_data: Dict[str, Any], secondary_data: Dict[str, Any]) -> tuple:
        """Extract sample_pet_data and either sample_review_data or sample_order_data from input files."""
        # Extract pet data list
        sample_pet_data = []
        if isinstance(pet_data, dict):
            for customer_id, pets in pet_data.items():
                if isinstance(pets, dict):
                    for pet_name, pet_info in pets.items():
                        if isinstance(pet_info, dict):
                            pet_info['name'] = pet_name
                            sample_pet_data.append(pet_info)
        
        # Detect data type and extract accordingly
        data_type = "unknown"
        sample_review_data = []
        sample_order_data = []
        
        if isinstance(secondary_data, dict):
            if 'reviews' in secondary_data:
                data_type = "reviews"
                sample_review_data = secondary_data['reviews']
            elif 'order_history' in secondary_data:
                data_type = "orders"
                sample_order_data = secondary_data['order_history']
        elif isinstance(secondary_data, list):
            # Try to determine type based on first item structure
            if secondary_data and len(secondary_data) > 0:
                first_item = secondary_data[0]
                if 'review_text' in first_item or 'rating' in first_item:
                    data_type = "reviews"
                    sample_review_data = secondary_data
                elif 'item_type' in first_item or 'order_date' in first_item:
                    data_type = "orders"
                    sample_order_data = secondary_data
        
        return sample_pet_data, sample_review_data, sample_order_data, data_type
    
    def generate_output(self, pet_data: Dict[str, Any], secondary_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a JSON object containing a playful letter and visual prompt.
        Uses LLM reasoning to interpret either review data or order history and pet profiles.
        """
        # Extract data
        sample_pet_data, sample_review_data, sample_order_data, data_type = self.extract_data(pet_data, secondary_data)
        
        # Prepare context for LLM based on data type
        if data_type == "reviews":
            context = self._prepare_context_reviews(sample_pet_data, sample_review_data)
        elif data_type == "orders":
            context = self._prepare_context_orders(sample_pet_data, sample_order_data)
        else:
            # Fallback: try both
            context = self._prepare_context_reviews(sample_pet_data, sample_review_data)
            if not sample_review_data:
                context = self._prepare_context_orders(sample_pet_data, sample_order_data)
        
        prompt = f"""You are an LLM that writes a JSON object containing:

1. A playful, personality-rich letter from the customer's pets.
2. A visual prompt describing an AI-generated, Chewy-branded artwork.
3. Individual personality analysis for each pet including badges and descriptive words.

You are given:
- `sample_pet_data`: A list of pet dictionaries. Each has:
  - `name`: e.g., "Turbo", "unknown"
  - `type`: e.g., "cat", "dog"
  - optional `breed`, `traits`, `age`, `size`, or color-based traits

- `sample_review_data` (if available): A list of product reviews. Each includes:
  - `product_name`
  - `review_text`
  - optional `rating`
  - optional `pet_name`

- `sample_order_data` (if available): A list of order history items. Each includes:
  - `product_name`
  - `item_type` (e.g., "food", "toy", "clothing", "treat")
  - `brand`
  - `quantity`
  - optional `pet_name`

==== INSTRUCTIONS ====

STEP 1 — INTERPRET DATA AND PET PROFILES:
- Use your reasoning skills to:
  1. If review data is available: Determine whether each review is **positive** based on tone and content.
     - Do not rely on rating alone.
     - Only use products that are clearly praised.
  2. If order history is available: Analyze the order history to understand what products the pets enjoy.
     - Consider item types (food, toys, clothing, treats) and brands.
     - Focus on frequently ordered items and favorite categories.
  3. Rewrite the product name in **natural, generic language** (e.g., "a super soft bed", "a twisty toy", "a festive light-up sweater").
     - Do not use the product name directly.

STEP 2 — GENERATE THE LETTER:
- Write a single letter from the perspective of the pets.
- If any pet is named `"unknown"`, sign the letter as: `"From: The {{number}} pets"`.
- - Otherwise, sign off with the actual pet names from `sample_pet_data` (comma-separated with "and").
- The letter should:
  - Mention the **positively reviewed** products (if review data available) or **frequently ordered** products (if order data available) using the LLM-generated natural description.
  - Express joy and personality using pet-like expressions (e.g., "zoomies of joy!", "snuggle squad reporting in!").
  - Avoid assigning products to specific pets unless the data clearly names a pet.
  - Reflect personality if traits are available.
  - Avoid marketing language or sounding like an ad.

STEP 3 — GENERATE THE VISUAL PROMPT:
- Describe a warm, playful, Chewy-branded scene featuring the pets.
- Include the positively reviewed products (if review data available) or frequently ordered products (if order data available), described naturally.
- If any pet is `"unknown"`:
  - Include a **generic** version of its `type` (e.g., "a generic domestic cat").
- If a pet has known physical traits (breed, size, age, color):
  - Include those in the visual description.
- Do NOT make up any physical characteristics that are not explicitly given.
- Include **Chewy branding subtly** — e.g., on a toy bin, food bowl, scarf label, or poster.

STEP 4 — ASSIGN HOUSEHOLD PERSONALITY BADGE:
Analyze the collective personality of all pets in the household based on:
- Combined profile traits and characteristics of all pets
- Associated reviews or order data
- Pet types and breeds in the household
- Overall household dynamics

Assign ONE personality badge for the entire household:
- **1 personality badge** from the 10 categories below that best represents the household's collective personality
- **3 compatible badge types** that would vibe well with the household
- **1 personality description** - a cool, one-sentence description that captures the household's personality vibe based on their collective traits

=== BADGE CATEGORIES ===
1. The Cuddler — affectionate, gentle, chill, snuggly  
2. The Explorer — curious, adventurous, independent, active  
3. The Guardian — protective, loyal, alert, watchful  
4. The Trickster — clever, mischievous, unpredictable, energetic  
5. The Scholar — observant, quiet, intelligent, puzzle-loving  
6. The Athlete — energetic, driven, fast, focused  
7. The Nurturer — comforting, social, motherly, empathetic  
8. The Diva — picky, confident, dramatic, stylish  
9. The Daydreamer — mellow, imaginative, slow-moving, sensitive  
10. The Shadow — shy, reserved, cautious, deeply loyal

==== OUTPUT FORMAT ====
You MUST return a valid JSON object with this EXACT structure:

{{
  "letter": "<write a playful letter from the pets' perspective>",
  "visual_prompt": "<describe a Chewy-branded scene with the pets and products>",
  "personality_badge": {{
    "badge": "<exact badge name from the 10 categories above>",
    "compatible_with": ["<badge1>", "<badge2>", "<badge3>"],
    "icon_png": "<badge_name_lowercase>.png",
    "description": "<one cool sentence that captures the household's personality vibe>"
  }}
}}

CRITICAL REQUIREMENTS:
1. Return ONLY the JSON object - no explanations, no markdown, no extra text
2. Use EXACT badge names from the 10 categories listed above
3. Assign ONE badge for the entire household based on collective personality
4. Use lowercase badge names for icon_png (e.g., "the_explorer.png", "the_diva.png")
5. Ensure all JSON syntax is valid (proper quotes, commas, brackets)

=== INPUT DATA ===
{context}

Generate the JSON object:"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a JSON generator that creates pet personality analysis. You MUST return ONLY valid JSON with no additional text, explanations, or markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # Fallback to hardcoded response
                return self._generate_fallback_output(sample_pet_data, sample_review_data, sample_order_data, data_type)
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self._generate_fallback_output(sample_pet_data, sample_review_data, sample_order_data, data_type)
    
    def _prepare_context_reviews(self, sample_pet_data: List[Dict[str, Any]], sample_review_data: List[Dict[str, Any]]) -> str:
        """Prepare context for LLM generation with review data."""
        context_parts = []
        
        # Pet data
        context_parts.append("SAMPLE_PET_DATA:")
        for pet in sample_pet_data:
            context_parts.append(f"- name: {pet.get('name', 'Unknown')}")
            context_parts.append(f"  type: {pet.get('type', pet.get('PetType', 'Unknown'))}")
            if pet.get('breed', pet.get('Breed')):
                context_parts.append(f"  breed: {pet.get('breed', pet.get('Breed'))}")
            if pet.get('traits', pet.get('PersonalityTraits')):
                context_parts.append(f"  traits: {pet.get('traits', pet.get('PersonalityTraits'))}")
            if pet.get('size', pet.get('SizeCategory')):
                context_parts.append(f"  size: {pet.get('size', pet.get('SizeCategory'))}")
            if pet.get('age', pet.get('LifeStage')):
                context_parts.append(f"  age: {pet.get('age', pet.get('LifeStage'))}")
            if pet.get('color', pet.get('Color')):
                context_parts.append(f"  color: {pet.get('color', pet.get('Color'))}")
        
        # Review data
        context_parts.append("\nSAMPLE_REVIEW_DATA:")
        for review in sample_review_data:
            context_parts.append(f"- product_name: {review.get('product_name', review.get('product', 'Unknown'))}")
            context_parts.append(f"  review_text: {review.get('review_text', '')}")
            if review.get('rating'):
                context_parts.append(f"  rating: {review.get('rating')}")
            if review.get('pet_name'):
                context_parts.append(f"  pet_name: {review.get('pet_name')}")
        
        return '\n'.join(context_parts)

    def _prepare_context_orders(self, sample_pet_data: List[Dict[str, Any]], sample_order_data: List[Dict[str, Any]]) -> str:
        """Prepare context for LLM generation with order data."""
        context_parts = []
        
        # Pet data
        context_parts.append("SAMPLE_PET_DATA:")
        for pet in sample_pet_data:
            context_parts.append(f"- name: {pet.get('name', 'Unknown')}")
            context_parts.append(f"  type: {pet.get('type', pet.get('PetType', 'Unknown'))}")
            if pet.get('breed', pet.get('Breed')):
                context_parts.append(f"  breed: {pet.get('breed', pet.get('Breed'))}")
            if pet.get('traits', pet.get('PersonalityTraits')):
                context_parts.append(f"  traits: {pet.get('traits', pet.get('PersonalityTraits'))}")
            if pet.get('size', pet.get('SizeCategory')):
                context_parts.append(f"  size: {pet.get('size', pet.get('SizeCategory'))}")
            if pet.get('age', pet.get('LifeStage')):
                context_parts.append(f"  age: {pet.get('age', pet.get('LifeStage'))}")
            if pet.get('color', pet.get('Color')):
                context_parts.append(f"  color: {pet.get('color', pet.get('Color'))}")
        
        # Order data
        context_parts.append("\nSAMPLE_ORDER_DATA:")
        for order in sample_order_data:
            context_parts.append(f"- product_name: {order.get('product_name', 'Unknown')}")
            context_parts.append(f"  item_type: {order.get('item_type', 'Unknown')}")
            context_parts.append(f"  brand: {order.get('brand', 'Unknown')}")
            context_parts.append(f"  quantity: {order.get('quantity', 1)}")
            if order.get('pet_name'):
                context_parts.append(f"  pet_name: {order.get('pet_name')}")
        
        return '\n'.join(context_parts)
    
    COMPATIBILITY_MAP = {
        "The Daydreamer": ["The Scholar", "The Shadow", "The Cuddler"],
        "The Guardian": ["The Athlete", "The Nurturer", "The Explorer"],
        "The Nurturer": ["The Guardian", "The Daydreamer", "The Cuddler"],
        "The Explorer": ["The Athlete", "The Trickster", "The Scholar"],
        "The Trickster": ["The Explorer", "The Charmer", "The Shadow"],
        "The Scholar": ["The Daydreamer", "The Explorer", "The Cuddler"],
        "The Athlete": ["The Guardian", "The Explorer", "The Trickster"],
        "The Cuddler": ["The Daydreamer", "The Nurturer", "The Scholar"],
        "The Shadow": ["The Trickster", "The Daydreamer", "The Scholar"],
        "The Charmer": ["The Trickster", "The Cuddler", "The Nurturer"]
    }

    def badge_icon_png(self, badge_name: str) -> str:
        """Return the PNG filename for a given badge name."""
        badge_mapping = {
            "The Daydreamer": "FrontEnd_Mobile/badge_daydreamer.png",
            "The Guardian": "FrontEnd_Mobile/badge_guardian.png",
            "The Nurturer": "FrontEnd_Mobile/badge_nurturer.png",
            "The Explorer": "FrontEnd_Mobile/badge_explorer.png",
            "The Trickster": "FrontEnd_Mobile/badge_trickster.png",
            "The Scholar": "FrontEnd_Mobile/badge_scholar.png",
            "The Athlete": "FrontEnd_Mobile/badge_athlete.png",
            "The Cuddler": "FrontEnd_Mobile/badge_cuddler.png",
            "The Shadow": "FrontEnd_Mobile/badge_shadow.png",
            "The Diva": "FrontEnd_Mobile/badge_diva.png"
        }
        return badge_mapping.get(badge_name, "FrontEnd_Mobile/badge_explorer.png")

    def summarize_purchase_history(self, purchases: list) -> str:
        """Summarize a pet's purchase history for LLM context."""
        if not purchases:
            return "No purchase data available."
        type_counts = {}
        brand_counts = {}
        product_counts = {}
        for p in purchases:
            t = p.get("item_type", "other").lower()
            b = p.get("brand", "").strip()
            prod = p.get("product_name", "").strip()
            type_counts[t] = type_counts.get(t, 0) + 1
            if b:
                brand_counts[b] = brand_counts.get(b, 0) + 1
            if prod:
                product_counts[prod] = product_counts.get(prod, 0) + 1
        # Frequent types
        frequent_types = sorted(type_counts, key=type_counts.get, reverse=True)[:2]
        frequent_brands = sorted(brand_counts, key=brand_counts.get, reverse=True)[:2]
        frequent_products = sorted(product_counts, key=product_counts.get, reverse=True)[:2]
        summary = []
        if frequent_types:
            summary.append(f"frequently receives {', '.join(frequent_types)}")
        if frequent_brands:
            summary.append(f"with a clear preference for {', '.join(frequent_brands)}")
        if frequent_products:
            summary.append(f"notable products include {', '.join(frequent_products)}")
        # Behavioral traits
        traits = []
        if len(type_counts) > 2:
            traits.append("variety-seeking")
        if any(count > 2 for count in brand_counts.values()):
            traits.append("brand-loyal")
        if "treat" in type_counts or "food" in type_counts:
            traits.append("food-motivated")
        if "toy" in type_counts:
            traits.append("playful")
        if traits:
            summary.append("they seem " + ' and '.join(traits))
        return "This pet " + ', '.join(summary) + "."

    def _llm_pet_personality(self, pet: dict, orders: list, purchase_summary: str = "No purchase data available.") -> dict:
        """Call LLM to extract traits, badge, and compatible badges for a pet, including purchase summary."""
        # Combine profile and orders
        profile_parts = []
        for key in ["traits", "PersonalityTraits", "BehavioralCues"]:
            val = pet.get(key, [])
            if isinstance(val, str):
                val = [val]
            profile_parts.extend(val)
        profile_str = "; ".join(profile_parts)
        order_str = " ".join([f"{o.get('item_type', '')} {o.get('brand', '')}" for o in orders])
        context = f"PROFILE: {profile_str}\nORDERS: {order_str}\nPURCHASE BEHAVIOR: {purchase_summary}"
        pet_name = pet.get("name", "Pet")
        prompt = (
            f"You are an expert at analyzing pet personalities. Given the following pet profile, order history, and purchase behavior, do the following:\n"
            f"1. Extract exactly 3 descriptive personality words for the pet (no more, no less).\n"
            f"2. Assign ONE badge from this list that best fits the pet: The Daydreamer, The Guardian, The Nurturer, The Explorer, The Trickster, The Scholar, The Athlete, The Cuddler, The Shadow, The Charmer. Only use these names.\n"
            f"3. Using the badge, select 2-3 compatible badge types from this compatibility map:\n{self.COMPATIBILITY_MAP}\n"
            f"4. Return a JSON object with:\n  - descriptive_words: [\"word1\", \"word2\", \"word3\"]\n  - personality_badge: \"...\"\n  - compatible_with: [\"...\", \"...\"]\n"
            f"\nPET PROFILE AND ORDER HISTORY AND PURCHASE BEHAVIOR:\n{context}\n"
            f"\nReturn only the JSON object. Do not add explanations."
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a pet personality analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
            # Build personality sentence
            words = result["descriptive_words"]
            badge = result["personality_badge"]
            sentence = f"{pet_name} is {words[0]}, {words[1]}, and {words[2]}, showing the spirit of a true {badge}."
            icon_png = self.badge_icon_png(badge)
            return {
                "name": pet_name,
                "descriptive_words": words,
                "personality_sentence": sentence,
                "personality_badge": badge,
                "compatible_with": result["compatible_with"],
                "icon_png": icon_png
            }
        except Exception as e:
            # Fallback: minimal output
            return {
                "name": pet.get("name", "Pet"),
                "descriptive_words": ["friendly", "gentle", "curious"],
                "personality_sentence": f"{pet.get('name', 'Pet')} is friendly, gentle, and curious, showing the spirit of a true Explorer.",
                "personality_badge": "The Explorer",
                "compatible_with": self.COMPATIBILITY_MAP["The Explorer"],
                "icon_png": self.badge_icon_png("The Explorer")
            }

    def _generate_fallback_output(self, sample_pet_data: List[Dict[str, Any]], sample_review_data: List[Dict[str, Any]], sample_order_data: List[Dict[str, Any]], data_type: str, purchase_history: Optional[List[dict]] = None) -> Dict[str, Any]:
        """Generate fallback output with per-pet badges using LLM and purchase history."""
        # Map data to pets based on type
        pet_reviews = {pet['name']: [] for pet in sample_pet_data}
        pet_orders = {pet['name']: [] for pet in sample_pet_data}
        
        if data_type == "reviews":
            for review in sample_review_data:
                for pet in sample_pet_data:
                    pet_name = pet.get('name', '').lower()
                    if pet_name and pet_name in review.get('review_text', '').lower():
                        pet_reviews[pet['name']].append(review)
        elif data_type == "orders":
            for order in sample_order_data:
                pet_name = order.get('pet_name', '')
                if pet_name in pet_orders:
                    pet_orders[pet_name].append(order)
        
        # Map purchase history to pets
        pet_purchases = {pet['name']: [] for pet in sample_pet_data}
        if purchase_history:
            for p in purchase_history:
                pet_name = p.get('pet_name', '')
                if pet_name in pet_purchases:
                    pet_purchases[pet_name].append(p)
        
        # Generate letter and visual prompt
        pet_names = [pet.get('name', 'Unknown') for pet in sample_pet_data]
        has_unknown = any(name.lower() == 'unknown' for name in pet_names)
        
        if has_unknown:
            signature = f"From: The {len(pet_names)} pets"
        else:
            if len(pet_names) == 1:
                signature = f"From: {pet_names[0]}"
            elif len(pet_names) == 2:
                signature = f"From: {pet_names[0]} and {pet_names[1]}"
            else:
                signature = f"From: {', '.join(pet_names[:-1])}, and {pet_names[-1]}"
        
        # Generate letter content based on data type
        letter = f"""Dear Human,

We hope this letter finds you well and ready for some serious cuddle time! We've been having the most amazing zoomies of joy with all the incredible things you've brought into our lives, and we just had to write to tell you how much we love everything!

"""
        
        # Add specific mentions based on data type
        if data_type == "reviews":
            # Analyze review data for positive mentions
            positive_products = []
            for review in sample_review_data:
                if review.get('rating', 0) >= 4 or 'love' in review.get('review_text', '').lower():
                    positive_products.append(review.get('product_name', review.get('product', '')))
            
            if positive_products:
                letter += f"We absolutely adore the {', '.join(positive_products[:3])} you've gotten for us! "
        
        elif data_type == "orders":
            # Analyze order data for product mentions
            item_types = {}
            brands = {}
            for order in sample_order_data:
                item_type = order.get('item_type', '')
                brand = order.get('brand', '')
                if item_type:
                    item_types[item_type] = item_types.get(item_type, 0) + 1
                if brand:
                    brands[brand] = brands.get(brand, 0) + 1
            
            common_types = sorted(item_types.items(), key=lambda x: x[1], reverse=True)[:3]
            if common_types:
                type_mentions = []
                for item_type, count in common_types:
                    if item_type == 'food':
                        type_mentions.append("delicious food")
                    elif item_type == 'toy':
                        type_mentions.append("amazing toys")
                    elif item_type == 'clothing':
                        type_mentions.append("stylish clothes")
                    elif item_type == 'treat':
                        type_mentions.append("yummy treats")
                
                if type_mentions:
                    letter += f"We absolutely adore the {', '.join(type_mentions)} you've spoiled us with! "
        
        letter += """It's like you've brought the thrill of the hunt right into our cozy home, and our tails haven't stopped wagging (or swishing, depending on who you ask)!

Every meal is like a gourmet feast, and we can't help but do our happy dance when you reach for the treat jar. The cozy things you've given us - whether it's soft beds, warm sweaters, or comfy spots - have made our home the most snuggle-approved place ever.

We feel so loved and cared for, and we want you to know that we appreciate every little thing you do for us. You always know exactly what we need to be happy, healthy, and entertained.

So from the bottom of our furry hearts, thank you for being the best human ever! We're so lucky to have you, and we promise to keep being the most loving, playful, and grateful pets you could ask for.

With all our love and zoomies,
{signature}

P.S. Can we have an extra treat for being such good pets? Pretty please with a paw on top!"""
        
        # Generate visual prompt
        pet_descriptions = []
        for pet in sample_pet_data:
            name = pet.get('name', 'Unknown')
            pet_type = pet.get('type', pet.get('PetType', 'Unknown')).lower()
            
            if name.lower() == 'unknown':
                pet_descriptions.append(f"a generic domestic {pet_type}")
            else:
                breed = pet.get('breed', pet.get('Breed'))
                if breed and breed.lower() not in ['unknown', 'unk']:
                    pet_descriptions.append(f"a {breed} {pet_type}")
                else:
                    pet_descriptions.append(f"a domestic {pet_type}")
        
        visual_prompt = f"""In a cozy, whimsical living room, {', '.join(pet_descriptions)} are enjoying their time together. The scene is filled with warm lighting and comfortable furniture. Chewy branding is subtly visible on a toy bin in the corner and a food bowl on the floor. The pets are surrounded by various beloved pet items including toys, food, and cozy accessories, creating a joyful and content atmosphere. The overall style is warm, colorful, and full of pet-loving charm."""
        
        # Per-pet badge assignment using LLM
        pets_output = []
        for pet in sample_pet_data:
            name = pet.get('name', 'Unknown')
            reviews = pet_reviews.get(name, [])
            orders = pet_orders.get(name, [])
            purchases = pet_purchases.get(name, [])
            purchase_summary = self.summarize_purchase_history(purchases)
            
            if data_type == "reviews":
                pet_result = self._llm_pet_personality(pet, reviews, purchase_summary)
            else:
                pet_result = self._llm_pet_personality(pet, orders, purchase_summary)
            
            pets_output.append(pet_result)
        
        return {
            "letter": letter,
            "visual_prompt": visual_prompt,
            "pets": pets_output
        }


def main():
    """Main function with argument handling."""
    parser = argparse.ArgumentParser(description='Pet Letter & Visual Prompt Generator')
    parser.add_argument('--pet-data', '-p', required=True, help='JSON file containing pet data')
    parser.add_argument('--secondary-data', '-s', required=True, help='JSON file containing either review data or order history data')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--output', '-out', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        system = PetLetterLLMSystem(openai_api_key=args.api_key)
        
        # Load data
        pet_data = system.load_json_file(args.pet_data)
        secondary_data = system.load_json_file(args.secondary_data)
        
        # Generate output
        result = system.generate_output(pet_data, secondary_data)
        
        # Output result
        output_json = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"Output saved to {args.output}")
        else:
            print(output_json)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 