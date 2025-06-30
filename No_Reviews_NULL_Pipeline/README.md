# No Reviews NULL Pipeline

## Overview
This pipeline is a modified version of the original pipeline that replaces all review data with NULL values to test how the system performs without review information.

## Architecture
The pipeline consists of three main agents:

1. **Review and Order Intelligence Agent** - Analyzes order history and NULL review data to create basic pet profiles
2. **Narrative Generation Agent** - Generates individual letters from each pet to their human
3. **Image Generation Agent** - Creates AI-generated images for each pet

## Key Differences from Original Pipeline
- **NULL Reviews**: All review data is replaced with NULL values
- **Limited Pet Information**: Pet profiles are based solely on order history
- **Generic Pet Names**: Pets are typically named "Pet" since no review data provides names
- **Basic Insights**: Reduced confidence scores due to lack of review context

## Data Requirements
- `Data/order_history.csv` - Customer order history
- `Data/qualifying_reviews.csv` - Customer review data (replaced with NULL values)

## Features
- ✅ Basic pet profiles inferred from order history only
- ✅ Individual letters from each pet
- ✅ AI-generated pet portraits
- ✅ Handles multiple pets per customer
- ✅ Processes specific customers or all customers

## Usage

### Run for a specific customer:
```bash
python run_pipeline_no_reviews_for_customer.py
```

### Run for multiple customers:
```bash
python run_pipeline_no_reviews_for_multiple_customers.py
```

## Output Structure
```
Output/
├── 1183376/
│   ├── enriched_pet_profile.json
│   ├── pet_letters.txt
│   └── images/
│       └── Pet_portrait.png
└── 1154095/
    ├── enriched_pet_profile.json
    ├── pet_letters.txt
    └── images/
        └── Pet_portrait.png
```

## Key Features
- **Order-Only Analysis**: Pet insights based solely on product purchases
- **Generic Pet Names**: Uses "Pet" as default name when no review data available
- **Basic Personality Traits**: Inferred from product categories and brands
- **Reduced Confidence**: Lower confidence scores due to limited data

## Limitations
- **No Pet Names**: Cannot identify specific pet names without reviews
- **Limited Personality**: Personality traits are basic and generic
- **No Product Preferences**: Cannot determine specific product preferences
- **Lower Accuracy**: Pet type and breed inference is less accurate

## Use Cases
- **Testing Pipeline Robustness**: See how the system handles missing data
- **Baseline Comparison**: Compare with review-based results
- **Data Quality Assessment**: Understand impact of missing review data
- **System Validation**: Ensure pipeline doesn't crash with NULL data

## Dependencies
- OpenAI API key required
- Python packages: pandas, openai, requests, pathlib

## Configuration
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Example Output
Without review data, the system generates basic profiles:
```json
{
  "PetType": "Pet",
  "PetTypeScore": 0.5,
  "Breed": "Mixed",
  "BreedScore": 0.3,
  "PersonalityTraits": ["friendly"],
  "MostOrderedProducts": ["Generic Pet Food", "Basic Toys"]
}
```

And generic letters:
```
Human,

I just had to write you this letter to tell you how much you mean to me! 
I'm Pet, your beautiful pet, and I'm so grateful for everything you do for me...
``` 