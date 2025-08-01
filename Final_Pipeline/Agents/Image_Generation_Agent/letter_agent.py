"""Letter-based Image Generation Agent using OpenAI Image API"""
import os
import io
import json
import openai
import requests
from PIL import Image
from dotenv import load_dotenv


def generate_image_from_prompt(visual_prompt: str, api_key: str, output_path: str = None, zip_aesthetics: dict = None, pet_details: list = None) -> str:
    """Generate an image from a visual prompt using OpenAI gpt-image-1."""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Build hyper-specific instructions based on actual pet data
        specific_instructions = []
        
        if pet_details:
            # Count pets by type for exact specification
            pet_counts = {}
            breed_list = []
            
            for pet in pet_details:
                pet_type = pet['type'].lower()
                breed = pet['breed']
                
                # Count pet types
                pet_counts[pet_type] = pet_counts.get(pet_type, 0) + 1
                
                # Collect breed and characteristic info
                if breed and breed.lower() not in ['unknown', 'unk', 'other']:
                    breed_list.append(f"{breed} {pet_type}")
                else:
                    breed_list.append(f"domestic {pet_type}")
            
            # Build exact count instruction
            total_pets = sum(pet_counts.values())
            count_details = []
            for pet_type, count in pet_counts.items():
                count_details.append(f"{count} {pet_type}{'s' if count > 1 else ''}")
            
            specific_instructions.append(f"GENERATE EXACTLY {total_pets} PETS: {', '.join(count_details)}.")
            specific_instructions.append(f"EXACT BREEDS REQUIRED: {', '.join(breed_list)}.")
            
            # Add dynamic breed substitution warnings for any specific breeds
            specific_breeds = [breed for breed in breed_list if not breed.startswith('domestic')]
            if specific_breeds:
                specific_instructions.append(f"DO NOT substitute these breeds with generic alternatives: {', '.join(specific_breeds)}.")
        
        # ZIP code location accuracy
        location_instruction = ""
        if zip_aesthetics and zip_aesthetics.get('location_background'):
            location_instruction = f"LOCATION: {zip_aesthetics['location_background']}. "
        
        # Art style (consistent every time)
        default_art_style = "Sophisticated artistic pet portrait, wholesome and warm, joyous energy, refined illustration style, pets as the main focus, inviting atmosphere, elegant colors, cozy and cheerful mood, bright and well-lit with vibrant lighting, NOT cartoonish, artistic interpretation"
        
        # Build final prompt: Specific Instructions + Art Style + Location + Visual Prompt
        prompt_parts = []
        if specific_instructions:
            prompt_parts.append(' '.join(specific_instructions))
        prompt_parts.append(default_art_style)
        if location_instruction:
            prompt_parts.append(location_instruction)
        prompt_parts.append(visual_prompt)
        
        prompt = ' '.join(prompt_parts)
        
        # Increase character limit to preserve pet details
        if len(prompt) > 1500:
            prompt = prompt[:1497] + "..."
        
        # Add timestamp to ensure unique generation
        import time
        timestamp = int(time.time())
        unique_prompt = f"{prompt} [Generated at {timestamp}]"
        
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        
        # Handle both URL and base64 responses
        image_data = response.data[0]
        if hasattr(image_data, 'url') and image_data.url:
            # URL response
            image_url = image_data.url
            
            # Download and save image if output path is provided
            if output_path:
                resp = requests.get(image_url)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    img.save(output_path)
                    print(f"✅ Image saved to: {output_path}")
            
            return image_url
        elif hasattr(image_data, 'b64_json') and image_data.b64_json:
            # Base64 response - save directly if output path provided
            if output_path:
                import base64
                image_bytes = base64.b64decode(image_data.b64_json)
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                print(f"✅ Image saved to: {output_path}")
            
            # Return the base64 data for pipeline processing
            return image_data.b64_json
        else:
            print(f"❌ No image data found in response")
            return None
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        return None


def generate_images_for_customer(customer_data: dict, api_key: str, output_dir: str) -> dict:
    """Generate images for all pets in a customer's data."""
    
    os.makedirs(output_dir, exist_ok=True)
    image_results = {}
    
    for pet_name, visual_prompt in customer_data.get('visual_prompts', {}).items():
        if visual_prompt:
            output_path = os.path.join(output_dir, f"{pet_name}_portrait.png")
            image_url = generate_image_from_prompt(visual_prompt, api_key, output_path)
            image_results[pet_name] = image_url
        else:
            image_results[pet_name] = None
    
    return image_results


def main(letters_path: str, output_dir: str = 'output_images'):
    """Main function to generate images from pet letters data."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize OpenAI client with API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment")
        print("Please check your .env file")
        return
    
    # Load the pet letters data
    try:
        with open(letters_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {letters_path} not found")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {letters_path}")
        return
    
    os.makedirs(output_dir, exist_ok=True)

    for customer_id, customer_data in data.items():
        # Extract the visual prompts for this customer
        visual_prompts = customer_data.get('visual_prompts', {})
        
        if not visual_prompts:
            print(f"No visual prompts found for {customer_id}")
            continue
            
        print(f"Generating images for {customer_id}...")
        
        # Generate images for each pet
        for pet_name, visual_prompt in visual_prompts.items():
            if visual_prompt:
                output_path = os.path.join(output_dir, f"{customer_id}_{pet_name}_portrait.png")
                image_url = generate_image_from_prompt(visual_prompt, api_key, output_path)
                
                if image_url:
                    print(f"✅ Generated image for {pet_name}")
                else:
                    print(f"❌ Failed to generate image for {pet_name}")


if __name__ == "__main__":
    main('pet_letters.json') 