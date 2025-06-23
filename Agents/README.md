# Review Intelligence Agent 🐾🧠

## Overview

The Review Intelligence Agent is a sophisticated AI-powered system that analyzes customer reviews from CSV files to extract meaningful insights about pets. Using OpenAI's GPT-4 model, it processes review data to understand pet personalities, behaviors, preferences, and health patterns, with full customer context support.

## Features

### 🎯 Core Capabilities
- **CSV Data Processing**: Load and process customer review data from CSV files
- **Customer-Pet Grouping**: Automatically group reviews by customer ID and pet name
- **Personality Analysis**: Extracts personality traits from review content
- **Behavioral Pattern Recognition**: Identifies recurring behaviors and patterns
- **Health Monitoring**: Tracks health observations and improvements
- **Product Effectiveness**: Evaluates how products affect pet behavior
- **Emotional State Assessment**: Quantifies emotional states across different contexts
- **Social Behavior Analysis**: Understands interactions with humans and other pets

### 📊 Output Structure
The agent outputs comprehensive JSON data including:
- Customer ID for tracking and integration
- Personality traits and behavioral patterns
- Eating habits and preferences
- Play preferences and activity levels
- Health observations and improvements
- Social behavior and training progress
- Environmental preferences and stress triggers
- Product effectiveness ratings
- Overall sentiment analysis
- Confidence scores for insights

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API Key**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### CSV File Processing

```python
from review_intelligence_agent import ReviewIntelligenceAgent

# Initialize the agent
agent = ReviewIntelligenceAgent()

# Process CSV file with customer reviews
results = agent.process_csv_file("customer_reviews.csv", "output/")

# Results structure: {customer_id: {pet_name: PetInsight}}
for customer_id, pets_insights in results.items():
    print(f"Customer {customer_id}:")
    for pet_name, insight in pets_insights.items():
        print(f"  {pet_name}: {insight.confidence_score:.2f} confidence")
```

### CSV Data Loading and Grouping

```python
# Load CSV data
df = agent.load_reviews_from_csv("customer_reviews.csv")

# Group reviews by customer and pet
grouped_reviews = agent.group_reviews_by_customer_and_pet(df)

# Process specific customer-pet combination
customer_id = "CUST001"
pet_name = "Max"
reviews = grouped_reviews[customer_id][pet_name]
insight = agent.analyze_reviews(reviews, customer_id, pet_name)
```

### Running the Example

```bash
cd Agents
python test_review_agent.py
```

## CSV Input Format

The agent expects a CSV file with the following columns:

| Column | Required | Description |
|--------|----------|-------------|
| CustomerID | ✅ | Unique customer identifier |
| ReviewID | ❌ | Review identifier |
| Product_Part_Number | ❌ | Product part number |
| Product_Name | ❌ | Product name |
| Pet_Name | ✅ | Name of the pet |
| Review_Title | ❌ | Review title |
| Review_Text | ✅ | Review content |
| is_recommended | ❌ | Whether product is recommended |
| moderation_status | ❌ | Review moderation status |
| rating | ❌ | Review rating (1-5) |
| user_nickname | ❌ | User nickname |
| document | ❌ | Review date |

**Required columns**: `CustomerID`, `Pet_Name`, `Review_Text`

## Output Format

The agent returns a `PetInsight` object with the following structure:

```json
{
    "customer_id": "CUST001",
    "pet_name": "Max",
    "personality_traits": ["energetic", "playful", "anxious", "food-motivated"],
    "behavioral_patterns": ["stranger anxiety", "food enthusiasm", "toy engagement"],
    "eating_habits": {
        "preferences": ["premium food", "interactive feeding"],
        "timing": "regular mealtimes with enthusiasm",
        "portion_control": "good",
        "pickiness_level": "low"
    },
    "play_preferences": ["interactive puzzle toys", "fetch", "mental stimulation"],
    "health_observations": ["improved coat condition", "increased energy", "better digestion"],
    "favorite_products": ["Premium Dog Food", "Interactive Puzzle Toy", "Digestive Probiotic"],
    "emotional_state": {
        "happiness": 0.85,
        "anxiety": 0.25,
        "excitement": 0.80,
        "calmness": 0.60
    },
    "social_behavior": {
        "with_humans": "very affectionate and trusting",
        "with_other_pets": "improving with calming supplements",
        "stranger_reaction": "initially anxious but improving"
    },
    "training_progress": {
        "obedience": "good",
        "house_training": "excellent",
        "tricks_learned": ["puzzle solving", "calm behavior"]
    },
    "environmental_preferences": ["indoor play", "quiet spaces", "familiar environments"],
    "activity_level": "high",
    "stress_triggers": ["strangers", "loud noises", "unfamiliar situations"],
    "comfort_zones": ["home", "familiar people", "routine activities"],
    "communication_style": "vocal and expressive",
    "relationship_with_owner": "very attached and trusting",
    "seasonal_behaviors": {
        "summer": ["enjoys outdoor activities", "more active"],
        "winter": ["prefers indoor play", "cozy activities"],
        "spring": ["loves walks", "exploring nature"],
        "fall": ["enjoys outdoor play", "moderate activity"]
    },
    "product_effectiveness": {
        "Premium Dog Food": {
            "effectiveness_rating": 0.95,
            "improvements_noted": ["better coat", "more energy", "improved appetite"],
            "side_effects": []
        }
    },
    "overall_sentiment": "positive",
    "confidence_score": 0.88,
    "review_count": 4,
    "analysis_timestamp": "2024-01-15T10:30:00"
}
```

## File Output Structure

The agent generates customer-centric JSON files:

1. **Customer JSON Files**: `{customer_id}.json`

Example:
```
output/
├── CUST001.json
├── CUST002.json
├── CUST003.json
└── CUST004.json
```

Each customer JSON file contains:
- **Customer ID**: Unique identifier
- **Analysis Metadata**: Summary statistics and timestamps
- **Pets**: Complete insights for each pet
- **Customer Summary**: Aggregated insights across all pets

### Customer JSON Structure

```json
{
  "customer_id": "CUST001",
  "analysis_metadata": {
    "total_pets": 2,
    "total_reviews": 7,
    "analysis_timestamp": "2024-01-15T10:30:00",
    "overall_sentiment": "positive",
    "average_confidence": 0.85
  },
  "pets": {
    "Max": {
      // Complete pet insights (see Output Format above)
    },
    "Luna": {
      // Complete pet insights for second pet
    }
  },
  "customer_summary": {
    "pet_types": ["Max", "Luna"],
    "personality_diversity": {
      "total_unique_traits": 8,
      "most_common_traits": [["energetic", 1], ["playful", 1]],
      "trait_distribution": {"energetic": 1, "playful": 1}
    },
    "common_health_concerns": [
      ["improved coat condition", 1],
      ["increased energy", 1]
    ],
    "favorite_product_categories": [
      ["Premium Dog Food", 1],
      ["Interactive Puzzle Toy", 1]
    ],
    "overall_activity_level": "high"
  }
}
```

## Configuration

### Model Settings
- **Model**: GPT-4 Turbo Preview (latest)
- **Temperature**: 0.3 (for consistent results)
- **Max Tokens**: 4000

### Customization
You can modify the analysis prompt in the `_create_analysis_prompt` method to focus on specific aspects or add new analysis requirements.

## Error Handling

The agent includes robust error handling:
- **CSV Loading Errors**: Validates required columns and data integrity
- **API Failures**: Returns default insights with low confidence
- **JSON Parsing Errors**: Handles malformed responses gracefully
- **Missing Data**: Uses reasonable defaults for missing information
- **Logging**: Comprehensive logging for debugging

## Performance Considerations

- **CSV Processing**: Efficient pandas-based data loading and grouping
- **API Rate Limits**: Consider implementing rate limiting for large datasets
- **Token Usage**: Monitor OpenAI API usage and costs
- **Caching**: Consider caching results for repeated analyses
- **Batch Processing**: Optimized for processing multiple customers and pets

## Integration with Chewy Playback

This agent is designed to integrate seamlessly with the Chewy Playback system:

1. **Customer Context**: Links insights to specific customers for personalized experiences
2. **Purchase Attribution**: Links reviews to specific products and orders
3. **Narrative Generation**: Provides insights for personalized pet stories
4. **Image Generation**: Offers context for creating pet-specific artwork
5. **Mobile App**: Delivers insights for the personalized playback experience

## Future Enhancements

- **Multi-language Support**: Analyze reviews in different languages
- **Sentiment Timeline**: Track emotional changes over time
- **Breed-specific Analysis**: Tailor insights based on pet breed
- **Vet Note Integration**: Combine with veterinary records
- **Real-time Processing**: Stream processing for live review analysis
- **Customer Segmentation**: Group customers by behavior patterns

## Contributing

When contributing to this agent:
1. Follow the existing code structure
2. Add comprehensive error handling
3. Include logging for debugging
4. Update the README for new features
5. Test with various CSV formats and data structures

## License

Part of the Chewy Playback project - internal use only. 