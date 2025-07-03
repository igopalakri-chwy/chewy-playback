# Chewy Playback Pipeline (Final Unified Version)

This is the final unified pipeline that combines the functionality of both the Original Pipeline (for customers with reviews) and the No Reviews Pipeline (for customers without reviews).

## Overview

The Final Pipeline automatically detects whether a customer has posted reviews or not and uses the appropriate intelligence agent:

- **Review and Order Intelligence Agent**: Used when customers have review data
- **Order Intelligence Agent**: Used when customers have no review data

## Key Features

### 🧠 Intelligent Agent Selection
- Automatically detects if a customer has reviews
- Uses the most appropriate agent for each customer
- Handles NULL review data gracefully

### ✍️ Unified Narrative Generation
- Uses the Original Pipeline's improved prompts
- Generates shorter, more focused letters (100-200 words for individual, 150-250 for collective)
- Creates collective letters from all pets
- Optimized visual prompts for DALL-E 3

### 🎨 Enhanced Image Generation
- Explicit pet count and naming in prompts
- No extra pets or humans in generated images
- Clean, focused visual prompts

### 📊 Confidence Scoring
- Automatic confidence score calculation
- Integrated into the pipeline workflow
- Both pet-level and customer-level scores

## Directory Structure

```
Final_Pipeline/
├── chewy_playback_pipeline.py          # Main unified pipeline
├── run_pipeline_for_customer.py        # Run for single customer
├── run_pipeline_for_multiple_customers.py  # Run for multiple customers
├── requirements.txt                    # Dependencies
├── README.md                          # This file
├── Agents/                            # Agent modules
│   ├── Review_and_Order_Intelligence_Agent/
│   ├── Narrative_Generation_Agent/
│   └── Image_Generation_Agent/
├── Data/                              # Input data
│   ├── order_history.csv
│   └── qualifying_reviews.csv
└── Output/                            # Generated outputs
    └── {customer_id}/
        ├── enriched_pet_profile.json
        ├── pet_letters.txt
        ├── visual_prompt.txt
        └── images/
            └── collective_pet_portrait.png
```

## Usage

### Single Customer
```bash
python run_pipeline_for_customer.py 1183376
```

### Multiple Customers
```bash
# Run for first 10 customers in dataset
python run_pipeline_for_multiple_customers.py

# Run for specific customers
python run_pipeline_for_multiple_customers.py 1183376 1317924 2209529
```

## How It Works

### 1. Data Preprocessing
- Processes order history and review data
- Creates standardized data formats for agents

### 2. Intelligence Agent Selection
- Checks if customer has reviews in the dataset
- Routes to appropriate agent:
  - **With Reviews**: Review and Order Intelligence Agent
  - **No Reviews**: Order Intelligence Agent

### 3. Profile Generation
- **Review Agent**: Creates detailed pet profiles using review sentiment and order patterns
- **Order Agent**: Creates basic pet profiles using only order history patterns

### 4. Narrative Generation
- Generates collective letters from all pets
- Creates optimized visual prompts for DALL-E 3
- Uses shorter, more focused content

### 5. Image Generation
- Creates collective pet portraits
- Explicit pet count and naming
- No extra pets or humans

### 6. Output Generation
- Saves enriched pet profiles with confidence scores
- Saves collective letters
- Saves visual prompts
- Downloads and saves generated images

## Output Files

For each customer, the pipeline generates:

- **`enriched_pet_profile.json`**: Complete pet profiles with confidence scores
- **`pet_letters.txt`**: Collective letter from all pets
- **`visual_prompt.txt`**: DALL-E 3 prompt used for image generation
- **`images/collective_pet_portrait.png`**: Generated pet portrait

## Agent Differences

### Review and Order Intelligence Agent
- Uses both review sentiment and order patterns
- Can identify multiple pets per customer
- Higher confidence scores due to more data
- Detailed personality and preference analysis

### Order Intelligence Agent
- Uses only order history patterns
- Creates single generic pet profile
- Lower confidence scores
- Basic preference inference from product choices

## Requirements

- Python 3.8+
- OpenAI API key
- Required packages in `requirements.txt`

## Environment Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Ensure data files are in the `Data/` directory:
- `order_history.csv`
- `qualifying_reviews.csv`

## Error Handling

The pipeline includes comprehensive error handling:
- Graceful fallbacks for API failures
- Data validation and preprocessing
- Customer-specific error isolation
- Detailed logging and progress tracking

## Performance

- Processes customers individually to isolate errors
- Automatic retry logic for API calls
- Efficient data loading and caching
- Progress tracking for long-running operations 