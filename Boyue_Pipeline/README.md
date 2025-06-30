# Boyue Pipeline - Enhanced Narrative Generation

## Overview
This pipeline uses the original Review and Order Intelligence Agent but replaces the Narrative Generation Agent with Boyue's enhanced version that generates collective letters and visual prompts.

## Architecture
The pipeline consists of three main agents:

1. **Review and Order Intelligence Agent** - Analyzes order history and review data to create enriched pet profiles
2. **Boyue Narrative Generation Agent** - Generates collective letters from all pets and visual prompts
3. **Image Generation Agent** - Creates AI-generated images based on the collective visual prompt

## Key Differences from Original Pipeline
- **Collective Letters**: All pets write one letter together instead of individual letters
- **Enhanced Visual Prompts**: Boyue's agent generates detailed visual prompts for image generation
- **Review Integration**: Uses actual customer reviews to mention specific products in letters
- **Unknown Pet Handling**: Gracefully handles pets with "UNK" names in collective letters

## Data Requirements
- `Data/order_history.csv` - Customer order history
- `Data/qualifying_reviews.csv` - Customer review data with pet information

## Features
- ✅ Enriched pet profiles with confidence scores
- ✅ Collective letters from all pets
- ✅ Enhanced visual prompts for image generation
- ✅ Single AI-generated image per customer
- ✅ Review-based product mentions in letters

## Usage

### Run for a specific customer:
```bash
python run_pipeline_boyue_for_customer.py
```

### Run for multiple customers:
```bash
python run_pipeline_boyue_for_multiple_customers.py
```

## Output Structure
```
Output_Boyue/
├── 1183376/
│   ├── enriched_pet_profile.json
│   ├── pet_letters.txt
│   ├── visual_prompt.txt
│   └── images/
│       └── collective_image.png
└── 1154095/
    ├── enriched_pet_profile.json
    ├── pet_letters.txt
    ├── visual_prompt.txt
    └── images/
        └── collective_image.png
```

## Key Features
- **Collective Narrative**: All pets contribute to one letter
- **Visual Prompt Generation**: Detailed prompts for AI image generation
- **Review-Based Content**: Letters mention specific products from reviews
- **Chewy Branding**: Visual prompts include Chewy branding elements
- **Unknown Pet Integration**: Unknown pets are referenced as "other furry family members"

## Boyue Agent Capabilities
- **LLM-Powered Analysis**: Uses GPT-4 to analyze reviews and pet profiles
- **Natural Language Generation**: Creates natural, conversational letters
- **Product Integration**: Mentions specific products customers loved
- **Personality Reflection**: Incorporates pet personality traits
- **Fallback Generation**: Provides fallback content if LLM fails

## Dependencies
- OpenAI API key required
- Python packages: pandas, openai, requests, pathlib

## Configuration
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Example Output
The Boyue agent generates letters like:
```
Hello there, fuzzy friend! This is Turbo, Elwood, and our mysterious buddy, 
reporting in from our comfy kitty corner. We've been having the time of our 
nine lives with the delightful goodies you've sent us...
```

And visual prompts like:
```
Envision a warm, cozy room with playful Chewy-branded elements. Turbo, a 
Himalayan cat, and Elwood, a Birman, are clad in well-made holiday sweaters...
``` 