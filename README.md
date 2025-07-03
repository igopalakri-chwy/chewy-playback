# Chewy Playback Pipeline (Final Unified Version)

This repository now contains only the **Final_Pipeline**, the unified and most advanced version of the Chewy Playback system. All legacy and experimental pipelines have been removed for clarity and maintainability.

## Overview

The Final Pipeline automatically generates personalized pet content for Chewy customers by:
- Analyzing order and review data
- Building detailed pet profiles
- Generating playful, personality-rich letters from the pets
- Creating DALL-E 3-optimized visual prompts
- Assigning a household personality badge (with icon)
- Generating collective pet portraits using AI

## Key Features
- **Automatic agent selection**: Uses review data if available, otherwise falls back to order-only analysis
- **Unified narrative generation**: Short, collective letters and visual prompts for all pets
- **Personality badge assignment**: Household badge with compatible types and icon
- **Confidence scoring**: For each pet and customer
- **Robust error handling**: Graceful fallbacks and detailed logging

## Directory Structure

```
Final_Pipeline/
├── chewy_playback_pipeline.py          # Main pipeline
├── run_pipeline_for_customer.py        # Run for a single customer
├── run_pipeline_for_multiple_customers.py  # Run for multiple customers
├── requirements.txt                    # Dependencies
├── README.md                           # This file
├── Agents/                             # Agent modules
├── Data/                               # Input data (order_history.csv, qualifying_reviews.csv)
└── Output/                             # Results for each customer
```

## Quick Start

1. **Install dependencies:**
```bash
cd Final_Pipeline
pip install -r requirements.txt
```

2. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Place your data files in `Final_Pipeline/Data/`:**
- `order_history.csv`
- `qualifying_reviews.csv`

4. **Run the pipeline:**
- For a single customer:
  ```bash
  python run_pipeline_for_customer.py 1183376
  ```
- For multiple customers:
  ```bash
  python run_pipeline_for_multiple_customers.py 1183376 1317924 2209529
  ```

## Output
For each customer, the pipeline generates:
- `enriched_pet_profile.json` — Pet profiles with confidence scores
- `pet_letters.txt` — Collective letter from all pets
- `visual_prompt.txt` — DALL-E 3 prompt
- `personality_badge.json` — Assigned badge and description
- `[badge image].png` — Badge icon
- `images/collective_pet_portrait.png` — AI-generated image

## Requirements
- Python 3.8+
- OpenAI API key
- See `requirements.txt`

## Support
For issues or questions, please open an issue on the repository.
