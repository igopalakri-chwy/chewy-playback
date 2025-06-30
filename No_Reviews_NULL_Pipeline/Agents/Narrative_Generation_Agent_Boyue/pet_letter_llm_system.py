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
    
    def extract_data(self, pet_data: Dict[str, Any], review_data: Dict[str, Any]) -> tuple:
        """Extract sample_pet_data and sample_review_data from input files."""
        # Extract pet data list
        sample_pet_data = []
        if isinstance(pet_data, dict):
            for customer_id, pets in pet_data.items():
                if isinstance(pets, dict):
                    for pet_name, pet_info in pets.items():
                        if isinstance(pet_info, dict):
                            pet_info['name'] = pet_name
                            sample_pet_data.append(pet_info)
        
        # Extract review data list
        sample_review_data = []
        if isinstance(review_data, dict) and 'reviews' in review_data:
            sample_review_data = review_data['reviews']
        elif isinstance(review_data, list):
            sample_review_data = review_data
        
        return sample_pet_data, sample_review_data
    
    def generate_output(self, pet_data: Dict[str, Any], review_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a JSON object containing a playful letter and visual prompt.
        Uses LLM reasoning to interpret reviews and pet profiles.
        """
        # Extract data
        sample_pet_data, sample_review_data = self.extract_data(pet_data, review_data)
        
        # Prepare context for LLM
        context = self._prepare_context(sample_pet_data, sample_review_data)
        
        prompt = f"""You are an LLM that writes a JSON object containing:

1. A playful, personality-rich letter from the customer's pets.
2. A visual prompt describing an AI-generated, Chewy-branded artwork.

You are given:
- `sample_pet_data`: A list of pet dictionaries. Each has:
  - `name`: e.g., "Turbo", "unknown"
  - `type`: e.g., "cat", "dog"
  - optional `breed`, `traits`, `age`, `size`, or color-based traits

- `sample_review_data`: A list of product reviews. Each includes:
  - `product_name`
  - `review_text`
  - optional `rating`
  - optional `pet_name`

==== INSTRUCTIONS ====

STEP 1 — INTERPRET REVIEWS AND PET PROFILES:
- Use your reasoning skills to:
  1. Determine whether each review is **positive** based on tone and content.
     - Do not rely on rating alone.
     - Only use products that are clearly praised.
  2. Rewrite the product name in **natural, generic language** (e.g., "a super soft bed", "a twisty toy", "a festive light-up sweater").
     - Do not use the product name directly.

STEP 2 — GENERATE THE LETTER:
- Write a single letter from the perspective of the pets.
- If any pet is named `"unknown"`, sign the letter as: `"From: The {{number}} pets"`.
- Otherwise, sign off as: `"From: Turbo, Elwood, and Mochi"` (use commas and "and").
- The letter should:
  - Mention only the **positively reviewed** products using the LLM-generated natural description.
  - Express joy and personality using pet-like expressions (e.g., "zoomies of joy!", "snuggle squad reporting in!").
  - Avoid assigning products to specific pets unless the review clearly names a pet.
  - Reflect personality if traits are available.
  - Avoid marketing language or sounding like an ad.

STEP 3 — GENERATE THE VISUAL PROMPT:
- Describe a warm, playful, Chewy-branded scene featuring the pets.
- Only include the positively reviewed products, described naturally.
- If any pet is `"unknown"`:
  - Include a **generic** version of its `type` (e.g., "a generic domestic cat").
- If a pet has known physical traits (breed, size, age, color):
  - Include those in the visual description.
- Do NOT make up any physical characteristics that are not explicitly given.
- Include **Chewy branding subtly** — e.g., on a toy bin, food bowl, scarf label, or poster.

==== OUTPUT FORMAT ====
Return a single JSON object like this:
{{
  "letter": "<generated letter text>",
  "visual_prompt": "<generated AI visual prompt>"
}}

Only return this JSON. Do not include explanations, extra commentary, or metadata.

=== INPUT DATA ===
{context}

Generate the JSON object:"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative pet letter and visual prompt generator. Generate playful, personality-rich content from pets' perspectives."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
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
                return self._generate_fallback_output(sample_pet_data, sample_review_data)
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self._generate_fallback_output(sample_pet_data, sample_review_data)
    
    def _prepare_context(self, sample_pet_data: List[Dict[str, Any]], sample_review_data: List[Dict[str, Any]]) -> str:
        """Prepare context for LLM generation."""
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
    
    def _generate_fallback_output(self, sample_pet_data: List[Dict[str, Any]], sample_review_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate fallback output when LLM fails."""
        # Determine signature
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
        
        # Generate simple letter
        letter = f"""Dear Human,

We hope this letter finds you well and ready for some serious cuddle time! We've been having the most amazing zoomies of joy with all the incredible things you've brought into our lives, and we just had to write to tell you how much we love everything!

The toys you've spoiled us with are absolutely paw-some! We can't get enough of chasing them around and playing together. It's like you've brought the thrill of the hunt right into our cozy home, and our tails haven't stopped wagging (or swishing, depending on who you ask)!

And then there's the food situation - oh my whiskers! You've been feeding us like royalty, and we're not complaining one bit. Every meal is like a gourmet feast, and we can't help but do our happy dance when you reach for the treat jar.

The cozy things you've given us - whether it's soft beds, warm sweaters, or comfy spots - have made our home the most snuggle-approved place ever. We feel so loved and cared for, and we want you to know that we appreciate every little thing you do for us.

We may not always show it in the most obvious ways (we are pets, after all), but you've filled our lives with so much joy, comfort, and endless belly rubs. You always know exactly what we need to be happy, healthy, and entertained.

So from the bottom of our furry hearts, thank you for being the best human ever! We're so lucky to have you, and we promise to keep being the most loving, playful, and grateful pets you could ask for.

With all our love and zoomies,
{signature}

P.S. Can we have an extra treat for being such good pets? Pretty please with a paw on top!"""
        
        # Generate simple visual prompt
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
        
        return {
            "letter": letter,
            "visual_prompt": visual_prompt
        }


def main():
    """Main function with argument handling."""
    parser = argparse.ArgumentParser(description='Pet Letter & Visual Prompt Generator')
    parser.add_argument('--pet-data', '-p', required=True, help='JSON file containing pet data')
    parser.add_argument('--review-data', '-r', required=True, help='JSON file containing review data')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        system = PetLetterLLMSystem(openai_api_key=args.api_key)
        
        # Load data
        pet_data = system.load_json_file(args.pet_data)
        review_data = system.load_json_file(args.review_data)
        
        # Generate output
        result = system.generate_output(pet_data, review_data)
        
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