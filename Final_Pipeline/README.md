# Chewy Playback Pipeline (Final Unified Version)

This is the final unified pipeline that combines the functionality of both the Original Pipeline (for customers with reviews) and the No Reviews Pipeline (for customers without reviews), with advanced personalization features including location-based backgrounds and intelligent order count filtering.

## Overview

The Final Pipeline automatically detects whether a customer has posted reviews or not and uses the appropriate intelligence agent. It also includes sophisticated personalization features:

- **Review and Order Intelligence Agent**: Used when customers have review data
- **Order Intelligence Agent**: Used when customers have no review data
- **Location-Based Personalization**: ZIP code-driven background personalization
- **Order Count Filtering**: Intelligent routing based on order history
- **Generic Playback Support**: Complete data saving for customers with limited orders

## Key Features

### 🧠 Intelligent Agent Selection
- Automatically detects if a customer has reviews
- Uses the most appropriate agent for each customer
- Handles NULL review data gracefully

### 🗺️ Location-Based Personalization
- **ZIP Code Integration**: Extracts customer ZIP codes from Snowflake data
- **Location Background Generator**: Maps ZIP codes to city/state landmarks
- **Dynamic Background Selection**: 
  - Major cities: City-specific landmarks (Space Needle, Hollywood Sign, Golden Gate Bridge)
  - States: State-specific landmarks (Mount Rainier, Grand Canyon, etc.)
  - Unknown locations: Generic regional aesthetics
- **Enhanced Visual Prompts**: Location backgrounds incorporated into DALL-E prompts
- **Regional Aesthetics**: ZIP code-driven color schemes and art styles

### 📊 Order Count Filtering
- **Minimum Order Threshold**: 5 orders required for personalized playback
- **Intelligent Routing**: 
  - ≥ 5 orders: Full personalized experience with location backgrounds
  - < 5 orders: Generic playback with complete data saving
- **Data Quality Assurance**: Ensures sufficient order history for meaningful personalization

### ✍️ Unified Narrative Generation
- Uses the Original Pipeline's improved prompts
- Generates shorter, more focused letters (100-200 words for individual, 150-250 for collective)
- Creates collective letters from all pets
- Optimized visual prompts for DALL-E 3
- **Location Context Integration**: ZIP aesthetics influence narrative style

### 🎨 Enhanced Image Generation
- Explicit pet count and naming in prompts
- No extra pets or humans in generated images
- Clean, focused visual prompts
- **Location Background Integration**: Backgrounds visible but not overwhelming

### 📊 Confidence Scoring
- Automatic confidence score calculation
- Integrated into the pipeline workflow
- Both pet-level and customer-level scores

### 💾 Generic Playback Data Saving
- **Complete Data Persistence**: All generic facts saved to separate JSON files
- **Individual File Organization**: Each data type in its own file
- **Robust Serialization**: Custom encoder handles Decimal and datetime objects
- **Structured Output**: Easy to locate and process specific data

### 🍽️ Enhanced Food Consumption Analysis
- **Complete 50-State Coverage**: Rich cultural references for every state
- **Iconic City Support**: Major cities with city-specific analogies
- **Precise Weight Calculations**: Accurate tier-based comparisons
- **Cultural Relevance**: State-specific items (Alabama football helmets, Alaska snowflakes, etc.)
- **Location-Based Fun Facts**: Personalized food consumption insights

## Directory Structure

```
Final_Pipeline/
├── chewy_playback_pipeline.py          # Main unified pipeline
├── customer_queries.json               # Snowflake query templates
├── snowflake_data_connector.py         # Snowflake integration
├── requirements.txt                    # Dependencies
├── README.md                          # This file
├── Agents/                            # Agent modules
│   ├── Review_and_Order_Intelligence_Agent/
│   ├── Narrative_Generation_Agent/
│   │   ├── pet_letter_llm_system.py   # Enhanced with location backgrounds
│   │   └── location_background_generator.py  # NEW: Location mapping
│   ├── Image_Generation_Agent/
│   │   └── letter_agent.py            # Enhanced with location prompts
│   └── Breed_Predictor_Agent/
├── customer_queries.json              # Snowflake query templates
├── dog_breed_data/                    # Breed prediction data
└── Output/                            # Generated outputs
    └── {customer_id}/
        ├── enriched_pet_profile.json
        ├── pet_letters.txt            # Personalized with location context
        ├── visual_prompt.txt          # Location-aware prompts
        ├── personality_badge.json     # Personality badges
        ├── zip_aesthetics.json        # Location aesthetics data
        ├── images/
        │   └── collective_pet_portrait.png  # Location-background images
        ├── predicted_breed.json       # Breed predictions
        ├── food_fun_fact.json         # Food consumption facts
        ├── amount_donated.json        # Generic playback data
        ├── cuddliest_month.json       # Generic playback data
        ├── total_months.json          # Generic playback data
        ├── autoship_savings.json      # Generic playback data
        ├── most_ordered.json          # Generic playback data
        └── yearly_food_count.json     # Generic playback data
```

## Usage

### Single Customer
```bash
python chewy_playback_pipeline.py --customers 1183376
```

### Multiple Customers
```bash
python chewy_playback_pipeline.py --customers 1183376 1317924 2209529
```

### With Custom API Key
```bash
python chewy_playback_pipeline.py --customers 1183376 --api-key "your-api-key"
```

## How It Works

### 1. Data Preprocessing
- Processes order history and review data from Snowflake
- Creates standardized data formats for agents
- Caches data for efficient processing

### 2. Intelligence Agent Selection
- Checks if customer has reviews in the dataset
- Routes to appropriate agent:
  - **With Reviews**: Review and Order Intelligence Agent
  - **No Reviews**: Order Intelligence Agent

### 3. Order Count Filtering
- **Confidence Score Check**: Only customers with score > 0.6 considered for personalization
- **Order Count Validation**: Minimum 5 orders required for personalized playback
- **Intelligent Routing**:
  - ≥ 5 orders: Full personalized experience
  - < 5 orders: Generic playback with complete data saving

### 4. Location Background Generation
- **ZIP Code Extraction**: Retrieves customer ZIP code from Snowflake
- **Location Mapping**: Maps ZIP to city/state using zippopotam.us API
- **Background Selection**: 
  - Major cities: City-specific landmarks
  - States: State-specific landmarks
  - Unknown: Regional aesthetics
- **Aesthetics Generation**: Creates location-specific visual styles

### 5. Profile Generation
- **Review Agent**: Creates detailed pet profiles using review sentiment and order patterns
- **Order Agent**: Creates basic pet profiles using only order history patterns
- **Location Integration**: ZIP aesthetics influence profile generation

### 6. Narrative Generation
- Generates collective letters from all pets
- Creates optimized visual prompts for DALL-E 3
- Uses shorter, more focused content
- **Location Context**: Incorporates location backgrounds and regional aesthetics

### 7. Image Generation
- Creates collective pet portraits
- Explicit pet count and naming
- No extra pets or humans
- **Location Backgrounds**: Backgrounds visible but not overwhelming

### 8. Output Generation
- Saves enriched pet profiles with confidence scores
- Saves collective letters with location context
- Saves visual prompts with location backgrounds
- Downloads and saves generated images
- **Generic Playback**: Saves all generic facts to separate JSON files

## Output Files

### For Personalized Playback Customers (≥ 5 orders):
- **`enriched_pet_profile.json`**: Complete pet profiles with confidence scores
- **`pet_letters.txt`**: Collective letter from all pets with location context
- **`visual_prompt.txt`**: DALL-E 3 prompt with location backgrounds
- **`personality_badge.json`**: Assigned personality badge
- **`zip_aesthetics.json`**: Location aesthetics and background data
- **`images/collective_pet_portrait.png`**: Generated pet portrait with location background
- **`predicted_breed.json`**: Breed predictions for unknown breeds
- **`food_fun_fact.json`**: Food consumption fun facts

### For Generic Playback Customers (< 5 orders):
- **`enriched_pet_profile.json`**: Basic pet profiles
- **`predicted_breed.json`**: Breed predictions (if needed)
- **`food_fun_fact.json`**: Food consumption facts
- **`amount_donated.json`**: Customer donation information
- **`cuddliest_month.json`**: Month with most orders
- **`total_months.json`**: Total months as customer
- **`autoship_savings.json`**: Autoship savings data
- **`most_ordered.json`**: Most frequently ordered product
- **`yearly_food_count.json`**: Detailed food consumption data

## Location Background System

### Supported Locations:
- **Major Cities**: 20+ US cities with specific landmarks
- **All 50 States**: State-specific landmarks and backgrounds
- **Unknown Locations**: Regional aesthetic fallbacks

### Background Examples:
- **Seattle**: Space Needle, Puget Sound
- **Los Angeles**: Hollywood Sign, palm trees
- **San Francisco**: Golden Gate Bridge, bay views
- **Miami**: Beach scenes, Art Deco architecture
- **Washington State**: Mount Rainier, evergreen forests
- **Arizona**: Grand Canyon, desert landscapes

### Technical Implementation:
- **ZIP Code API**: Uses zippopotam.us for location lookup
- **Background Generator**: `LocationBackgroundGenerator` class
- **Aesthetics Integration**: ZIP aesthetics influence narrative and visual prompts
- **Fallback Handling**: Graceful degradation for unknown locations

## Order Count Filter Logic

### Decision Matrix:
| Confidence Score | Order Count | Playback Type | Features |
|------------------|-------------|---------------|----------|
| > 0.6 | ≥ 5 | Personalized | Full experience + location backgrounds |
| > 0.6 | < 5 | Generic | Complete data saving, no narrative/image |
| 0.3-0.6 | Any | Generic | Basic data, no personalization |
| < 0.3 | Any | No Playback | Minimal processing |

### Benefits:
- **Data Quality**: Ensures sufficient order history for meaningful personalization
- **Cost Efficiency**: Reduces API calls for customers with limited data
- **Quality Control**: Prevents poor personalization based on insufficient data
- **Scalability**: Optimizes pipeline performance for large customer bases

## Agent Differences

### Review and Order Intelligence Agent
- Uses both review sentiment and order patterns
- Can identify multiple pets per customer
- Higher confidence scores due to more data
- Detailed personality and preference analysis
- Location-aware profile generation

### Order Intelligence Agent
- Uses only order history patterns
- Creates single generic pet profile
- Lower confidence scores
- Basic preference inference from product choices
- Location integration for eligible customers

## Requirements

- Python 3.8+
- OpenAI API key
- Snowflake credentials
- Required packages in `requirements.txt`

## Environment Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
   
   Create a `.env` file in your project root with the following content:
   ```bash
   # OpenAI API Key
   OPENAI_API_KEY="your-api-key-here"
   
   # Snowflake Credentials
   SNOWFLAKE_USER="your-snowflake-user"
   SNOWFLAKE_ACCOUNT="your-snowflake-account"
   SNOWFLAKE_WAREHOUSE="your-warehouse"
   SNOWFLAKE_DATABASE="your-database"
   SNOWFLAKE_SCHEMA="your-schema"
   SNOWFLAKE_AUTHENTICATOR="externalbrowser"
   ```
   
   **Note**: The `.env` file is automatically ignored by git to keep your credentials secure.

3. Configure Snowflake connection in `snowflake_data_connector.py`

## Error Handling

The pipeline includes comprehensive error handling:
- Graceful fallbacks for API failures
- Data validation and preprocessing
- Customer-specific error isolation
- Detailed logging and progress tracking
- Location API fallbacks
- JSON serialization error handling

## Performance

- Processes customers individually to isolate errors
- Automatic retry logic for API calls
- Efficient data loading and caching
- Progress tracking for long-running operations
- Location data caching for efficiency
- Generic playback optimization for customers with limited data

## Recent Updates

### Enhanced Food Consumption Analyzer (Latest)
- ✅ Complete 50-state coverage with rich cultural references
- ✅ Enhanced iconic cities with precise weight calculations
- ✅ State-specific analogies (Alabama football helmets, Alaska snowflakes, etc.)
- ✅ Improved weight tiers and cultural accuracy
- ✅ Comprehensive testing with multiple ZIP codes
- ✅ Pipeline integration maintained with enhanced functionality

### Location Background Personalization (Latest)
- ✅ ZIP code extraction from Snowflake data
- ✅ Location mapping with zippopotam.us API
- ✅ Dynamic background selection for cities and states
- ✅ Enhanced narrative generation with location context
- ✅ Location-aware image generation
- ✅ Regional aesthetics integration

### Order Count Filter (Latest)
- ✅ Minimum 5 orders required for personalized playback
- ✅ Intelligent routing based on order history
- ✅ Generic playback with complete data saving
- ✅ Data quality assurance
- ✅ Cost optimization

### Generic Playback Data Saving (Latest)
- ✅ Complete data persistence for customers with < 5 orders
- ✅ Individual JSON files for each data type
- ✅ Custom JSON encoder for Decimal/datetime objects
- ✅ Structured output organization
- ✅ Error handling for serialization issues 