#!/usr/bin/env python3
"""
OpenAI-Powered Pet Letters Generator
Uses OpenAI API to generate completely unique letters for each pet
"""

import json
import requests
from typing import Dict, List, Any


def generate_letter_with_openai(pet_data: Dict[str, Any], api_key: str) -> str:
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

    # OpenAI API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "You are a creative writer who specializes in writing heartfelt letters from pets to their human companions. Make each letter unique, personal, and emotionally touching."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.8
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            letter = result["choices"][0]["message"]["content"].strip()
            return letter
        else:
            print(f"API Error: {response.status_code}")
            return generate_fallback_letter(pet_data)
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return generate_fallback_letter(pet_data)


def generate_fallback_letter(pet_data: Dict[str, Any]) -> str:
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


def generate_visual_prompt_for_pet(pet_data: Dict[str, Any]) -> str:
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