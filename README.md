# Chewy Playback Pipeline (Final Unified Version)

This repository contains the **Final_Pipeline**, the unified and most advanced version of the Chewy Playback system. All legacy and experimental scripts have been removed for clarity and maintainability.

## Overview

The Final Pipeline automatically generates personalized pet content for Chewy customers by:
- Analyzing order and review data
- Building detailed pet profiles
- Generating playful, personality-rich letters from the pets
- Creating DALL-E 3-optimized visual prompts
- Assigning a household personality badge (with icon)
- Generating collective pet portraits using AI
- **ZIP Aesthetics**: Tailors visual and narrative style based on the customer's ZIP code
- **Unknowns analyzer**: Identifies missing pet attributes

## Key Features
- **Automatic agent selection**: Uses review data if available, otherwise falls back to order-only analysis
- **Unified narrative generation**: Short, collective letters and visual prompts for all pets
- **ZIP-based personalization**: Visual and narrative style adapts to the customer's region
- **Personality badge assignment**: Household badge with compatible types and icon
- **Confidence scoring**: For each pet and customer
- **Unknowns analysis**: Identifies missing pet attributes and creates customer-specific reports
- **Robust error handling**: Graceful fallbacks and detailed logging

## Directory Structure

```
chewy-playback/
├── Final_Pipeline/
│   ├── chewy_playback_pipeline.py      # Main unified pipeline (entry point)
│   ├── Agents/                        # Agent modules
│   ├── Data/                          # Input data (order_history.csv, qualifying_reviews.csv)
│   └── Output/                        # Results for each customer
├── zip_visual_aesthetics.py           # Standalone ZIP aesthetics generator
├── ZIP_AESTHETICS_README.md           # ZIP aesthetics documentation
├── requirements.txt                   # Dependencies
├── README.md                          # This file
├── .gitignore
├── venv/                              # (optional) Python virtual environment
├── Merge_Mobile_V1/                   # (optional) Legacy/experimental mobile code
├── FrontEnd_Mobile/                   # Badge images and frontend assets
└── Detailed Chewy Wrapped Architecture.pdf
```

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Place your data files in `Final_Pipeline/Data/`:**
- `order_history.csv`
- `qualifying_reviews.csv`

4. **Run the pipeline from the `Final_Pipeline` directory:**
```bash
cd Final_Pipeline
python chewy_playback_pipeline.py --customers 1183376 1317924 2209529
```
- Omit `--customers` to process all customers.

## ZIP Aesthetics Feature
- The pipeline uses the customer's ZIP code (from order data) to generate:
  - Regional visual style, color/texture, art style, and tone
  - Personalized narrative and visual prompts
  - More relevant and engaging outputs for each customer
- ZIP aesthetics are saved as `zip_aesthetics.json` in each customer's output folder.

## Output
For each customer, the pipeline generates:
- `enriched_pet_profile.json` — Pet profiles with confidence scores
- `pet_letters.txt` — Collective letter from all pets
- `visual_prompt.txt` — DALL-E 3 prompt
- `personality_badge.json` — Assigned badge and description
- `[badge image].png` — Badge icon (from FrontEnd_Mobile/)
- `images/collective_pet_portrait.png` — AI-generated image
- `predicted_breed.json` — Dog breed predictions (for unknown/mixed breeds only)
- `unknowns.json` — Analysis of missing pet attributes (if any)
- `zip_aesthetics.json` — Regional style info used for personalization

## Branch Workflow
- For development, use a feature branch (e.g., `branch_yash`) to avoid affecting `main`.
- Merge changes to `main` only after testing.

## Requirements
- Python 3.8+
- OpenAI API key
- See `requirements.txt`

## Support
For issues or questions, please open an issue on the repository.
