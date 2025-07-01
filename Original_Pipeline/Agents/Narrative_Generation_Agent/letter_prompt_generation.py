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
- Keep it between 100-200 words
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
        "max_tokens": 300,
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


def generate_collective_letter_with_openai(all_pets_data: Dict[str, Dict[str, Any]], api_key: str) -> str:
    """Generate a collective letter from all pets to their human owner."""
    
    # Filter out pets with UNK names or treat them differently
    known_pets_info = []
    unknown_pets_count = 0
    
    for pet_name, pet_data in all_pets_data.items():
        # Skip pets with UNK names or treat them as additional family members
        if pet_name.upper() in ['UNK', 'UNKNOWN', 'UNNAMED'] or pet_data.get("PetType") == "UNK":
            unknown_pets_count += 1
            continue
        
        pet_info = {
            "name": pet_name,
            "pet_type": pet_data.get("PetType", "Pet"),
            "breed": pet_data.get("Breed", "beautiful"),
            "personality_traits": pet_data.get("PersonalityTraits", []),
            "favorite_products": pet_data.get("MostOrderedProducts", []),
            "behavioral_cues": pet_data.get("BehavioralCues", []),
            "health_mentions": pet_data.get("HealthMentions", []),
            "dietary_prefs": pet_data.get("DietaryPreferences", []),
            "life_stage": pet_data.get("LifeStage", "adult"),
            "gender": pet_data.get("Gender", ""),
            "size_category": pet_data.get("SizeCategory", "medium"),
            "weight": pet_data.get("Weight", "")
        }
        known_pets_info.append(pet_info)
    
    # If no known pets, use fallback
    if not known_pets_info:
        return generate_collective_fallback_letter(all_pets_data)
    
    # Create a detailed prompt for the collective letter
    pets_description = ""
    for i, pet in enumerate(known_pets_info):
        pets_description += f"""
Pet {i+1} - {pet['name']}:
- Type: {pet['pet_type']}
- Breed: {pet['breed']}
- Life Stage: {pet['life_stage']}
- Gender: {pet['gender']}
- Size: {pet['size_category']}
- Weight: {pet['weight']}
- Personality Traits: {', '.join(pet['personality_traits'])}
- Favorite Products: {', '.join(pet['favorite_products'][:3])}  # Limit to top 3
- Behavioral Cues: {', '.join(pet['behavioral_cues'])}
- Health Mentions: {', '.join(pet['health_mentions'])}
- Dietary Preferences: {', '.join(pet['dietary_prefs'][:3])}  # Limit to top 3
"""
    
    # Get unique characteristics across all known pets
    all_personality_traits = []
    all_favorite_products = []
    all_behavioral_cues = []
    all_health_mentions = []
    all_dietary_prefs = []
    
    for pet in known_pets_info:
        all_personality_traits.extend(pet['personality_traits'])
        all_favorite_products.extend(pet['favorite_products'])
        all_behavioral_cues.extend(pet['behavioral_cues'])
        all_health_mentions.extend(pet['health_mentions'])
        all_dietary_prefs.extend(pet['dietary_prefs'])
    
    # Remove duplicates and limit
    unique_traits = list(set(all_personality_traits))[:5]
    unique_products = list(set(all_favorite_products))[:5]
    unique_behaviors = list(set(all_behavioral_cues))[:3]
    unique_health = list(set(all_health_mentions))[:3]
    unique_dietary = list(set(all_dietary_prefs))[:5]
    
    pet_names = [pet['name'] for pet in known_pets_info]
    
    # Handle different numbers of pets
    if len(pet_names) == 1:
        pet_names_str = pet_names[0]
        family_context = f"just {pet_names[0]}"
    elif len(pet_names) == 2:
        pet_names_str = f"{pet_names[0]} and {pet_names[1]}"
        family_context = f"{pet_names[0]} and {pet_names[1]}"
    else:
        pet_names_str = ", ".join(pet_names[:-1]) + f" and {pet_names[-1]}"
        family_context = f"our little family of {len(pet_names)} pets"
    
    # Add context about additional family members if there are unknown pets
    additional_context = ""
    if unknown_pets_count > 0:
        if unknown_pets_count == 1:
            additional_context = f" (plus one more furry family member who prefers to stay mysterious)"
        else:
            additional_context = f" (plus {unknown_pets_count} more furry family members who prefer to stay mysterious)"
    
    prompt = f"""Write a completely unique, heartfelt collective letter from all pets to their human owner.

Pet Details:
{pets_description}

Collective Family Characteristics:
- Known Pets: {pet_names_str}
- Additional Family Members: {additional_context}
- Combined Personality Traits: {', '.join(unique_traits)}
- Shared Favorite Products: {', '.join(unique_products)}
- Family Behavioral Patterns: {', '.join(unique_behaviors)}
- Family Health Focus: {', '.join(unique_health)}
- Family Dietary Preferences: {', '.join(unique_dietary)}

Requirements:
- Start with "Human" instead of "Dear Human" - make it casual and funny
- Write as if all pets are collaborating on one letter together
- Mention each known pet by name and their unique contributions to the family
- If there are additional family members, refer to them indirectly (e.g., "our other furry friends", "the rest of our family") but NEVER mention "UNK", "unknown", or "mystery pet"
- Make it completely unique and different from any template
- Include specific details about their collective personality, products, and behaviors
- Make it emotional, heartfelt, and personal
- Use the pets' actual names and characteristics
- Make it whimsical and delightful
- Include signatures from all known pets
- Keep it between 150-250 words
- Make it feel like a real collaborative letter from all pets to their human
- Show how the pets work together as a family unit
- If there are additional pets, mention them as part of the family without naming them specifically

Write the collective letter:"""

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
                "content": "You are a creative writer who specializes in writing heartfelt collective letters from multiple pets to their human companions. Make each letter unique, personal, and emotionally touching, showing how pets collaborate as a family. Never mention 'UNK', 'unknown', or 'mystery pet' - instead refer to additional pets indirectly as family members."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 400,
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
            return generate_collective_fallback_letter(all_pets_data)
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return generate_collective_fallback_letter(all_pets_data)


def generate_collective_fallback_letter(all_pets_data: Dict[str, Dict[str, Any]]) -> str:
    """Generate a fallback collective letter if API fails."""
    
    # Filter out pets with UNK names
    known_pet_names = []
    unknown_pets_count = 0
    
    for pet_name, pet_data in all_pets_data.items():
        if pet_name.upper() in ['UNK', 'UNKNOWN', 'UNNAMED'] or pet_data.get("PetType") == "UNK":
            unknown_pets_count += 1
            continue
        known_pet_names.append(pet_name)
    
    # Handle different scenarios
    if not known_pet_names:
        # If no known pets, create a generic family letter
        return f"""Human,

We just had to write you this letter together to tell you how much you mean to all of us! We're your furry family, and we're so grateful for everything you do for us.

Every day with you is a gift. Whether we're playing with our favorite things, going on adventures, or just spending quiet time together, we're reminded of how lucky we are to have you as our human.

We know we can each be a bit unique sometimes - each in our own special way - but you always understand and love us for who we are. Your patience and understanding mean the world to all of us.

Thank you for always looking out for our health and making sure we have the best care. Your attention to our needs shows us how much you love each and every one of us.

You've given us the most wonderful life filled with love, joy, and endless adventures. We promise to love you unconditionally, be your faithful companions, and bring happiness to your life every single day.

With all our love and gratitude,
Your Furry Family ❤️

P.S. We can't wait for our next adventure together!"""
    
    # Create pet names string
    if len(known_pet_names) == 1:
        pet_names_str = known_pet_names[0]
        family_reference = f"{known_pet_names[0]} and the rest of our family"
    elif len(known_pet_names) == 2:
        pet_names_str = f"{known_pet_names[0]} and {known_pet_names[1]}"
        family_reference = f"{known_pet_names[0]}, {known_pet_names[1]}, and our other furry friends"
    else:
        pet_names_str = ", ".join(known_pet_names[:-1]) + f" and {known_pet_names[-1]}"
        family_reference = f"{pet_names_str} and the rest of our family"
    
    # Get some sample data from the first known pet
    first_pet = next(pet_data for pet_name, pet_data in all_pets_data.items() 
                    if pet_name.upper() not in ['UNK', 'UNKNOWN', 'UNNAMED'])
    favorite_products = first_pet.get("MostOrderedProducts", [])
    personality_traits = first_pet.get("PersonalityTraits", [])
    
    # Add context about additional family members
    additional_context = ""
    if unknown_pets_count > 0:
        if unknown_pets_count == 1:
            additional_context = " (along with one more furry family member who prefers to stay mysterious)"
        else:
            additional_context = f" (along with {unknown_pets_count} more furry family members who prefer to stay mysterious)"
    
    return f"""Human,

We just had to write you this letter together to tell you how much you mean to all of us! We're {pet_names_str}{additional_context}, and we're so grateful for everything you do for our little family.

Every day with you is a gift. Whether we're playing with our {favorite_products[0].lower() if favorite_products else 'favorite things'}, going on adventures, or just spending quiet time together, we're reminded of how lucky we are to have you as our human.

We know we can be a bit {personality_traits[0].lower() if personality_traits else 'unique'} sometimes - each in our own special way - but you always understand and love us for who we are. Your patience and understanding mean the world to all of us.

Thank you for always looking out for our health and making sure we have the best care. Your attention to our needs shows us how much you love each and every one of us.

You've given us the most wonderful life filled with love, joy, and endless adventures. We promise to love you unconditionally, be your faithful companions, and bring happiness to your life every single day.

With all our love and gratitude,
{family_reference} ❤️

P.S. We can't wait for our next adventure together!""" 


def generate_collective_visual_prompt(all_pets_data: Dict[str, Dict[str, Any]]) -> str:
    """Generate a collective visual prompt for all pets in a customer's household."""
    
    # Filter out pets with UNK names
    known_pets = []
    for pet_name, pet_data in all_pets_data.items():
        if pet_name.upper() not in ['UNK', 'UNKNOWN', 'UNNAMED'] and pet_data.get("PetType") != "UNK":
            known_pets.append((pet_name, pet_data))
    
    if not known_pets:
        # Fallback if no known pets
        return """A heartwarming family portrait featuring multiple pets in a cozy, loving home environment. The image shows pets of various types gathered together in a warm, inviting setting with soft lighting and comfortable surroundings. The background features gentle, dreamy colors with floating hearts and warm patterns. The style should be cute, shareable digital art with a wholesome, family-friendly aesthetic perfect for social media. The image should radiate happiness and unconditional love, with bright, cheerful lighting. IMPORTANT: The Chewy logo must be prominently displayed at the bottom center of the image in clear, readable text with warm, friendly colors, perfect for Chewy's brand of caring for pets and their families."""
    
    # Build collective description
    pet_descriptions = []
    pet_types = set()
    personality_traits = set()
    favorite_products = set()
    
    for pet_name, pet_data in known_pets:
        pet_type = pet_data.get("PetType", "Pet")
        breed = pet_data.get("Breed", "beautiful")
        size_category = pet_data.get("SizeCategory", "medium")
        weight = pet_data.get("Weight", "")
        life_stage = pet_data.get("LifeStage", "adult")
        gender = pet_data.get("Gender", "")
        
        pet_types.add(pet_type.lower())
        
        # Collect personality traits
        traits = pet_data.get("PersonalityTraits", [])
        personality_traits.update([trait.lower() for trait in traits])
        
        # Collect favorite products
        products = pet_data.get("MostOrderedProducts", [])
        favorite_products.update([product.lower() for product in products[:2]])
        
        # Create individual pet description
        pet_desc = f"{pet_name}, a {size_category} {breed.lower()} {pet_type.lower()}"
        if weight:
            pet_desc += f" weighing {weight}"
        if life_stage != "adult":
            pet_desc += f" ({life_stage})"
        if gender:
            pet_desc += f" ({gender})"
        
        pet_descriptions.append(pet_desc)
    
    # Create collective personality description
    personality_desc = ""
    if "playful" in personality_traits:
        personality_desc += "playful and energetic, "
    if "affectionate" in personality_traits:
        personality_desc += "loving and affectionate, "
    if "curious" in personality_traits:
        personality_desc += "curious and inquisitive, "
    if "loyal" in personality_traits:
        personality_desc += "loyal and devoted, "
    if "social" in personality_traits:
        personality_desc += "friendly and social, "
    
    if not personality_desc:
        personality_desc = "charming and endearing, "
    
    # Create environment based on pet types
    if len(pet_types) == 1:
        if "dog" in pet_types:
            environment = "in a whimsical, cozy home setting with soft cushions, warm lighting, and playful dog toys"
        elif "cat" in pet_types:
            environment = "in a magical, sunlit room with comfortable perches, floating cat toys, and cozy napping spots"
        else:
            environment = "in a charming, loving home environment with comfortable spaces and artistic details"
    else:
        # Mixed pets
        environment = "in a harmonious, multi-pet household with cozy spaces for different types of pets, warm lighting, and shared play areas"
    
    # Add favorite items
    favorite_items = ""
    if favorite_products:
        items = list(favorite_products)[:3]  # Limit to 3 items
        favorite_items = f", surrounded by their beloved {', '.join(items)} in cute packaging"
    
    # Build the collective prompt
    pets_list = ", ".join(pet_descriptions)
    
    prompt = f"""A delightful, artistic family portrait featuring {pets_list} gathered together {personality_desc}in a heartwarming scene. The pets are shown {environment}{favorite_items}, interacting with each other in a loving, harmonious way. Each pet maintains their unique characteristics while creating a beautiful, unified family moment. The background features soft, dreamy colors with gentle patterns, floating hearts, and warm, inviting lighting. The image should radiate happiness, unconditional love, and the joy of having multiple pets in a family. The style should be cute, shareable digital art with a wholesome, family-friendly aesthetic perfect for social media. The image should be heartwarming and adorable, with a warm color palette that makes people want to share it. IMPORTANT: The Chewy logo must be prominently displayed at the bottom center of the image in clear, readable text with warm, friendly colors, perfect for Chewy's brand of caring for pets and their families."""
    
    return prompt 