import json
import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from openai import OpenAI
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root (one level up from Agents folder)
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    # Also try loading from current directory
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, continue without it
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PetInsight:
    """Data structure for pet insights extracted from reviews"""
    customer_id: str
    pet_name: str
    personality_traits: List[str]
    behavioral_patterns: List[str]
    eating_habits: Dict[str, Any]
    play_preferences: List[str]
    health_observations: List[str]
    favorite_products: List[str]
    emotional_state: Dict[str, float]
    social_behavior: Dict[str, Any]
    training_progress: Dict[str, Any]
    environmental_preferences: List[str]
    activity_level: str
    stress_triggers: List[str]
    comfort_zones: List[str]
    communication_style: str
    relationship_with_owner: str
    seasonal_behaviors: Dict[str, List[str]]
    product_effectiveness: Dict[str, Dict[str, Any]]
    overall_sentiment: str
    confidence_score: float
    review_count: int
    analysis_timestamp: str

class ReviewIntelligenceAgent:
    """
    Review Intelligence Agent that processes customer reviews from CSV to extract
    meaningful insights about pets using OpenAI's GPT models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Review Intelligence Agent.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client with new API format
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4-turbo-preview"  # Using the latest model for best results
        
    def _create_analysis_prompt(self, reviews: List[Dict[str, Any]], customer_id: str, pet_name: str) -> str:
        """
        Create a comprehensive prompt for analyzing pet reviews.
        
        Args:
            reviews: List of review dictionaries
            customer_id: Customer ID for context
            pet_name: Name of the pet being analyzed
            
        Returns:
            Formatted prompt string
        """
        # Format reviews for the prompt
        reviews_text = ""
        for i, review in enumerate(reviews, 1):
            reviews_text += f"Review {i}:\n"
            reviews_text += f"Rating: {review.get('rating', 'N/A')}/5\n"
            reviews_text += f"Text: {review.get('text', '')}\n"
            reviews_text += f"Product: {review.get('product_name', 'N/A')}\n"
            reviews_text += f"Date: {review.get('date', 'N/A')}\n"
            reviews_text += f"Title: {review.get('review_title', 'N/A')}\n"
            reviews_text += f"Recommended: {review.get('is_recommended', 'N/A')}\n\n"
        
        prompt = f"""
You are a Pet Behavior Analyst specializing in extracting meaningful insights from customer reviews about their pets. Your task is to analyze the following reviews for Customer {customer_id}'s pet {pet_name} and provide comprehensive insights in JSON format.

REVIEWS TO ANALYZE:
{reviews_text}

ANALYSIS REQUIREMENTS:
1. Extract personality traits (e.g., playful, anxious, confident, shy, energetic, calm)
2. Identify behavioral patterns (e.g., food aggression, separation anxiety, social behavior)
3. Analyze eating habits (preferences, timing, portion control, pickiness)
4. Determine play preferences (toys, activities, social vs solo play)
5. Note health observations (energy levels, coat condition, digestive issues)
6. Identify favorite products and their effectiveness
7. Assess emotional state across different contexts
8. Evaluate social behavior with humans and other animals
9. Track training progress and learning patterns
10. Note environmental preferences (indoor/outdoor, temperature, noise sensitivity)
11. Determine activity level (high, moderate, low)
12. Identify stress triggers and comfort zones
13. Analyze communication style (vocal, body language, gestures)
14. Assess relationship with owner (attachment style, trust level)
15. Note seasonal behavior changes
16. Evaluate product effectiveness with specific metrics
17. Determine overall sentiment from all reviews
18. Provide confidence score (0-1) for the analysis

OUTPUT FORMAT:
Return ONLY a valid JSON object with the following structure:
{{
    "customer_id": "{customer_id}",
    "pet_name": "{pet_name}",
    "personality_traits": ["trait1", "trait2", "trait3"],
    "behavioral_patterns": ["pattern1", "pattern2"],
    "eating_habits": {{
        "preferences": ["preference1", "preference2"],
        "timing": "description",
        "portion_control": "description",
        "pickiness_level": "low/medium/high"
    }},
    "play_preferences": ["preference1", "preference2"],
    "health_observations": ["observation1", "observation2"],
    "favorite_products": ["product1", "product2"],
    "emotional_state": {{
        "happiness": 0.85,
        "anxiety": 0.15,
        "excitement": 0.70,
        "calmness": 0.60
    }},
    "social_behavior": {{
        "with_humans": "description",
        "with_other_pets": "description",
        "stranger_reaction": "description"
    }},
    "training_progress": {{
        "obedience": "description",
        "house_training": "description",
        "tricks_learned": ["trick1", "trick2"]
    }},
    "environmental_preferences": ["preference1", "preference2"],
    "activity_level": "high/medium/low",
    "stress_triggers": ["trigger1", "trigger2"],
    "comfort_zones": ["zone1", "zone2"],
    "communication_style": "description",
    "relationship_with_owner": "description",
    "seasonal_behaviors": {{
        "summer": ["behavior1", "behavior2"],
        "winter": ["behavior1", "behavior2"],
        "spring": ["behavior1", "behavior2"],
        "fall": ["behavior1", "behavior2"]
    }},
    "product_effectiveness": {{
        "product_name": {{
            "effectiveness_rating": 0.85,
            "improvements_noted": ["improvement1", "improvement2"],
            "side_effects": ["effect1", "effect2"]
        }}
    }},
    "overall_sentiment": "positive/neutral/negative",
    "confidence_score": 0.85,
    "review_count": {len(reviews)},
    "analysis_timestamp": "{datetime.now().isoformat()}"
}}

IMPORTANT:
- Base all insights on the actual review content provided
- If information is not available in reviews, use "Not specified" or reasonable defaults
- Ensure all emotional state values are between 0 and 1
- Confidence score should reflect how much information was available for analysis
- Be specific and detailed in descriptions
- Focus on actionable insights that could help with pet care decisions
- Consider the customer context when analyzing the relationship with owner

Return ONLY the JSON object, no additional text or explanations.
"""
        return prompt
    
    def analyze_reviews(self, reviews: List[Dict[str, Any]], customer_id: str, pet_name: str) -> PetInsight:
        """
        Analyze customer reviews to extract pet insights.
        
        Args:
            reviews: List of review dictionaries with keys: text, rating, product_name, date
            customer_id: Customer ID for context
            pet_name: Name of the pet being analyzed
            
        Returns:
            PetInsight object containing extracted insights
        """
        try:
            logger.info(f"Starting analysis for Customer {customer_id}, Pet {pet_name} with {len(reviews)} reviews")
            
            if not reviews:
                logger.warning(f"No reviews provided for Customer {customer_id}, Pet {pet_name}")
                return self._create_default_insight(customer_id, pet_name)
            
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(reviews, customer_id, pet_name)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Pet Behavior Analyst. Provide only valid JSON output."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=4000
            )
            
            # Extract and parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Clean the response to ensure it's valid JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON response
            insights_data = json.loads(response_text)
            
            # Create PetInsight object
            pet_insight = PetInsight(**insights_data)
            
            logger.info(f"Successfully analyzed Customer {customer_id}, Pet {pet_name} with confidence score: {pet_insight.confidence_score}")
            return pet_insight
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            return self._create_default_insight(customer_id, pet_name)
        except Exception as e:
            logger.error(f"Error analyzing reviews for Customer {customer_id}, Pet {pet_name}: {e}")
            return self._create_default_insight(customer_id, pet_name)
    
    def _create_default_insight(self, customer_id: str, pet_name: str) -> PetInsight:
        """Create a default PetInsight when analysis fails."""
        return PetInsight(
            customer_id=customer_id,
            pet_name=pet_name,
            personality_traits=["Analysis pending"],
            behavioral_patterns=["Analysis pending"],
            eating_habits={"preferences": [], "timing": "Not specified", "portion_control": "Not specified", "pickiness_level": "Not specified"},
            play_preferences=["Analysis pending"],
            health_observations=["Analysis pending"],
            favorite_products=["Analysis pending"],
            emotional_state={"happiness": 0.5, "anxiety": 0.5, "excitement": 0.5, "calmness": 0.5},
            social_behavior={"with_humans": "Not specified", "with_other_pets": "Not specified", "stranger_reaction": "Not specified"},
            training_progress={"obedience": "Not specified", "house_training": "Not specified", "tricks_learned": []},
            environmental_preferences=["Analysis pending"],
            activity_level="Not specified",
            stress_triggers=["Analysis pending"],
            comfort_zones=["Analysis pending"],
            communication_style="Not specified",
            relationship_with_owner="Not specified",
            seasonal_behaviors={"summer": [], "winter": [], "spring": [], "fall": []},
            product_effectiveness={},
            overall_sentiment="neutral",
            confidence_score=0.0,
            review_count=0,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def save_insights_to_json(self, pet_insight: PetInsight, output_path: str) -> bool:
        """
        Save pet insights to a JSON file.
        
        Args:
            pet_insight: PetInsight object to save
            output_path: Path where to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert dataclass to dictionary
            insights_dict = asdict(pet_insight)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(insights_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Insights saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving insights to {output_path}: {e}")
            return False
    
    def process_csv_file(self, csv_path: str, output_dir: str = "output") -> Dict[str, Dict[str, PetInsight]]:
        """
        Process a CSV file containing customer reviews and generate insights for each customer-pet combination.
        Creates one JSON file per customer containing all their pets and insights.
        
        Args:
            csv_path: Path to the CSV file
            output_dir: Directory to save JSON files
            
        Returns:
            Dictionary structure: {customer_id: {pet_name: PetInsight}}
        """
        try:
            # Load and group reviews
            df = self.load_reviews_from_csv(csv_path)
            grouped_reviews = self.group_reviews_by_customer_and_pet(df)
            
            results = {}
            
            for customer_id, pets_reviews in grouped_reviews.items():
                logger.info(f"Processing Customer {customer_id} with {len(pets_reviews)} pets")
                results[customer_id] = {}
                
                for pet_name, reviews in pets_reviews.items():
                    logger.info(f"  Analyzing {len(reviews)} reviews for Pet {pet_name}")
                    
                    # Analyze reviews for this customer-pet combination
                    pet_insight = self.analyze_reviews(reviews, customer_id, pet_name)
                    results[customer_id][pet_name] = pet_insight
                
                # Save customer JSON file with all pets and insights
                safe_customer_id = customer_id.replace('/', '_').replace('\\', '_')
                customer_output_path = os.path.join(output_dir, f"{safe_customer_id}.json")
                self.save_customer_insights_to_json(results[customer_id], customer_output_path)
            
            logger.info(f"Completed processing {len(results)} customers")
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV file {csv_path}: {e}")
            raise
    
    def save_customer_insights_to_json(self, customer_insights: Dict[str, PetInsight], output_path: str) -> bool:
        """
        Save all pet insights for a customer to a comprehensive JSON file.
        
        Args:
            customer_insights: Dictionary mapping pet names to PetInsight objects
            output_path: Path where to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get customer ID from the first pet insight
            customer_id = list(customer_insights.values())[0].customer_id if customer_insights else "UNKNOWN"
            
            # Create comprehensive customer structure
            customer_data = {
                "customer_id": customer_id,
                "analysis_metadata": {
                    "total_pets": len(customer_insights),
                    "total_reviews": sum(insight.review_count for insight in customer_insights.values()),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "overall_sentiment": self._calculate_customer_sentiment(customer_insights),
                    "average_confidence": sum(insight.confidence_score for insight in customer_insights.values()) / len(customer_insights) if customer_insights else 0.0
                },
                "pets": {
                    pet_name: asdict(insight) for pet_name, insight in customer_insights.items()
                },
                "customer_summary": {
                    "pet_types": list(customer_insights.keys()),
                    "personality_diversity": self._analyze_personality_diversity(customer_insights),
                    "common_health_concerns": self._extract_common_health_concerns(customer_insights),
                    "favorite_product_categories": self._extract_favorite_categories(customer_insights),
                    "overall_activity_level": self._calculate_overall_activity_level(customer_insights)
                }
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(customer_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Customer insights saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving customer insights to {output_path}: {e}")
            return False
    
    def _calculate_customer_sentiment(self, customer_insights: Dict[str, PetInsight]) -> str:
        """Calculate overall sentiment for a customer based on all their pets."""
        sentiments = [insight.overall_sentiment for insight in customer_insights.values()]
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")
        neutral_count = sentiments.count("neutral")
        
        if positive_count > negative_count and positive_count > neutral_count:
            return "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            return "negative"
        else:
            return "neutral"
    
    def _analyze_personality_diversity(self, customer_insights: Dict[str, PetInsight]) -> Dict[str, Any]:
        """Analyze personality diversity across all pets of a customer."""
        all_traits = []
        for insight in customer_insights.values():
            all_traits.extend(insight.personality_traits)
        
        trait_counts = {}
        for trait in all_traits:
            trait_counts[trait] = trait_counts.get(trait, 0) + 1
        
        return {
            "total_unique_traits": len(set(all_traits)),
            "most_common_traits": sorted(trait_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "trait_distribution": trait_counts
        }
    
    def _extract_common_health_concerns(self, customer_insights: Dict[str, PetInsight]) -> List[str]:
        """Extract common health concerns across all pets of a customer."""
        all_health_observations = []
        for insight in customer_insights.values():
            all_health_observations.extend(insight.health_observations)
        
        # Count occurrences and return most common
        health_counts = {}
        for observation in all_health_observations:
            if observation != "Analysis pending":
                health_counts[observation] = health_counts.get(observation, 0) + 1
        
        return sorted(health_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _extract_favorite_categories(self, customer_insights: Dict[str, PetInsight]) -> List[str]:
        """Extract favorite product categories across all pets of a customer."""
        all_products = []
        for insight in customer_insights.values():
            all_products.extend(insight.favorite_products)
        
        # Count occurrences and return most common
        product_counts = {}
        for product in all_products:
            if product != "Analysis pending":
                product_counts[product] = product_counts.get(product, 0) + 1
        
        return sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _calculate_overall_activity_level(self, customer_insights: Dict[str, PetInsight]) -> str:
        """Calculate overall activity level for a customer based on all their pets."""
        activity_levels = [insight.activity_level for insight in customer_insights.values()]
        high_count = activity_levels.count("high")
        medium_count = activity_levels.count("medium")
        low_count = activity_levels.count("low")
        
        if high_count > medium_count and high_count > low_count:
            return "high"
        elif low_count > high_count and low_count > medium_count:
            return "low"
        else:
            return "medium"
    
    def load_reviews_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load reviews data from CSV file.
        
        Args:
            csv_path: Path to the CSV file containing review data
            
        Returns:
            DataFrame with review data
        """
        try:
            logger.info(f"Loading reviews from {csv_path}")
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['CustomerID', 'Pet_Name', 'Review_Text']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clean the data
            df = df.dropna(subset=['CustomerID', 'Pet_Name', 'Review_Text'])
            df = df[df['Review_Text'].str.strip() != '']
            
            logger.info(f"Loaded {len(df)} reviews from {len(df['CustomerID'].unique())} customers")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_path}: {e}")
            raise
    
    def group_reviews_by_customer_and_pet(self, df: pd.DataFrame) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Group reviews by customer ID and pet name.
        
        Args:
            df: DataFrame containing review data
            
        Returns:
            Dictionary structure: {customer_id: {pet_name: [reviews]}}
        """
        grouped_reviews = {}
        
        for _, row in df.iterrows():
            customer_id = str(row['CustomerID'])
            pet_name = str(row['Pet_Name'])
            
            # Create review dictionary
            review = {
                'text': str(row['Review_Text']),
                'rating': row.get('rating', 5),  # Default to 5 if not available
                'product_name': str(row.get('Product_Name', 'Unknown Product')),
                'date': str(row.get('document', datetime.now().strftime('%Y-%m-%d'))),
                'review_title': str(row.get('Review_Title', '')),
                'is_recommended': row.get('is_recommended', True),
                'moderation_status': str(row.get('moderation_status', 'approved')),
                'user_nickname': str(row.get('user_nickname', 'Anonymous'))
            }
            
            # Initialize customer if not exists
            if customer_id not in grouped_reviews:
                grouped_reviews[customer_id] = {}
            
            # Initialize pet if not exists
            if pet_name not in grouped_reviews[customer_id]:
                grouped_reviews[customer_id][pet_name] = []
            
            # Add review to pet's list
            grouped_reviews[customer_id][pet_name].append(review)
        
        logger.info(f"Grouped reviews into {len(grouped_reviews)} customers with {sum(len(pets) for pets in grouped_reviews.values())} total pets")
        return grouped_reviews


if __name__ == "__main__":
    """Example usage of the Review Intelligence Agent."""
    print("Review Intelligence Agent - CSV Processing Example")
    print("=" * 50)
    
    try:
        # Initialize the agent
        agent = ReviewIntelligenceAgent()
        
        # Process CSV file
        csv_path = "sample_reviews.csv"
        if os.path.exists(csv_path):
            print(f"Processing {csv_path}...")
            results = agent.process_csv_file(csv_path, "output/")
            print(f"✅ Processed {len(results)} customers")
        else:
            print(f"❌ CSV file not found: {csv_path}")
            print("Please ensure you have a CSV file with the required columns.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your OpenAI API key and CSV file format.") 