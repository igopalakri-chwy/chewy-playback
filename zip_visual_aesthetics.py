#!/usr/bin/env python3
"""
ZIP Code Visual Aesthetics Generator
Uses OpenAI API to generate visual aesthetics for a given U.S. ZIP code.
"""

import os
import sys
import openai
from typing import Dict, Optional
from dotenv import load_dotenv


class ZIPVisualAestheticsGenerator:
    """Generates visual aesthetics for U.S. ZIP codes using OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generator with OpenAI API key."""
        load_dotenv()
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_aesthetics(self, zip_code: str) -> Dict[str, str]:
        """
        Generate visual aesthetics for a given ZIP code.
        
        Args:
            zip_code: U.S. ZIP code as a string
            
        Returns:
            Dictionary with visual_style, color_texture, and art_style
        """
        try:
            # Create the prompt
            prompt = f"""Given the ZIP code {zip_code}, provide the following:
visual_style (3–5 words), color_texture (3–5 words), and art_style (3–5 words). Output only in this format:
visual_style = "..."
color_texture = "..."
art_style = "..."
"""
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in visual aesthetics and regional design. Analyze ZIP codes to determine the visual characteristics of the area."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            # Extract the response content
            result = response.choices[0].message.content.strip()
            
            # Parse the response
            aesthetics = self._parse_response(result)
            
            # Print the results in the expected format
            print(f'visual_style = "{aesthetics["visual_style"]}"')
            print(f'color_texture = "{aesthetics["color_texture"]}"')
            print(f'art_style = "{aesthetics["art_style"]}"')
            
            return aesthetics
            
        except openai.APIError as e:
            print(f"❌ OpenAI API Error: {e}")
            return self._get_fallback_aesthetics()
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return self._get_fallback_aesthetics()
    
    def _parse_response(self, response: str) -> Dict[str, str]:
        """Parse the OpenAI response to extract the three aesthetics components."""
        try:
            lines = response.strip().split('\n')
            aesthetics = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('visual_style = '):
                    aesthetics['visual_style'] = self._extract_quoted_value(line)
                elif line.startswith('color_texture = '):
                    aesthetics['color_texture'] = self._extract_quoted_value(line)
                elif line.startswith('art_style = '):
                    aesthetics['art_style'] = self._extract_quoted_value(line)
            
            # Ensure all required fields are present
            required_fields = ['visual_style', 'color_texture', 'art_style']
            for field in required_fields:
                if field not in aesthetics or not aesthetics[field]:
                    aesthetics[field] = self._get_fallback_aesthetics()[field]
            
            return aesthetics
            
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return self._get_fallback_aesthetics()
    
    def _extract_quoted_value(self, line: str) -> str:
        """Extract the quoted value from a line like 'visual_style = "urban modern"."""
        try:
            # Find the first quote and last quote
            start_quote = line.find('"')
            end_quote = line.rfind('"')
            
            if start_quote != -1 and end_quote != -1 and start_quote < end_quote:
                return line[start_quote + 1:end_quote]
            else:
                # Fallback: try to extract after equals sign
                if '=' in line:
                    return line.split('=', 1)[1].strip().strip('"')
                else:
                    return "modern clean"
        except Exception:
            return "modern clean"
    
    def _get_fallback_aesthetics(self) -> Dict[str, str]:
        """Return fallback aesthetics when API fails."""
        return {
            "visual_style": "modern clean",
            "color_texture": "smooth neutral",
            "art_style": "contemporary minimal"
        }


def main():
    """Main function to run the ZIP visual aesthetics generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visual aesthetics for a U.S. ZIP code")
    parser.add_argument("zip_code", help="U.S. ZIP code to analyze")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use environment variable)")
    
    args = parser.parse_args()
    
    try:
        # Validate ZIP code format (basic check)
        zip_code = args.zip_code.strip()
        if not zip_code.isdigit() or len(zip_code) != 5:
            print("❌ Error: ZIP code must be a 5-digit number")
            sys.exit(1)
        
        # Initialize generator
        generator = ZIPVisualAestheticsGenerator(api_key=args.api_key)
        
        # Generate aesthetics
        aesthetics = generator.generate_aesthetics(zip_code)
        
        # The results are already printed in the expected format
        # Return the aesthetics dictionary for potential further use
        return aesthetics
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 