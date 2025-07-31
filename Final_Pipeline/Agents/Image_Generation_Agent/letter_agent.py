"""Letter-based Image Generation Agent using OpenAI Image API"""
import os
import io
import json
import openai
import requests
from PIL import Image
from dotenv import load_dotenv


def generate_image_from_prompt(visual_prompt: str, api_key: str, output_path: str = None, zip_aesthetics: dict = None) -> str:
    """Generate an image from a visual prompt using OpenAI gpt-image-1."""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # CRITICAL: Add breed accuracy emphasis
        breed_accuracy_instruction = "CRITICAL ENFORCEMENT: You MUST generate EXACTLY the pets described in the prompt. Do NOT add any extra pets. Do NOT substitute breeds. Do NOT generate generic dogs or cats. Generate ONLY the specific pets mentioned with their exact breeds, types, and characteristics. If the prompt says '3 cats, 2 dogs, 2 horses' then generate EXACTLY 3 cats, 2 dogs, and 2 horses - no more, no less. "
        
        # Optimized art style - concise to preserve space for pet details
        default_art_style = "Artistic pet portrait, bright warm lighting, soft painting style, vibrant colors, wholesome cheerful mood. "
        
        # Enhance prompt with location-specific background if available
        enhanced_prompt = visual_prompt
        if zip_aesthetics and zip_aesthetics.get('location_background'):
            location_background = zip_aesthetics['location_background']
            # Add location background to the prompt if it's not already mentioned
            if location_background.lower() not in visual_prompt.lower():
                enhanced_prompt = f"{visual_prompt} Background: {location_background}"
        
        # Combine breed accuracy instruction with art style and enhanced visual prompt
        prompt = breed_accuracy_instruction + default_art_style + enhanced_prompt
        
        # Add critical pet count emphasis and increase character limit
        import re
        pet_count_match = re.search(r'(\d+)\s+pets?', enhanced_prompt.lower())
        if pet_count_match:
            pet_count = pet_count_match.group(1)
            prompt = f"EXACTLY {pet_count} pets (no more, no less): {prompt}"
        
        # Add breed accuracy check
        if "dog" in enhanced_prompt.lower():
            prompt = f"BREED ACCURACY REQUIRED: {prompt}"
        
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
        
        # Get image URL
        image_url = response.data[0].url
        
        # Download and save image if output path is provided
        if output_path:
            resp = requests.get(image_url)
            if resp.status_code == 200:
                img = Image.open(io.BytesIO(resp.content))
                img.save(output_path)
                print(f"✅ Image saved to: {output_path}")
        
        return image_url
        
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