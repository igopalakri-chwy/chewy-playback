# Chewy Playback Pipeline 🚀

A comprehensive pipeline that orchestrates three AI agents to create personalized pet experiences from Chewy data.

## 🌟 Overview

The Chewy Playback Pipeline processes customer data through three specialized agents:

1. **Review and Order Intelligence Agent** - Analyzes order history and reviews to create enriched pet profiles
2. **Narrative Generation Agent** - Generates personalized letters from pets to their humans
3. **Image Generation Agent** - Creates custom pet portraits using AI-generated visual prompts

## 📁 Directory Structure

```
chewy-playback/
├── chewy_playback_pipeline.py    # Main pipeline orchestrator
├── test_pipeline.py              # Test script for verification
├── requirements.txt              # Python dependencies
├── PIPELINE_README.md           # This documentation
├── Data/                        # Input CSV files
│   ├── order_history.csv
│   └── qualifying_reviews.csv
├── Agents/                      # Individual agent implementations
│   ├── Review_and_Order_Intelligence_Agent/
│   ├── Narrative_Generation_Agent/
│   └── Image_Generation_Agent/
└── Output/                      # Generated outputs (created by pipeline)
    └── {customer_id}/
        ├── enriched_pet_profile.json
        ├── pet_letters.txt
        └── images/
            ├── {pet_name}_portrait.png
            └── ...
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up OpenAI API Key

Create a `.env` file in the root directory:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

Or set the environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the Pipeline

**Process all customers:**
```bash
python chewy_playback_pipeline.py
```

**Process specific customers:**
```bash
python chewy_playback_pipeline.py --customers 1183376 1234567
```

**Test with a single customer:**
```bash
python test_pipeline.py
```

## 🔄 Pipeline Flow

### Step 1: Data Preprocessing
- Reads raw CSV files from `Data/` directory
- Preprocesses data for the Review and Order Intelligence Agent
- Creates `processed_orderhistory.csv` and `processed_qualifyingreviews.csv`

### Step 2: Review and Order Intelligence Agent
- Analyzes customer order history and reviews
- Extracts pet characteristics, personality traits, and preferences
- Generates enriched pet profiles with confidence scores
- Output: JSON with detailed pet insights

### Step 3: Narrative Generation Agent
- Takes enriched pet profiles as input
- Generates personalized letters from pets to their humans
- Creates visual prompts for image generation
- Output: Letters and image generation prompts

### Step 4: Image Generation Agent
- Uses visual prompts to generate custom pet portraits
- Creates 1024x1024 images using OpenAI DALL-E 3
- Downloads and saves images locally
- Output: Custom pet portraits

### Step 5: Output Organization
- Creates customer-specific directories in `Output/`
- Saves enriched profiles, letters, and images
- Organizes everything by customer ID

## 📊 Input Data Requirements

### Order History CSV (`Data/order_history.csv`)
Required columns:
- `CustomerID`: Unique customer identifier
- `ProductID`: Product identifier  
- `ProductName`: Product name/description
- `OrderDate`: Date of order
- `Quantity`: Quantity ordered
- `Price`: Product price

### Qualifying Reviews CSV (`Data/qualifying_reviews.csv`)
Required columns:
- `CustomerID`: Unique customer identifier
- `PetName`: Name of the pet
- `ReviewText`: Customer review text
- `PetType`: Type of pet (dog, cat, etc.)
- `Breed`: Pet breed
- `LifeStage`: Life stage (puppy, adult, senior, etc.)
- `Gender`: Pet gender
- `SizeCategory`: Size category (small, medium, large, etc.)
- `Weight`: Pet weight
- `Birthday`: Pet birthday (YYYY-MM-DD format)

## 📤 Output Structure

For each customer, the pipeline creates:

```
Output/{customer_id}/
├── enriched_pet_profile.json    # Detailed pet insights with confidence scores
├── pet_letters.txt              # Personalized letters from pets to humans
└── images/                      # Custom pet portraits
    ├── {pet_name}_portrait.png
    └── ...
```

### Enriched Pet Profile JSON
Contains detailed insights for each pet:
- Basic info (type, breed, gender, age)
- Personality traits with confidence scores
- Dietary preferences and behavioral cues
- Most ordered products (filtered by pet type)
- Health mentions and brand preferences

### Pet Letters
Personalized, heartfelt letters written from each pet's perspective, including:
- Specific personality traits and behaviors
- Favorite products and activities
- Emotional connection to their human
- Unique voice and character

### Pet Portraits
Custom AI-generated images featuring:
- Pet's breed and characteristics
- Personality-based visual elements
- Chewy branding
- Wholesome, shareable aesthetic

## ⚙️ Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for all AI operations
- `OPENAI_MODEL`: Model to use (default: gpt-4o for text, dall-e-3 for images)
- `OPENAI_TEMPERATURE`: Response creativity (default: 0.8 for letters, 0.1 for analysis)

### Pipeline Options
- `--customers`: Specify customer IDs to process
- `--api-key`: Override environment variable for API key

## 🧪 Testing

Run the test script to verify the pipeline works:

```bash
python test_pipeline.py
```

This will:
- Process customer 1183376
- Generate all outputs
- Display the file structure
- Verify everything works correctly

## 🔧 Troubleshooting

### Common Issues

**"OpenAI API key not found"**
- Ensure `.env` file exists with `OPENAI_API_KEY=your-key`
- Or set environment variable: `export OPENAI_API_KEY="your-key"`

**"Data files not found"**
- Ensure `Data/order_history.csv` and `Data/qualifying_reviews.csv` exist
- Check file permissions and paths

**"Module not found" errors**
- Install dependencies: `pip install -r requirements.txt`
- Ensure all agent directories are present

**Image generation fails**
- Check OpenAI API quota and billing
- Verify DALL-E 3 access
- Check internet connection for image downloads

### Debug Mode

For detailed logging, modify the pipeline script to add debug prints or use Python's logging module.

## 📈 Performance

### Processing Times
- **Small dataset** (< 100 customers): ~5-10 minutes
- **Medium dataset** (100-1000 customers): ~30-60 minutes  
- **Large dataset** (> 1000 customers): ~2-4 hours

### Cost Estimation
- **Text generation**: ~$0.01-0.05 per customer
- **Image generation**: ~$0.04 per image
- **Total**: ~$0.05-0.10 per customer (varies by number of pets)

## 🔮 Future Enhancements

- **Batch processing**: Process multiple customers in parallel
- **Caching**: Cache intermediate results to avoid reprocessing
- **Custom prompts**: Allow customization of letter and image prompts
- **Quality filters**: Add confidence thresholds for outputs
- **Error recovery**: Resume processing from failure points

## 📄 License

Prototype project for internal use only. Not open-sourced.

---

> "Your pet's digital life, lovingly narrated." 🐶🐱 