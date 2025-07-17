import pandas as pd
import json
import logging
import re
from typing import Dict, List, Any
import openai
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReviewOrderIntelligenceAgent:
    """
    AI agent that derives enriched pet insights from order history and qualifying reviews
    using LLM analysis to generate comprehensive pet profiles.
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the Review and Order Intelligence Agent."""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.order_data = None
        self.review_data = None
    
    def load_data(self, order_history_path: str, qualifying_reviews_path: str) -> bool:
        """Load order history and qualifying reviews data from CSV files."""
        try:
            logger.info("Loading order history and review data...")
            self.order_data = pd.read_csv(order_history_path)
            self.review_data = pd.read_csv(qualifying_reviews_path)
            logger.info(f"Loaded {len(self.order_data)} order records")
            logger.info(f"Loaded {len(self.review_data)} review records")
            self._validate_data()
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def _validate_data(self) -> None:
        """Validate that required columns exist in the data."""
        required_order_cols = ['CustomerID', 'ProductID', 'ProductName']
        required_review_cols = ['CustomerID', 'PetName']
        missing_order_cols = [col for col in required_order_cols if col not in self.order_data.columns]
        missing_review_cols = [col for col in required_review_cols if col not in self.review_data.columns]
        if missing_order_cols:
            raise ValueError(f"Missing required columns in order history: {missing_order_cols}")
        if missing_review_cols:
            raise ValueError(f"Missing required columns in reviews: {missing_review_cols}")
    
    def _get_customer_pets(self, customer_id: str) -> List[str]:
        """Get all pets for a customer, including those mentioned in reviews but not registered."""
        if self.review_data is None:
            return []
        
        # Get registered pets from the data
        customer_reviews = self.review_data[self.review_data['CustomerID'].astype(str) == str(customer_id)]
        registered_pets = customer_reviews['PetName'].dropna().unique().tolist()
        
        # Look for additional pets mentioned in review text
        additional_pets = self._detect_additional_pets_from_reviews(customer_reviews)
        
        # Combine and remove duplicates
        all_pets = list(set(registered_pets + additional_pets))
        
        return all_pets
    
    def _detect_additional_pets_from_reviews(self, customer_reviews: pd.DataFrame) -> List[str]:
        """Detect additional pets mentioned in review text that aren't in registered profiles."""
        additional_pets = []
        
        for _, review in customer_reviews.iterrows():
            review_text = review['ReviewText'].lower()
            
            # Look for patterns indicating multiple pets
            if 'three cats' in review_text or '3 cats' in review_text:
                # This suggests there's a third cat not in the registered profiles
                # Since we don't know the actual name, use "UNK"
                if 'UNK' not in additional_pets:
                    additional_pets.append('UNK')
            
            elif 'four cats' in review_text or '4 cats' in review_text:
                if 'UNK' not in additional_pets:
                    additional_pets.append('UNK')
            
            elif 'five cats' in review_text or '5 cats' in review_text:
                if 'UNK' not in additional_pets:
                    additional_pets.append('UNK')
            
            # Similar patterns for dogs
            elif 'three dogs' in review_text or '3 dogs' in review_text:
                if 'UNK' not in additional_pets:
                    additional_pets.append('UNK')
            
            elif 'four dogs' in review_text or '4 dogs' in review_text:
                if 'UNK' not in additional_pets:
                    additional_pets.append('UNK')
            
            # Look for specific pet names mentioned in reviews
            # This is a simple pattern - in a real system, you might use NER
            import re
            pet_mentions = re.findall(r'\b(my|the)\s+(\w+)\b', review_text)
            for _, potential_pet in pet_mentions:
                if len(potential_pet) > 2 and potential_pet not in additional_pets:
                    # Simple heuristic: if it's capitalized in the original text, it might be a pet name
                    original_text = review['ReviewText']
                    if potential_pet.title() in original_text or potential_pet.upper() in original_text:
                        additional_pets.append(potential_pet.title())
        
        return additional_pets
    
    def _get_pet_reviews(self, customer_id: str, pet_name: str) -> pd.DataFrame:
        """Get reviews for a specific pet, handling both registered and unregistered pets."""
        if self.review_data is None:
            return pd.DataFrame()
        
        customer_reviews = self.review_data[self.review_data['CustomerID'].astype(str) == str(customer_id)]
        
        # For registered pets, get their specific reviews
        if pet_name in customer_reviews['PetName'].values:
            pet_reviews = customer_reviews[customer_reviews['PetName'] == pet_name]
        else:
            # For unregistered pets (like "UNK"), use all customer reviews
            # This allows the LLM to analyze the overall context and infer information
            pet_reviews = customer_reviews.copy()
            if pet_name == 'UNK':
                logger.info(f"Using all customer reviews for unregistered pet (name unknown)")
            else:
                logger.info(f"Using all customer reviews for unregistered pet: {pet_name}")
        
        return pet_reviews
    
    def _get_customer_orders(self, customer_id: str) -> pd.DataFrame:
        """Get all orders for a specific customer."""
        if self.order_data is None:
            return pd.DataFrame()
        return self.order_data[self.order_data['CustomerID'].astype(str) == str(customer_id)]
    
    def _select_priority_reviews(self, pet_reviews: pd.DataFrame, max_priority: int = 10, max_other: int = 5) -> List[str]:
        """Select and prioritize reviews mentioning gender/weight/size, plus a few others for context."""
        priority_reviews, other_reviews = [], []
        keywords = ['girl', 'boy', 'female', 'male', 'she', 'he', 'lbs', 'pound', 'weight', 'large breed', 'small breed']
        for _, review in pet_reviews.iterrows():
            review_text = review.get('ReviewText', '')
            if any(word in review_text.lower() for word in keywords):
                priority_reviews.append(review_text)
            else:
                other_reviews.append(review_text)
        selected = priority_reviews[:max_priority] + other_reviews[:max_other]
        return selected
    
    def _prepare_llm_context(self, pet_reviews: pd.DataFrame, customer_orders: pd.DataFrame, pet_name: str, structured_pet_data: Dict[str, Any] = None) -> str:
        """Prepare context data for LLM analysis."""
        context_parts = []
        
        # Add structured pet data that's already available
        if structured_pet_data and pet_name != 'UNK':
            # Use the structured pet data passed from the pipeline
            context_parts.append(f"Pet Profile Data for {pet_name}:")
            context_parts.append(f"- Pet Type: {structured_pet_data.get('PetType', 'UNK')}")
            context_parts.append(f"- Breed: {structured_pet_data.get('PetBreed', structured_pet_data.get('Breed', 'UNK'))}")
            context_parts.append(f"- Gender: {structured_pet_data.get('Gender', 'UNK')}")
            context_parts.append(f"- Life Stage: {structured_pet_data.get('PetAge', structured_pet_data.get('LifeStage', 'UNK'))}")
            context_parts.append(f"- Size Category: {structured_pet_data.get('SizeCategory', 'UNK')}")
            context_parts.append(f"- Weight: {structured_pet_data.get('Weight', 'UNK')}")
            context_parts.append(f"- Birthday: {structured_pet_data.get('Birthday', 'UNK')}")
            context_parts.append("")
        elif not pet_reviews.empty and pet_name != 'UNK':
            # Fallback: try to get pet data from reviews (old method)
            try:
                pet_data = pet_reviews.iloc[0]
                context_parts.append(f"Pet Profile Data for {pet_name}:")
                context_parts.append(f"- Pet Type: {pet_data.get('PetType', 'UNK')}")
                context_parts.append(f"- Breed: {pet_data.get('Breed', 'UNK')}")
                context_parts.append(f"- Gender: {pet_data.get('Gender', 'UNK')}")
                context_parts.append(f"- Life Stage: {pet_data.get('LifeStage', 'UNK')}")
                context_parts.append(f"- Size Category: {pet_data.get('SizeCategory', 'UNK')}")
                context_parts.append(f"- Weight: {pet_data.get('Weight', 'UNK')}")
                context_parts.append(f"- Birthday: {pet_data.get('Birthday', 'UNK')}")
                context_parts.append("")
            except Exception as e:
                logger.warning(f"Could not extract pet data from reviews for {pet_name}: {e}")
                context_parts.append(f"Pet Profile Data for {pet_name}:")
                context_parts.append("- Pet Type: UNK")
                context_parts.append("- Breed: UNK")
                context_parts.append("- Gender: UNK")
                context_parts.append("- Life Stage: UNK")
                context_parts.append("- Size Category: UNK")
                context_parts.append("- Weight: UNK")
                context_parts.append("- Birthday: UNK")
                context_parts.append("")
        elif pet_name == 'UNK':
            context_parts.append(f"Pet Profile Data for {pet_name}:")
            context_parts.append("- Pet Type: UNK")
            context_parts.append("- Breed: UNK")
            context_parts.append("- Gender: UNK")
            context_parts.append("- Life Stage: UNK")
            context_parts.append("- Size Category: UNK")
            context_parts.append("- Weight: UNK")
            context_parts.append("- Birthday: UNK")
            context_parts.append("")
            context_parts.append("NOTE: This pet is mentioned in reviews but has no registered profile data.")
            context_parts.append("")
        else:
            # No structured data available
            context_parts.append(f"Pet Profile Data for {pet_name}:")
            context_parts.append("- Pet Type: UNK")
            context_parts.append("- Breed: UNK")
            context_parts.append("- Gender: UNK")
            context_parts.append("- Life Stage: UNK")
            context_parts.append("- Size Category: UNK")
            context_parts.append("- Weight: UNK")
            context_parts.append("- Birthday: UNK")
            context_parts.append("")
            context_parts.append("NOTE: No structured profile data available for this pet.")
            context_parts.append("")
        
        # Add pet reviews context - prioritize reviews with gender/weight information
        if not pet_reviews.empty:
            context_parts.append(f"Pet Reviews for {pet_name}:")
            
            # For UNK pets, only include reviews that mention "three cats" or similar
            if pet_name == 'UNK':
                relevant_reviews = []
                for _, review in pet_reviews.iterrows():
                    review_text = review.get('ReviewText', '').lower()
                    if 'three cats' in review_text or '3 cats' in review_text:
                        relevant_reviews.append(review)
                
                if relevant_reviews:
                    for i, review in enumerate(relevant_reviews[:10]):
                        context_parts.append(f"Review {i+1}: {review.get('ReviewText', '')}")
                else:
                    context_parts.append("No specific reviews mentioning this pet found.")
            else:
                # For registered pets, use all their reviews
                # First, add reviews that mention gender/weight information
                priority_reviews = []
                other_reviews = []
                
                for _, review in pet_reviews.iterrows():
                    review_text = review.get('ReviewText', '')
                    if any(word in review_text.lower() for word in ['girl', 'boy', 'female', 'male', 'she', 'he', 'her', 'his', 'lbs', 'pounds', 'weight', 'large', 'small', 'breed']):
                        priority_reviews.append(review)
                    else:
                        other_reviews.append(review)
                
                # Add priority reviews first (up to 10)
                for i, review in enumerate(priority_reviews[:10]):
                    context_parts.append(f"Review {i+1}: {review.get('ReviewText', '')}")
                
                # Add other reviews if we have space (up to 10 total)
                remaining_slots = 10 - len(priority_reviews[:10])
                for i, review in enumerate(other_reviews[:remaining_slots]):
                    context_parts.append(f"Review {len(priority_reviews[:10])+i+1}: {review.get('ReviewText', '')}")
        
        # Add customer order context - filter by pet-appropriate products
        if not customer_orders.empty:
            context_parts.append(f"\nCustomer Order History:")
            
            # Determine pet type for filtering
            pet_type = "UNK"
            if structured_pet_data and structured_pet_data.get('PetType') and structured_pet_data.get('PetType') != 'UNK':
                pet_type = structured_pet_data.get('PetType')
            elif not pet_reviews.empty and pet_name != 'UNK':
                try:
                    pet_type = pet_reviews.iloc[0].get('PetType', 'UNK')
                except Exception:
                    pet_type = "UNK"
            elif pet_name == 'UNK':
                # For UNK pets, infer from context (reviews mention "three cats")
                pet_type = "Cat"
            
            # Filter orders by pet-appropriate products
            filtered_orders = customer_orders.copy()
            if pet_type == "Cat":
                # For cats, exclude dog-specific products
                cat_orders = customer_orders[~customer_orders['ProductName'].str.contains('Dog|dog', case=False, na=False)]
                filtered_orders = cat_orders
                context_parts.append("(Filtered to cat-appropriate products only - excluding dog products)")
            elif pet_type == "Dog":
                # For dogs, exclude cat-specific products
                dog_orders = customer_orders[~customer_orders['ProductName'].str.contains('Cat|cat', case=False, na=False)]
                filtered_orders = dog_orders
                context_parts.append("(Filtered to dog-appropriate products only - excluding cat products)")
            else:
                # For unknown pet types, include all products
                context_parts.append("(All products included - pet type unknown)")
            
            # Group by product and get top ordered products
            if not filtered_orders.empty:
                product_counts = filtered_orders.groupby('ProductName')['Quantity'].sum().sort_values(ascending=False)
                
                context_parts.append(f"Total products in filtered list: {len(filtered_orders)}")
                for i, (product, quantity) in enumerate(product_counts.head(10).items()):
                    context_parts.append(f"Product {i+1}: {product} (Quantity: {quantity})")
            else:
                context_parts.append("No pet-appropriate products found in order history.")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, context: str, pet_name: str) -> str:
        """Create the analysis prompt for the LLM."""
        unk_warning = ""
        if pet_name == 'UNK':
            unk_warning = """

CRITICAL WARNING FOR UNK PETS:
- This pet has NO structured profile data
- All structured fields (Breed, Gender, Birthday, etc.) should be "UNK" with score 0.0
- Only extract information that is EXPLICITLY mentioned in the review text
- DO NOT infer or guess any characteristics
- DO NOT use information from other pets' profiles
- If no specific information is found in reviews, use "UNK" with score 0.0
"""
        
        return f"""
Analyze the following data for pet '{pet_name}' and provide insights in JSON format:

{context}{unk_warning}

IMPORTANT EXTRACTION GUIDELINES:
- USE THE STRUCTURED DATA PROVIDED: If the "Pet Profile Data" section shows specific values (like Breed: Birman, Gender: MALE), use those exact values with high confidence scores (0.9-1.0)
- GENDER: Look for words like "girl", "boy", "female", "male", "she", "he", "her", "his" in the review text, OR use the structured data if provided
- WEIGHT: Look for numbers followed by "lbs", "pounds", "weight" in the review text
- BREED: Use the structured data if provided (e.g., "Birman", "Himalayan"), OR look for breed mentions in review text
- SIZE: Infer from weight and breed information (e.g., "large breed", "125 lbs" = "Large")
- PET TYPE: Use the structured data if provided, otherwise infer from context
- MOST ORDERED PRODUCTS: ONLY include products that are appropriate for the pet type. The order history has been pre-filtered to show only pet-appropriate products:
  * For CATS: Only include cat food, cat litter, cat toys, cat treats, cat flea treatment, etc.
  * For DOGS: Only include dog food, dog treats, dog toys, dog dental chews, dog flea treatment, etc.
  * DO NOT include dog products for cats or cat products for dogs
  * DO NOT include generic products that could be for either pet type unless clearly specified
  * CRITICAL: Only categorize products that are actually listed in the "Customer Order History" section above

Please analyze and return a JSON object with the following structure:
{{
    "PetType": "string",
    "PetTypeScore": float,
    "Breed": "string", 
    "BreedScore": float,
    "LifeStage": "string",
    "LifeStageScore": float,
    "Gender": "string",
    "GenderScore": float,
    "SizeCategory": "string",
    "SizeScore": float,
    "Weight": "string",
    "WeightScore": float,
    "Birthday": "string",
    "BirthdayScore": float,
    "PersonalityTraits": ["string"],
    "PersonalityScores": {{"trait": float}},
    "FavoriteProductCategories": ["string"],
    "CategoryScores": {{"category": float}},
    "BrandPreferences": ["string"],
    "BrandScores": {{"brand": float}},
    "DietaryPreferences": ["string"],
    "DietaryScores": {{"preference": float}},
    "BehavioralCues": ["string"],
    "BehavioralScores": {{"behavior": float}},
    "HealthMentions": ["string"],
    "HealthScores": {{"health": float}},
    "MostOrderedProducts": ["string"]
}}

IMPORTANT: If structured data is provided (e.g., Breed: Birman, Gender: MALE), use those exact values with high confidence scores (0.9-1.0). Only use "UNK" if the information is truly not available.
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured format."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_response = json.loads(json_str)
                
                # Post-process to fix product categorization issues
                parsed_response = self._fix_product_categorization(parsed_response)
                
                return parsed_response
            else:
                logger.warning("No JSON found in LLM response")
                return self._get_default_insights()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            return self._get_default_insights()
    
    def _fix_product_categorization(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Fix product categorization to ensure pets only get appropriate products."""
        pet_type = parsed_response.get('PetType', '').lower()
        
        if pet_type == 'dog':
            # For dogs, remove cat-specific categories
            favorite_categories = parsed_response.get('FavoriteProductCategories', [])
            category_scores = parsed_response.get('CategoryScores', {})
            
            # Remove cat-specific categories
            cat_keywords = ['cat', 'litter', 'hairball']
            filtered_categories = []
            filtered_scores = {}
            
            for category in favorite_categories:
                category_lower = category.lower()
                if not any(keyword in category_lower for keyword in cat_keywords):
                    filtered_categories.append(category)
                    if category in category_scores:
                        filtered_scores[category] = category_scores[category]
            
            parsed_response['FavoriteProductCategories'] = filtered_categories
            parsed_response['CategoryScores'] = filtered_scores
            
        elif pet_type == 'cat':
            # For cats, remove dog-specific categories
            favorite_categories = parsed_response.get('FavoriteProductCategories', [])
            category_scores = parsed_response.get('CategoryScores', {})
            
            # Remove dog-specific categories
            dog_keywords = ['dog', 'poop']
            filtered_categories = []
            filtered_scores = {}
            
            for category in favorite_categories:
                category_lower = category.lower()
                if not any(keyword in category_lower for keyword in dog_keywords):
                    filtered_categories.append(category)
                    if category in category_scores:
                        filtered_scores[category] = category_scores[category]
            
            parsed_response['FavoriteProductCategories'] = filtered_categories
            parsed_response['CategoryScores'] = filtered_scores
        
        return parsed_response
    
    def _analyze_pet_attributes_with_llm(self, pet_reviews: pd.DataFrame, customer_orders: pd.DataFrame, pet_name: str, structured_pet_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use LLM to analyze pet attributes from reviews and orders."""
        if not self.openai_api_key:
            logger.warning("No OpenAI API key provided, using fallback analysis")
            return self._fallback_analysis(pet_reviews, customer_orders, pet_name)
        try:
            context = self._prepare_llm_context(pet_reviews, customer_orders, pet_name, structured_pet_data)
            prompt = self._create_analysis_prompt(context, pet_name)
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert pet behavior analyst. Analyze the provided data to extract pet insights. IMPORTANT: If structured pet data is provided (like Breed, Gender, Pet Type), use those exact values with high confidence scores (0.9-1.0). Only extract additional information from review text when structured data is not available. Look for clues like 'girl', 'boy', '125 lbs', 'large breed', etc. in review text for additional insights. Only use information present in the data. If information is not available, use 'UNK' and score 0. CRITICAL: When categorizing products, ONLY assign products that are appropriate for the pet type. Dogs should only have dog products, cats should only have cat products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            llm_response = response.choices[0].message.content
            return self._parse_llm_response(llm_response)
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return self._fallback_analysis(pet_reviews, customer_orders, pet_name)
    
    def _fallback_analysis(self, pet_reviews: pd.DataFrame, customer_orders: pd.DataFrame, pet_name: str) -> Dict[str, Any]:
        """Fallback analysis when LLM is not available. Only uses structured fields, not review text."""
        insights = self._get_default_insights()
        if not pet_reviews.empty:
            first_review = pet_reviews.iloc[0]
            for attr in ['PetType', 'Breed', 'LifeStage', 'Gender', 'SizeCategory', 'Weight', 'Birthday']:
                if attr in first_review and pd.notna(first_review[attr]):
                    insights[attr] = str(first_review[attr])
                    insights[f"{attr}Score"] = 0.8
        if not customer_orders.empty:
            product_counts = customer_orders['ProductName'].value_counts()
            most_ordered = [product for product, count in product_counts.items() if count > 5]
            insights['MostOrderedProducts'] = most_ordered[:5]
        return insights
    
    def _get_default_insights(self) -> Dict[str, Any]:
        """Get default insights structure with UNK values."""
        return {
            "PetType": "UNK", "PetTypeScore": 0.0,
            "Breed": "UNK", "BreedScore": 0.0,
            "LifeStage": "UNK", "LifeStageScore": 0.0,
            "Gender": "UNK", "GenderScore": 0.0,
            "SizeCategory": "UNK", "SizeScore": 0.0,
            "Weight": "UNK", "WeightScore": 0.0,
            "Birthday": "UNK", "BirthdayScore": 0.0,
            "PersonalityTraits": [], "PersonalityScores": {},
            "FavoriteProductCategories": [], "CategoryScores": {},
            "BrandPreferences": [], "BrandScores": {},
            "DietaryPreferences": [], "DietaryScores": {},
            "BehavioralCues": [], "BehavioralScores": {},
            "HealthMentions": [], "HealthScores": {},
            "MostOrderedProducts": []
        }
    
    def process_customer_data(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Process all customer data and generate enriched pet insights."""
        logger.info("Starting customer data processing...")
        if self.review_data is None or self.order_data is None:
            logger.error("Data not loaded. Please load data first.")
            return {}
        results = {}
        unique_customers = self.review_data['CustomerID'].unique()
        for customer_id in unique_customers:
            try:
                logger.info(f"Processing customer {customer_id}...")
                customer_pets = self._get_customer_pets(str(customer_id))
                if not customer_pets:
                    logger.warning(f"No pets found for customer {customer_id}")
                    continue
                customer_orders = self._get_customer_orders(str(customer_id))
                customer_results = {}
                for pet_name in customer_pets:
                    logger.info(f"Analyzing pet {pet_name} for customer {customer_id}...")
                    pet_reviews = self._get_pet_reviews(str(customer_id), pet_name)
                    insights = self._analyze_pet_attributes_with_llm(pet_reviews, customer_orders, pet_name)
                    pet_insight = {
                        "PetType": insights.get("PetType", "UNK"),
                        "PetTypeScore": insights.get("PetTypeScore", 0.0),
                        "Breed": insights.get("Breed", "UNK"),
                        "BreedScore": insights.get("BreedScore", 0.0),
                        "LifeStage": insights.get("LifeStage", "UNK"),
                        "LifeStageScore": insights.get("LifeStageScore", 0.0),
                        "Gender": insights.get("Gender", "UNK"),
                        "GenderScore": insights.get("GenderScore", 0.0),
                        "SizeCategory": insights.get("SizeCategory", "UNK"),
                        "SizeScore": insights.get("SizeScore", 0.0),
                        "Weight": insights.get("Weight", "UNK"),
                        "WeightScore": insights.get("WeightScore", 0.0),
                        "Birthday": insights.get("Birthday", "UNK"),
                        "BirthdayScore": insights.get("BirthdayScore", 0.0),
                        "PersonalityTraits": insights.get("PersonalityTraits", []),
                        "PersonalityScores": insights.get("PersonalityScores", {}),
                        "FavoriteProductCategories": insights.get("FavoriteProductCategories", []),
                        "CategoryScores": insights.get("CategoryScores", {}),
                        "BrandPreferences": insights.get("BrandPreferences", []),
                        "BrandScores": insights.get("BrandScores", {}),
                        "DietaryPreferences": insights.get("DietaryPreferences", []),
                        "DietaryScores": insights.get("DietaryScores", {}),
                        "BehavioralCues": insights.get("BehavioralCues", []),
                        "BehavioralScores": insights.get("BehavioralScores", {}),
                        "HealthMentions": insights.get("HealthMentions", []),
                        "HealthScores": insights.get("HealthScores", {}),
                        "MostOrderedProducts": insights.get("MostOrderedProducts", [])
                    }
                    customer_results[pet_name] = pet_insight
                results[str(customer_id)] = customer_results
            except Exception as e:
                logger.error(f"Error processing customer {customer_id}: {e}")
                continue
        logger.info(f"Completed processing {len(results)} customers")
        return results
    
    def save_results(self, results: Dict[str, Dict[str, Dict[str, Any]]], output_path: str) -> bool:
        """Save results to JSON file."""
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False
    
    def generate_summary_report(self, results: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate a summary report of the processing results."""
        if not results:
            return {
                'total_customers': 0,
                'total_pets': 0,
                'average_confidence': 0.0,
                'pets_with_complete_data': 0
            }
        total_customers = len(results)
        total_pets = sum(len(pets) for pets in results.values())
        all_scores = []
        pets_with_complete_data = 0
        for customer_pets in results.values():
            for pet_insights in customer_pets.values():
                scores = [
                    pet_insights.get('PetTypeScore', 0),
                    pet_insights.get('BreedScore', 0),
                    pet_insights.get('LifeStageScore', 0),
                    pet_insights.get('GenderScore', 0),
                    pet_insights.get('SizeScore', 0),
                    pet_insights.get('WeightScore', 0),
                    pet_insights.get('BirthdayScore', 0)
                ]
                all_scores.extend(scores)
                if any(score > 0.5 for score in scores):
                    pets_with_complete_data += 1
        average_confidence = sum(all_scores) / len(all_scores) if all_scores else 0.0
        return {
            'total_customers': total_customers,
            'total_pets': total_pets,
            'average_confidence': average_confidence,
            'pets_with_complete_data': pets_with_complete_data
        }

if __name__ == "__main__":
    """Example usage of the Review and Order Intelligence Agent."""
    print("🧠 Review and Order Intelligence Agent - Example Usage")
    print("=" * 60)
    
    try:
        agent = ReviewOrderIntelligenceAgent()
        
        data_loaded = agent.load_data(
            order_history_path="dummy_orderhistory.csv",
            qualifying_reviews_path="dummy_qualifyingreviews.csv"
        )
        
        if not data_loaded:
            print("❌ Failed to load data")
            exit(1)
        
        results = agent.process_customer_data()
        success = agent.save_results(results, "output/pet_insights.json")
        
        if success:
            print(f"✅ Results saved to output/pet_insights.json")
        
        summary = agent.generate_summary_report(results)
        print(f"\n📊 Processing Summary:")
        print(f"Total Customers: {summary['total_customers']}")
        print(f"Total Pets: {summary['total_pets']}")
        print(f"Average Confidence: {summary['average_confidence']:.3f}")
        print(f"Pets with Complete Data: {summary['pets_with_complete_data']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please ensure all required CSV files are present.") 