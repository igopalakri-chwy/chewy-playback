#!/usr/bin/env python3
"""Simple script to run the letter-based image generation agent"""

import sys
import os

# Add current directory to path
sys.path.append('.')

from src.letter_agent import main

if __name__ == "__main__":
    print("Starting Letter-based Image Generation Agent...")
    print("Using pet_letters.json")
    
    try:
        main('pet_letters.json')
        print("Letter-based image generation complete!")
        print("Check the 'output_images/' folder for your generated images")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your .env file has a valid OPENAI_API_KEY") 