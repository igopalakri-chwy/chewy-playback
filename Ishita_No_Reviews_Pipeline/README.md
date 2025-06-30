# Ishita No Reviews Pipeline

## Overview
This pipeline is specifically designed to process customers who have never given reviews. It uses a separate dataset containing only customers with zero reviews and creates personalized content based solely on their order history.

## Architecture
The pipeline consists of three main agents:

1. **Review and Order Intelligence Agent** - Analyzes order history for customers with no reviews
2. **Narrative Generation Agent** - Generates individual letters from each pet to their human
3. **Image Generation Agent** - Creates AI-generated images for each pet

## Key Differences from Other Pipelines
- **Zero Reviews Dataset**: Uses `Data_No_Reviews/zero_reviews.csv` containing only customers with no reviews
- **Order-Only Analysis**: Pet insights based solely on product purchases
- **Real Customer Data**: Processes actual customers who have never reviewed
- **Local Data Processing**: Uses data contained within the pipeline folder

## Data Requirements
- `Data_No_Reviews/processed_orderhistory.csv` - Processed order history for no-review customers
- `Data_No_Reviews/zero_reviews.csv` - Customer data for those who never reviewed

## Features
- ✅ Pet profiles inferred from order history only
- ✅ Individual letters from each pet
- ✅ AI-generated pet portraits
- ✅ Handles multiple pets per customer
- ✅ Processes specific customers or all customers
- ✅ Local data processing

## Usage

### Run for a specific customer:
```bash
python run_pipeline_no_reviews_for_customer.py
```

### Run for multiple customers:
```bash
python run_pipeline_no_reviews_for_multiple_customers.py
```

### Run with local data:
```bash
python run_pipeline_with_local_data.py
```

## Output Structure
```
Output/
├── 13985/
│   ├── enriched_pet_profile.json
│   ├── pet_letters.txt
│   └── images/
│       └── Pet_portrait.png
├── 14306/
│   ├── enriched_pet_profile.json
│   ├── pet_letters.txt
│   └── images/
│       └── Pet_portrait.png
└── 17319/
    ├── enriched_pet_profile.json
    ├── pet_letters.txt
    └── images/
        └── Pet_portrait.png
```

## Key Features
- **Zero Review Focus**: Specifically designed for customers who never review
- **Order-Based Insights**: Pet profiles derived from purchase patterns
- **Generic Pet Names**: Uses "Pet" as default name when no review data available
- **Product Category Analysis**: Infers pet types from product categories
- **Local Data Processing**: Self-contained with its own data files

## Data Processing
The pipeline includes preprocessing steps:
- **Data Cleaning**: Removes duplicates and invalid entries
- **Column Mapping**: Maps data columns to expected format
- **Customer Filtering**: Focuses on customers with zero reviews
- **Order Analysis**: Extracts pet insights from purchase history

## Limitations
- **No Pet Names**: Cannot identify specific pet names without reviews
- **Limited Personality**: Personality traits are basic and generic
- **No Product Preferences**: Cannot determine specific product preferences
- **Lower Accuracy**: Pet type and breed inference is less accurate

## Use Cases
- **No-Review Customer Engagement**: Target customers who don't typically engage
- **Baseline Content Generation**: Create content for customers with limited data
- **Customer Segmentation**: Understand behavior of non-reviewing customers
- **Marketing Strategy**: Develop strategies for low-engagement customers

## Dependencies
- OpenAI API key required
- Python packages: pandas, openai, requests, pathlib

## Configuration
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Example Output
For customers with no reviews, the system generates:
```json
{
  "PetType": "Dog",
  "PetTypeScore": 0.7,
  "Breed": "Mixed",
  "BreedScore": 0.4,
  "PersonalityTraits": ["active", "loyal"],
  "MostOrderedProducts": ["Dog Food", "Dog Toys", "Treats"]
}
```

And letters like:
```
Human,

I just had to write you this letter to tell you how much you mean to me! 
I'm Pet, your beautiful dog, and I'm so grateful for everything you do for me...
```

## Data Files
- `Data_No_Reviews/processed_orderhistory.csv` - Cleaned order history data
- `Data_No_Reviews/zero_reviews.csv` - Customer data for zero-review customers 