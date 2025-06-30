# Chewy Playback Pipeline Collection

## Overview
This repository contains four distinct pipelines for generating personalized pet content using Chewy customer data. Each pipeline is designed for different use cases and data scenarios.

## Pipeline Architecture

All pipelines use a three-agent architecture:
1. **Review and Order Intelligence Agent** - Analyzes customer data to create pet profiles
2. **Narrative Generation Agent** - Generates personalized letters from pets
3. **Image Generation Agent** - Creates AI-generated pet portraits

## Available Pipelines

### 1. [Original Pipeline](./Original_Pipeline/)
**Purpose**: Standard pipeline using order history and review data
- ✅ Individual letters from each pet
- ✅ AI-generated portraits for each pet
- ✅ Review-based pet insights
- ✅ Confidence scoring

### 2. [Boyue Pipeline](./Boyue_Pipeline/)
**Purpose**: Enhanced narrative generation with collective letters
- ✅ Collective letters from all pets
- ✅ Enhanced visual prompts
- ✅ Review-based product mentions
- ✅ Single image per customer

### 3. [No Reviews NULL Pipeline](./No_Reviews_NULL_Pipeline/)
**Purpose**: Testing pipeline robustness with NULL review data
- ✅ NULL review data replacement
- ✅ Order-only pet insights
- ✅ Generic pet names
- ✅ Baseline comparison

### 4. [Ishita No Reviews Pipeline](./Ishita_No_Reviews_Pipeline/)
**Purpose**: Processing customers who never gave reviews
- ✅ Zero-review customer dataset
- ✅ Local data processing
- ✅ Order-based insights
- ✅ Real customer data

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Required packages (see `requirements.txt`)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd chewy-playback

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### Choose Your Pipeline

#### For Standard Processing (with reviews):
```bash
cd Original_Pipeline
python run_pipeline_for_customer.py
```

#### For Enhanced Narrative Generation:
```bash
cd Boyue_Pipeline
python run_pipeline_boyue_for_customer.py
```

#### For Testing Without Reviews:
```bash
cd No_Reviews_NULL_Pipeline
python run_pipeline_no_reviews_for_customer.py
```

#### For Zero-Review Customers:
```bash
cd Ishita_No_Reviews_Pipeline
python run_pipeline_with_local_data.py
```

## Pipeline Comparison

| Feature | Original | Boyue | NULL | Ishita |
|---------|----------|-------|------|--------|
| Review Data | ✅ | ✅ | ❌ | ❌ |
| Individual Letters | ✅ | ❌ | ✅ | ✅ |
| Collective Letters | ❌ | ✅ | ❌ | ❌ |
| Visual Prompts | ❌ | ✅ | ❌ | ❌ |
| Confidence Scoring | ✅ | ✅ | ✅ | ✅ |
| Unknown Pet Handling | ✅ | ✅ | ✅ | ✅ |
| Local Data | ❌ | ❌ | ❌ | ✅ |

## Data Requirements

### Original & Boyue Pipelines
- `Data/order_history.csv` - Customer order history
- `Data/qualifying_reviews.csv` - Customer review data

### NULL Pipeline
- `Data/order_history.csv` - Customer order history
- `Data/qualifying_reviews.csv` - NULL review data

### Ishita Pipeline
- `Data_No_Reviews/processed_orderhistory.csv` - Processed order history
- `Data_No_Reviews/zero_reviews.csv` - Zero-review customer data

## Output Structure

Each pipeline generates:
- `enriched_pet_profile.json` - Pet profile with confidence scores
- `pet_letters.txt` - Personalized letters from pets
- `images/` - AI-generated pet portraits
- `visual_prompt.txt` - (Boyue only) Enhanced visual prompts

## Use Cases

### Original Pipeline
- Standard customer engagement
- Individual pet personalization
- Review-based insights

### Boyue Pipeline
- Enhanced storytelling
- Collective family narratives
- Marketing campaigns

### NULL Pipeline
- System testing
- Baseline comparison
- Data quality assessment

### Ishita Pipeline
- Low-engagement customers
- No-review customer targeting
- Customer segmentation

## Configuration

All pipelines support:
- Environment variable API keys
- Command-line API keys
- Custom customer selection
- Batch processing

## Dependencies

- `pandas` - Data processing
- `openai` - AI model integration
- `requests` - API calls
- `pathlib` - File operations

## Contributing

Each pipeline is self-contained with its own README and configuration. To modify a pipeline:

1. Navigate to the specific pipeline folder
2. Follow the pipeline-specific README
3. Test changes with the provided scripts
4. Update the pipeline README if needed

## Support

For issues with specific pipelines, check the individual pipeline README files for troubleshooting guides and examples.
