"""Letter-based Image Generation Agent using OpenAI Image API"""
import os
import io
import json
import openai
import requests
from PIL import Image
from dotenv import load_dotenv


def generate_image_from_prompt(visual_prompt: str, api_key: str, output_path: str = None) -> str:
    """Generate an image from a visual prompt using OpenAI gpt-image-1."""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Art style prompt to ensure consistency
        art_style = "Soft, blended brushstrokes that mimic traditional oil or gouache painting. Warm, glowing lighting with gentle ambient highlights and diffuse shadows. Vivid yet harmonious color palette, featuring saturated pastels and rich warm tones. Subtle texture that gives a hand-painted, storybook feel. Sparkle accents and light flares to add magical charm. Smooth gradients and soft edges, avoiding harsh lines or stark contrast. A dreamy, nostalgic tone evocative of classic children's book illustrations. "
        
        # Combine art style with visual prompt
        prompt = art_style + visual_prompt
        
        # Truncate prompt to fit OpenAI's 1000 character limit
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."
        
        # Add timestamp to ensure unique generation
        import time
        timestamp = int(time.time())
        unique_prompt = f"{prompt} [Generated at {timestamp}]"
        
        response = client.images.generate(
            model="gpt-image-1",
            prompt=unique_prompt,
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