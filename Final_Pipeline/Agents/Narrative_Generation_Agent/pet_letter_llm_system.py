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
import sys
from pathlib import Path
from location_background_generator import LocationBackgroundGenerator


class ZIPVisualAestheticsGenerator:
    """Generate visual aesthetics based on ZIP codes."""
    
    def __init__(self):
        self.openai_client = openai.OpenAI()
        self.location_generator = LocationBackgroundGenerator()
    
    def generate_aesthetics(self, zip_code: str) -> Dict[str, str]:
        """Generate visual aesthetics for a given ZIP code."""
        try:
            # Get location-specific background information
            location_data = self.location_generator.generate_location_background(zip_code)
            
            # Generate AI-enhanced aesthetics based on location
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing ZIP codes to determine regional visual aesthetics. Return only a JSON object with visual_style, color_texture, art_style, tone_style, and location_background fields."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze ZIP code {zip_code} (location: {location_data['city']}, {location_data['state']}) and provide regional visual aesthetics in JSON format with these fields: visual_style, color_texture, art_style, tone_style, location_background. Use the location data to enhance the aesthetics."
                    }
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON from response
            try:
                result = json.loads(content)
                # Add location data to the result
                result['location_data'] = location_data
                return result
            except json.JSONDecodeError:
                # Fallback to location-based aesthetics
                return self._get_location_based_aesthetics(location_data)
                
        except Exception as e:
            print(f"Error generating aesthetics for {zip_code}: {e}")
            return self._get_location_based_aesthetics(location_data)
    
    def _get_location_based_aesthetics(self, location_data: Dict[str, str]) -> Dict[str, str]:
        """Generate aesthetics based on location data when AI fails."""
        location_type = location_data.get('location_type', 'unknown')
        
        if location_type == 'major_city':
            return {
                'visual_style': 'urban sophisticated',
                'color_texture': 'vibrant dynamic',
                'art_style': 'contemporary urban',
                'tone_style': 'energetic, cosmopolitan',
                'location_background': location_data.get('background_description', ''),
                'location_data': location_data
            }
        elif location_type == 'state':
            return {
                'visual_style': 'natural regional',
                'color_texture': 'earthy warm',
                'art_style': 'landscape inspired',
                'tone_style': 'authentic, grounded',
                'location_background': location_data.get('background_description', ''),
                'location_data': location_data
            }
        else:
            return self._get_default_aesthetics()
    
    def _get_default_aesthetics(self) -> Dict[str, str]:
        """Return default aesthetics when analysis fails."""
        return {
            'visual_style': 'modern clean',
            'color_texture': 'smooth neutral',
            'art_style': 'contemporary minimal',
            'tone_style': 'friendly, warm',
            'location_background': 'a beautiful outdoor setting with natural scenery',
            'location_data': {'city': 'Unknown', 'state': 'Unknown', 'location_type': 'unknown'}
        }


class PetLetterLLMSystem:
    """A system that generates playful letters and visual prompts from pets."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.use_llm = True
        
        # Personality badge descriptive words mapping
        self.badge_descriptive_words = {
            "The Cuddler": ["affectionate", "gentle", "chill", "snuggly"],
            "The Explorer": ["curious", "adventurous", "independent", "active"],
            "The Guardian": ["protective", "loyal", "alert", "watchful"],
            "The Trickster": ["clever", "mischievous", "unpredictable", "energetic"],
            "The Scholar": ["observant", "quiet", "intelligent", "puzzle-loving"],
            "The Athlete": ["energetic", "driven", "fast", "focused"],
            "The Nurturer": ["comforting", "social", "motherly", "empathetic"],
            "The Diva": ["picky", "confident", "dramatic", "stylish"],
            "The Daydreamer": ["mellow", "imaginative", "slow-moving", "sensitive"],
            "The Shadow": ["shy", "reserved", "cautious", "deeply loyal"]
        }
        
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
            # Always extract order data if available (for ZIP code extraction)
            if 'order_history' in secondary_data:
                sample_order_data = secondary_data['order_history']
            
            # Extract review data if available
            if 'reviews' in secondary_data:
                sample_review_data = secondary_data['reviews']
                data_type = "reviews"
            elif sample_order_data:
                data_type = "orders"
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
    
    def extract_zip_code_from_orders(self, sample_order_data: List[Dict[str, Any]]) -> Optional[str]:
        """Extract ZIP code from order data."""
        if not sample_order_data:
            return None
        
        # Look for ZIP code in the order data
        for order in sample_order_data:
            # Check different possible field names for ZIP code
            zip_code = order.get('zip_code') or order.get('ZIP_CODE') or order.get('zip') or order.get('ZIP')
            if zip_code:
                # Clean the ZIP code (remove any extra info like "-3415")
                clean_zip = str(zip_code).split('-')[0].strip()
                if len(clean_zip) == 5 and clean_zip.isdigit():
                    return clean_zip
        
        return None
    
    def get_zip_aesthetics(self, zip_code: str) -> Dict[str, str]:
        """Get visual aesthetics for a ZIP code using the ZIP aesthetics generator."""
        try:
            generator = ZIPVisualAestheticsGenerator()
            aesthetics = generator.generate_aesthetics(zip_code)
            
            # Add a 'tones' field based on the aesthetics
            tones = self._derive_tones_from_aesthetics(aesthetics)
            aesthetics['tones'] = tones
            
            # Add location context for narrative generation
            location_context = generator.location_generator.get_location_context(zip_code)
            aesthetics['location_context'] = location_context
            
            return aesthetics
        except Exception as e:
            print(f"Warning: Could not get ZIP aesthetics for {zip_code}: {e}")
            return self._get_default_aesthetics()
    
    def _derive_tones_from_aesthetics(self, aesthetics: Dict[str, str]) -> str:
        """Derive appealing tones from the visual aesthetics."""
        visual_style = aesthetics.get('visual_style', '').lower()
        color_texture = aesthetics.get('color_texture', '').lower()
        art_style = aesthetics.get('art_style', '').lower()
        
        tones = []
        
        # Analyze visual style for tones
        if 'urban' in visual_style or 'modern' in visual_style:
            tones.append('sophisticated')
        if 'tropical' in visual_style or 'vibrant' in color_texture:
            tones.append('energetic')
        if 'luxury' in visual_style or 'elegant' in art_style:
            tones.append('premium')
        if 'rustic' in visual_style or 'earthy' in color_texture:
            tones.append('authentic')
        if 'minimal' in art_style or 'clean' in visual_style:
            tones.append('refined')
        
        # Default tones if none derived
        if not tones:
            tones = ['warm', 'friendly']
        
        return ', '.join(tones)
    
    def _get_default_aesthetics(self) -> Dict[str, str]:
        """Return default aesthetics when ZIP analysis fails."""
        return {
            'visual_style': 'modern clean',
            'color_texture': 'smooth neutral',
            'art_style': 'contemporary minimal',
            'tones': 'warm, friendly',
            'location_background': 'a beautiful outdoor setting with natural scenery',
            'location_context': 'Use general regional aesthetics for the background.',
            'location_data': {'city': 'Unknown', 'state': 'Unknown', 'location_type': 'unknown'}
        }
    
    def generate_output(self, pet_data: Dict[str, Any], secondary_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a JSON object containing a playful letter and visual prompt.
        Uses LLM reasoning to interpret either review data or order history and pet profiles.
        ZIP aesthetics are only used to influence the style, background, and tone, but are never directly mentioned in the letter text.
        """
        # Extract data
        sample_pet_data, sample_review_data, sample_order_data, data_type = self.extract_data(pet_data, secondary_data)
        
        # Get ZIP code and aesthetics
        zip_code = self.extract_zip_code_from_orders(sample_order_data)
        zip_aesthetics = None
        if zip_code:
            print(f"  🗺️ Found ZIP code: {zip_code}")
            zip_aesthetics = self.get_zip_aesthetics(zip_code)
            print(f"  🎨 ZIP aesthetics: {zip_aesthetics['visual_style']}, {zip_aesthetics['color_texture']}, {zip_aesthetics['art_style']}")
        else:
            print(f"  ⚠️ No ZIP code found, using default aesthetics")
            zip_aesthetics = self._get_default_aesthetics()
        
        # Prepare context for LLM based on data type
        if data_type == "reviews":
            context = self._prepare_context_reviews(sample_pet_data, sample_review_data, zip_aesthetics)
        elif data_type == "orders":
            context = self._prepare_context_orders(sample_pet_data, sample_order_data, zip_aesthetics)
        else:
            # Fallback: try both
            context = self._prepare_context_reviews(sample_pet_data, sample_review_data, zip_aesthetics)
            if not sample_review_data:
                context = self._prepare_context_orders(sample_pet_data, sample_order_data, zip_aesthetics)
        
        prompt = f"""You are an LLM that writes a JSON object containing:

1. A playful, personality-rich letter from the customer's pets.
2. A visual prompt describing an AI-generated, Chewy-branded artwork with EXACTLY the number of pets specified.
3. Individual personality analysis for each pet including badges and descriptive words.

You are given:
- `sample_pet_data`: A list of pet dictionaries. Each has:
  - `name`: e.g., "Turbo", "unknown"
  - `type`: e.g., "cat", "dog"
  - optional `breed`, `traits`, `age`, `size`, `weight`, or color-based traits

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

- `zip_aesthetics` (if available): Regional visual aesthetics including:
  - `visual_style`: Regional visual characteristics
  - `color_texture`: Regional color and texture preferences
  - `art_style`: Regional art style preferences
  - `tones`: Appealing tones for the region
  - `location_background`: Specific location-based background description
  - `location_context`: Location context for narrative generation

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
- Write a **SHORT, CONCISE** letter from the perspective of the pets (aim for 2-3 sentences maximum).
- If any pet is named `"unknown"`, sign the letter as: `"From: The pets"`.
- Otherwise, sign off with the actual pet names from `sample_pet_data` (comma-separated with "and").
- The letter should:
  - **Keep it brief**: Focus on one main message or product mention.
  - Mention the **positively reviewed** products (if review data available) or **frequently ordered** products (if order data available) using the LLM-generated natural description.
  - Express joy and personality using pet-like expressions (e.g., "zoomies of joy!", "snuggle squad reporting in!").
  - Avoid assigning products to specific pets unless the data clearly names a pet.
  - Reflect personality if traits are available.
  - **Incorporate only the tones and style cues** from `zip_aesthetics` to influence the mood and feel of the letter, but **do NOT directly mention any region, ZIP code, city, or style name** in the letter text.
  - Avoid marketing language or sounding like an ad.
  - **Use proper letter formatting**: Include a space after the salutation (e.g., "Dear Human,\n\n"), a space before the ending (e.g., "\n\nWith all our love and zoomies,"), and keep the body text flowing naturally without excessive line breaks.
  - **LENGTH CONSTRAINT**: The letter body should be no more than 2-3 sentences total.

STEP 3 — GENERATE THE VISUAL PROMPT:
- **CRITICAL PET COUNT RULE: You MUST count the pets in sample_pet_data and ensure the image contains EXACTLY that number of pets.**
- **PET COUNT VERIFICATION: Before writing the visual prompt, count the pets in sample_pet_data. The image must show exactly this number of pets - no more, no less.**
- **ABSOLUTELY NO EXTRA PETS: Do not add any additional pets, background pets, implied pets, or random pets. Only include the pets listed in sample_pet_data.**
- **EXACT PET MATCH: The number of pets in the visual description must exactly match the number of pets in sample_pet_data.**
- **PET TYPE ACCURACY: You MUST specify the exact pet type (dog/cat) for each pet based on the data. Do not change or guess pet types.**
- **EXPLICIT PET TYPES: Start the visual prompt by explicitly stating the pet count and types (e.g., "four dogs and one cat" or "three cats and two dogs").**
- **CRITICAL: DO NOT MENTION PET NAMES in the visual prompt. Focus on physical characteristics instead.**
- Describe a sophisticated artistic pet portrait scene featuring the pets as the main subjects.
- **Pets should be the clear focus** - describe their appearance, poses, and expressions prominently with joyful energy.
- **MANDATORY PHYSICAL TRAITS: You MUST include breed, size, and weight information for each pet when available:**
  - **BREED**: Always mention the breed if known (e.g., "Shih Tzu dogs", "Beagle mix", "domestic cat")
  - **SIZE/WEIGHT**: Always include size/weight descriptions (e.g., "small 10-pound", "medium 16-pound", "large 63-pound")
  - **AGE**: Include age/life stage when available (e.g., "young", "adult", "senior")
  - **GENDER**: Include gender when available (e.g., "male", "female")
- **ZIP aesthetics influence the background and style**, not the main pet focus:
  - Use the `visual_style` to describe background elements and setting
  - Apply the `color_texture` to influence the overall color palette
  - Follow the `art_style` for style direction in the background
  - **LOCATION BACKGROUND**: Incorporate the `location_background` description as the background setting (e.g., "Space Needle with Seattle skyline", "Golden Gate Bridge spanning the bay", "Mount Rainier visible through window")
  - The pets remain the primary subjects regardless of ZIP aesthetics
  - The location background should be visible but not overwhelming - it should enhance the scene without dominating it
- Include the positively reviewed products (if review data available) or frequently ordered products (if order data available), described naturally as props or accessories.
- If any pet is `"unknown"`:
  - Include a **generic** version of its `type` (e.g., "a generic domestic cat").
- **PHYSICAL TRAIT PRIORITY**: When describing pets, prioritize physical characteristics over names:
  - Instead of "Maxine, Theo, Gigi, and Daniel" → "four dogs of varying sizes"
  - Instead of "Anyanka the cat" → "a domestic cat"
  - Focus on: breed, size, weight, age, gender, and physical appearance
- Do NOT make up any physical characteristics that are not explicitly given.
- Include **Chewy branding subtly** — e.g., on a toy bin, food bowl, scarf label, or poster in the background.
- **LIGHTING AND BRIGHTNESS: The scene should be bright and well-lit with vibrant, cheerful lighting. Use bright, warm lighting that illuminates the pets clearly. Avoid dark shadows or dim lighting. The overall atmosphere should be bright, sunny, and uplifting.**
- The scene should be sophisticated, artistic, wholesome, warm, and inviting with joyous energy, suitable for a refined artistic pet portrait that customers would love to receive.

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
    "description": "<one cool sentence that captures the household's personality vibe>",
    "descriptive_words": ["<word1>", "<word2>", "<word3>", "<word4>"]
  }}
}}

CRITICAL REQUIREMENTS:
1. Return ONLY the JSON object - no explanations, no markdown, no extra text
2. Use EXACT badge names from the 10 categories listed above
3. Assign ONE badge for the entire household based on collective personality
4. Use lowercase badge names for icon_png (e.g., "the_explorer.png", "the_diva.png")
5. Ensure all JSON syntax is valid (proper quotes, commas, brackets)
6. **Do NOT mention any region, ZIP code, city, or style name directly in the letter. Only use the tones and style cues to influence the mood and feel.**
7. **FINAL PET COUNT CHECK: The visual_prompt must describe exactly the number of pets in sample_pet_data. Count them carefully and ensure no extra pets are added.**

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
                # Add ZIP aesthetics to the result
                result['zip_aesthetics'] = zip_aesthetics
                # Add descriptive words to the personality badge if not already present
                if 'personality_badge' in result and 'badge' in result['personality_badge']:
                    badge_name = result['personality_badge']['badge']
                    if badge_name in self.badge_descriptive_words:
                        result['personality_badge']['descriptive_words'] = self.badge_descriptive_words[badge_name]
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        # Add ZIP aesthetics to the result
                        result['zip_aesthetics'] = zip_aesthetics
                        # Add descriptive words to the personality badge if not already present
                        if 'personality_badge' in result and 'badge' in result['personality_badge']:
                            badge_name = result['personality_badge']['badge']
                            if badge_name in self.badge_descriptive_words:
                                result['personality_badge']['descriptive_words'] = self.badge_descriptive_words[badge_name]
                        return result
                    except json.JSONDecodeError:
                        pass
                
                # Fallback to hardcoded response
                fallback_result = self._generate_fallback_output(sample_pet_data, sample_review_data, sample_order_data, data_type)
                fallback_result['zip_aesthetics'] = zip_aesthetics
                # Add descriptive words to the personality badge if not already present
                if 'personality_badge' in fallback_result and 'badge' in fallback_result['personality_badge']:
                    badge_name = fallback_result['personality_badge']['badge']
                    if badge_name in self.badge_descriptive_words:
                        fallback_result['personality_badge']['descriptive_words'] = self.badge_descriptive_words[badge_name]
                return fallback_result
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
            fallback_result = self._generate_fallback_output(sample_pet_data, sample_review_data, sample_order_data, data_type)
            fallback_result['zip_aesthetics'] = zip_aesthetics
            # Add descriptive words to the personality badge if not already present
            if 'personality_badge' in fallback_result and 'badge' in fallback_result['personality_badge']:
                badge_name = fallback_result['personality_badge']['badge']
                if badge_name in self.badge_descriptive_words:
                    fallback_result['personality_badge']['descriptive_words'] = self.badge_descriptive_words[badge_name]
            return fallback_result
    
    def _prepare_context_reviews(self, sample_pet_data: List[Dict[str, Any]], sample_review_data: List[Dict[str, Any]], zip_aesthetics: Optional[Dict[str, str]] = None) -> str:
        """Prepare context for LLM generation with review data."""
        context_parts = []
        
        # Pet data with enhanced information
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
            if pet.get('weight', pet.get('Weight')):
                context_parts.append(f"  weight: {pet.get('weight', pet.get('Weight'))}")
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
        
        # Add ZIP aesthetics to context if available
        if zip_aesthetics:
            context_parts.append("\nZIP_AESTHETICS:")
            context_parts.append(f"- visual_style: {zip_aesthetics['visual_style']}")
            context_parts.append(f"- color_texture: {zip_aesthetics['color_texture']}")
            context_parts.append(f"- art_style: {zip_aesthetics['art_style']}")
            context_parts.append(f"- tones: {zip_aesthetics['tones']}")
            if zip_aesthetics.get('location_background'):
                context_parts.append(f"- location_background: {zip_aesthetics['location_background']}")
            if zip_aesthetics.get('location_context'):
                context_parts.append(f"- location_context: {zip_aesthetics['location_context']}")
        
        return '\n'.join(context_parts)

    def _prepare_context_orders(self, sample_pet_data: List[Dict[str, Any]], sample_order_data: List[Dict[str, Any]], zip_aesthetics: Optional[Dict[str, str]] = None) -> str:
        """Prepare context for LLM generation with order data."""
        context_parts = []
        
        # Pet data with enhanced information
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
            if pet.get('weight', pet.get('Weight')):
                context_parts.append(f"  weight: {pet.get('weight', pet.get('Weight'))}")
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
        
        # Add ZIP aesthetics to context if available
        if zip_aesthetics:
            context_parts.append("\nZIP_AESTHETICS:")
            context_parts.append(f"- visual_style: {zip_aesthetics['visual_style']}")
            context_parts.append(f"- color_texture: {zip_aesthetics['color_texture']}")
            context_parts.append(f"- art_style: {zip_aesthetics['art_style']}")
            context_parts.append(f"- tones: {zip_aesthetics['tones']}")
            if zip_aesthetics.get('location_background'):
                context_parts.append(f"- location_background: {zip_aesthetics['location_background']}")
            if zip_aesthetics.get('location_context'):
                context_parts.append(f"- location_context: {zip_aesthetics['location_context']}")
        
        return '\n'.join(context_parts)
    
    def _determine_household_badge(self, sample_pet_data: List[Dict[str, Any]], sample_review_data: List[Dict[str, Any]], sample_order_data: List[Dict[str, Any]], data_type: str) -> str:
        """Determine household badge based on pet characteristics and data."""
        # Analyze pet types and traits
        pet_types = [pet.get('type', pet.get('PetType', '')).lower() for pet in sample_pet_data]
        traits = []
        for pet in sample_pet_data:
            pet_traits = pet.get('traits', pet.get('PersonalityTraits', []))
            if isinstance(pet_traits, list):
                traits.extend(pet_traits)
            elif isinstance(pet_traits, str):
                traits.append(pet_traits)
        
        # Analyze order data for clues
        order_clues = []
        if data_type == "orders":
            for order in sample_order_data:
                item_type = order.get('item_type', '').lower()
                if item_type in ['toy', 'ball', 'frisbee']:
                    order_clues.append('active')
                elif item_type in ['bed', 'blanket', 'cushion']:
                    order_clues.append('chill')
                elif item_type in ['treat', 'food']:
                    order_clues.append('food_lover')
        
        # Simple rule-based badge assignment
        trait_text = ' '.join(traits).lower()
        clue_text = ' '.join(order_clues).lower()
        
        # Check for specific personality indicators
        if any(word in trait_text for word in ['protective', 'guard', 'watch', 'alert']):
            return "The Guardian"
        elif any(word in trait_text for word in ['playful', 'energetic', 'active', 'fast']) or 'active' in clue_text:
            return "The Athlete"
        elif any(word in trait_text for word in ['curious', 'explore', 'adventure', 'independent']):
            return "The Explorer"
        elif any(word in trait_text for word in ['affectionate', 'gentle', 'chill', 'snuggly']):
            return "The Cuddler"
        elif any(word in trait_text for word in ['clever', 'mischievous', 'trick', 'smart']):
            return "The Trickster"
        elif any(word in trait_text for word in ['quiet', 'observant', 'intelligent', 'puzzle']):
            return "The Scholar"
        elif any(word in trait_text for word in ['social', 'motherly', 'comforting', 'empathetic']):
            return "The Nurturer"
        elif any(word in trait_text for word in ['picky', 'confident', 'dramatic', 'stylish']):
            return "The Diva"
        elif any(word in trait_text for word in ['mellow', 'imaginative', 'slow', 'sensitive']):
            return "The Daydreamer"
        elif any(word in trait_text for word in ['shy', 'reserved', 'cautious', 'loyal']):
            return "The Shadow"
        
        # Default based on pet types
        if 'dog' in pet_types and 'cat' in pet_types:
            return "The Explorer"  # Mixed household tends to be more active
        elif 'dog' in pet_types:
            return "The Athlete"   # Dogs are often more energetic
        elif 'cat' in pet_types:
            return "The Scholar"   # Cats are often more observant
        else:
            return "The Explorer"  # Final fallback
    
    def _generate_household_description(self, badge: str, sample_pet_data: List[Dict[str, Any]]) -> str:
        """Generate a description for the household based on the badge and pets."""
        pet_names = [pet.get('name', 'Unknown') for pet in sample_pet_data]
        pet_types = [pet.get('type', pet.get('PetType', 'Unknown')).lower() for pet in sample_pet_data]
        
        descriptions = {
            "The Cuddler": "This household is filled with warmth and affection, creating a cozy haven of love and snuggles.",
            "The Explorer": "This household is filled with energy and curiosity, creating endless fun and adventure.",
            "The Guardian": "This household is protected by loyal companions who watch over their family with devotion.",
            "The Trickster": "This household is full of clever mischief and playful surprises around every corner.",
            "The Scholar": "This household is home to thoughtful observers who love to learn and discover.",
            "The Athlete": "This household is bursting with energy and drive, always ready for action and play.",
            "The Nurturer": "This household is filled with caring spirits who comfort and support everyone around them.",
            "The Diva": "This household has a flair for the dramatic and knows how to make every moment stylish.",
            "The Daydreamer": "This household moves at its own peaceful pace, finding beauty in quiet moments.",
            "The Shadow": "This household is home to gentle souls who show their love through quiet loyalty."
        }
        
        return descriptions.get(badge, "This household is filled with unique personalities that make every day special.")
    
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

We're so excited to tell you how much we love everything you've brought into our lives!"""
        
        # Add specific mentions based on data type
        if data_type == "reviews":
            # Analyze review data for positive mentions
            positive_products = []
            for review in sample_review_data:
                if review.get('rating', 0) >= 4 or 'love' in review.get('review_text', '').lower():
                    positive_products.append(review.get('product_name', review.get('product', '')))
            
            if positive_products:
                letter += f"We absolutely adore the {positive_products[0]} you've gotten for us! "
        
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
                    letter += f"We absolutely adore the {type_mentions[0]} you've spoiled us with! "
        
        letter += f""" Thank you for being the best human ever!

With all our love and zoomies,
{signature}"""
        
        # Generate visual prompt with enhanced pet information
        pet_descriptions = []
        for pet in sample_pet_data:
            name = pet.get('name', 'Unknown')
            pet_type = pet.get('type', pet.get('PetType', 'Unknown')).lower()
            
            # Build enhanced description with available traits
            description_parts = []
            
            if name.lower() == 'unknown':
                description_parts.append(f"a generic domestic {pet_type}")
            else:
                # Add breed if available and not unknown
                breed = pet.get('breed', pet.get('Breed'))
                if breed and breed.lower() not in ['unknown', 'unk']:
                    description_parts.append(f"a {breed} {pet_type}")
                else:
                    description_parts.append(f"a domestic {pet_type}")
        
                # Add size if available and not unknown
                size = pet.get('size', pet.get('SizeCategory'))
                if size and size.lower() not in ['unknown', 'unk']:
                    description_parts.append(f"{size.lower()}")
                
                # Add age/life stage if available and not unknown
                age = pet.get('age', pet.get('LifeStage'))
                if age and age.lower() not in ['unknown', 'unk']:
                    if age.lower() in ['p', 'puppy', 'kitten']:
                        description_parts.append("young")
                    elif age.lower() in ['s', 'senior']:
                        description_parts.append("senior")
                    elif age.lower() in ['a', 'adult']:
                        description_parts.append("adult")
                
                # Add weight if available and not unknown
                weight = pet.get('weight', pet.get('Weight'))
                if weight and weight.lower() not in ['unknown', 'unk']:
                    try:
                        weight_num = float(weight)
                        if weight_num < 10:
                            description_parts.append("small")
                        elif weight_num < 50:
                            description_parts.append("medium-sized")
                        else:
                            description_parts.append("large")
                    except (ValueError, TypeError):
                        pass
            
            # Join all parts to create the description
            pet_descriptions.append(' '.join(description_parts))
        
        # Ensure we have exactly the right number of pets
        pet_count = len(sample_pet_data)
        
        # Count pet types for explicit description
        dog_count = sum(1 for pet in sample_pet_data if pet.get('type', pet.get('PetType', '')).lower() == 'dog')
        cat_count = sum(1 for pet in sample_pet_data if pet.get('type', pet.get('PetType', '')).lower() == 'cat')
        
        # Create explicit pet type description
        if dog_count > 0 and cat_count > 0:
            pet_type_description = f"{dog_count} dog{'s' if dog_count > 1 else ''} and {cat_count} cat{'s' if cat_count > 1 else ''}"
        elif dog_count > 0:
            pet_type_description = f"{dog_count} dog{'s' if dog_count > 1 else ''}"
        elif cat_count > 0:
            pet_type_description = f"{cat_count} cat{'s' if cat_count > 1 else ''}"
        else:
            pet_type_description = f"{pet_count} pet{'s' if pet_count > 1 else ''}"
        
        visual_prompt = f"""In a bright, sunny, and cozy living room, {pet_type_description} ({', '.join(pet_descriptions)}) are enjoying their time together. The scene features EXACTLY {pet_count} pets as the main focus - no more, no less. The scene is filled with bright, warm lighting that illuminates everything clearly, with comfortable furniture. Chewy branding is subtly visible on a toy bin in the corner and a food bowl on the floor. The pets are surrounded by various beloved pet items including toys, food, and cozy accessories, creating a joyful and content atmosphere. The overall style is bright, warm, colorful, and full of pet-loving charm with vibrant, cheerful lighting."""
        
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
        
        # Determine household badge using the enhanced logic
        household_badge = self._determine_household_badge(sample_pet_data, sample_review_data, sample_order_data, data_type)
        household_description = self._generate_household_description(household_badge, sample_pet_data)
        
        # Get compatible badges
        compatible_badges = self.COMPATIBILITY_MAP.get(household_badge, ["The Explorer", "The Athlete", "The Cuddler"])
        
        # Create personality badge structure
        personality_badge = {
            "badge": household_badge,
            "compatible_with": compatible_badges,
            "icon_png": f"{household_badge.lower().replace(' ', '_')}.png",
            "description": household_description,
            "descriptive_words": self.badge_descriptive_words.get(household_badge, ["friendly", "gentle", "curious", "loving"])
        }
        
        return {
            "letter": letter,
            "visual_prompt": visual_prompt,
            "personality_badge": personality_badge
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