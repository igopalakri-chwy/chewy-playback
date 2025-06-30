# Original Chewy Playback Pipeline

## Overview
This is the original Chewy Playback Pipeline that processes customer data using order history and review data to generate personalized pet content.

## Architecture
The pipeline consists of three main agents:

1. **Review and Order Intelligence Agent** - Analyzes order history and review data to create enriched pet profiles
2. **Narrative Generation Agent** - Generates collective letters from all pets to their human
3. **Image Generation Agent** - Creates AI-generated collective images featuring all pets

## Data Requirements
- `Data/order_history.csv` - Customer order history
- `Data/qualifying_reviews.csv` - Customer review data with pet information

## Features
- ✅ Enriched pet profiles with confidence scores
- ✅ Collective letters from all pets
- ✅ AI-generated collective pet portrait
- ✅ Handles multiple pets per customer
- ✅ Processes specific customers or all customers

## Usage

### Run for a specific customer:
```bash
python run_pipeline_for_customer.py
```

### Run for multiple customers:
```bash
python run_pipeline_for_multiple_customers.py
```

### Run for specific customers:
```bash
python chewy_playback_pipeline.py --customers 1183376 1154095
```

## Output Structure
```
Output/
├── 1183376/
│   ├── enriched_pet_profile.json
│   ├── pet_letters.txt
│   └── images/
│       └── collective_pet_portrait.png
└── 1154095/
    ├── enriched_pet_profile.json
    ├── pet_letters.txt
    └── images/
        └── collective_pet_portrait.png
```

## Key Features
- **Review Integration**: Uses actual customer reviews to understand pet preferences
- **Collective Letters**: All pets write one letter together
- **Collective Images**: Single AI-generated image featuring all pets
- **Confidence Scoring**: Calculates confidence scores for pet profile accuracy
- **Unknown Pet Handling**: Gracefully handles pets with incomplete information

## Dependencies
- OpenAI API key required
- Python packages: pandas, openai, requests, pathlib

## Configuration
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or pass it as a command line argument:
```bash
python chewy_playback_pipeline.py --api-key "your-api-key-here"
``` 