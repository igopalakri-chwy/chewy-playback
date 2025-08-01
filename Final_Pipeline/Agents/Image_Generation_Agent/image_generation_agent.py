"""Letter-based Image Generation Agent using OpenAI Image API"""
import os
import io
import json
import openai
import requests
from PIL import Image
from dotenv import load_dotenv


def generate_image_from_prompt(visual_prompt: str = None, api_key: str = None, output_path: str = None, zip_aesthetics: dict = None, pet_details: list = None) -> str:
    """Generate an image from a visual prompt using OpenAI gpt-image-1."""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Start with the visual prompt and add consistent art style
        prompt = visual_prompt or ""
        
        # Add consistent art style to every image
        art_style = " Sophisticated artistic pet portrait, wholesome and warm, joyous energy, refined illustration style, pets as the main focus, inviting atmosphere, elegant colors, cozy and cheerful mood, bright and well-lit with vibrant lighting, NOT cartoonish, artistic interpretation"
        prompt += art_style
        
        # Add essential pet accuracy instructions (only if pet_details provided)
        if pet_details:
            total_pets = len(pet_details)
            pet_summary = []
            for pet in pet_details:
                pet_type = pet['type'].lower()
                breed = pet['breed'] if pet['breed'] and pet['breed'].lower() not in ['unknown', 'unk', 'other'] else 'domestic'
                name = pet['name']
                pet_summary.append(f"{name} the {breed} {pet_type}")
            
            # Add concise accuracy instructions
            accuracy_note = f" IMPORTANT: Show exactly {total_pets} pets total: {', '.join(pet_summary)}. NO TEXT in image."
            prompt += accuracy_note
        
        # Add location context if available
        if zip_aesthetics and zip_aesthetics.get('location_background'):
            prompt += f" Setting: {zip_aesthetics['location_background']}."
        
        # Ensure prompt stays within reasonable limits
        if len(prompt) > 1500:
            prompt = prompt[:1497] + "..."
        
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1536",
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