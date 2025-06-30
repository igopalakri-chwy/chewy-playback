import json
import os
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceScoreCalculator:
    """
    Utility class to add confidence scores to the JSON output from the Review and Order Intelligence Agent.
    Calculates the average of all individual scores for each pet and adds it as a confidence_score field.
    """
    
    def __init__(self):
        """Initialize the Confidence Score Calculator."""
        self.score_fields = [
            'PetTypeScore',
            'BreedScore', 
            'LifeStageScore',
            'GenderScore',
            'SizeScore',
            'WeightScore',
            'BirthdayScore'
        ]
    
    def calculate_confidence_score(self, pet_data: Dict[str, Any]) -> float:
        """
        Calculate the average confidence score for a pet based on all available scores.
        
        Args:
            pet_data: Dictionary containing pet insights with various score fields
            
        Returns:
            float: Average confidence score (0.0 to 1.0)
        """
        scores = []
        
        # Collect all available scores
        for score_field in self.score_fields:
            if score_field in pet_data:
                score = pet_data[score_field]
                if isinstance(score, (int, float)) and score >= 0:
                    scores.append(score)
        
        # Calculate average
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.0
    
    def add_confidence_scores_to_json(self, input_path: str, output_path: str = None) -> bool:
        """
        Read JSON file, add confidence scores to each pet, and save the updated JSON.
        
        Args:
            input_path: Path to the input JSON file
            output_path: Path to save the updated JSON file (optional, defaults to input_path)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the input JSON file
            logger.info(f"Reading JSON file from: {input_path}")
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Process each pet (the structure has pets as direct keys)
            total_pets = 0
            total_confidence = 0.0
            pet_confidence_scores = []
            
            # Handle both nested structure (customer_id -> pets) and direct structure (pet_name -> data)
            if isinstance(data, dict):
                # Check if this is a nested structure with customer IDs
                if any(isinstance(value, dict) and 'PetType' in value for value in data.values()):
                    # This is the direct structure (pet_name -> data)
                    for pet_name, pet_data in data.items():
                        if isinstance(pet_data, dict) and 'PetType' in pet_data:
                            # Calculate confidence score for this pet
                            confidence_score = self.calculate_confidence_score(pet_data)
                            
                            # Add confidence score to pet data
                            pet_data['confidence_score'] = confidence_score
                            
                            total_pets += 1
                            total_confidence += confidence_score
                            pet_confidence_scores.append(confidence_score)
                            
                            logger.info(f"Pet {pet_name}: confidence_score = {confidence_score:.3f}")
                    
                    # Calculate customer confidence score as average of all pet confidence scores
                    if pet_confidence_scores:
                        customer_confidence_score = sum(pet_confidence_scores) / len(pet_confidence_scores)
                        data['cust_confidence_score'] = customer_confidence_score
                        logger.info(f"Customer confidence score: {customer_confidence_score:.3f}")
                    
                else:
                    # This might be a nested structure (customer_id -> pets)
                    for customer_id, customer_pets in data.items():
                        if isinstance(customer_pets, dict):
                            customer_pet_scores = []
                            for pet_name, pet_data in customer_pets.items():
                                if isinstance(pet_data, dict) and 'PetType' in pet_data:
                                    # Calculate confidence score for this pet
                                    confidence_score = self.calculate_confidence_score(pet_data)
                                    
                                    # Add confidence score to pet data
                                    pet_data['confidence_score'] = confidence_score
                                    
                                    total_pets += 1
                                    total_confidence += confidence_score
                                    customer_pet_scores.append(confidence_score)
                                    
                                    logger.info(f"Customer {customer_id}, Pet {pet_name}: confidence_score = {confidence_score:.3f}")
                            
                            # Calculate customer confidence score for this customer
                            if customer_pet_scores:
                                customer_confidence_score = sum(customer_pet_scores) / len(customer_pet_scores)
                                customer_pets['cust_confidence_score'] = customer_confidence_score
                                logger.info(f"Customer {customer_id} confidence score: {customer_confidence_score:.3f}")
            
            # Calculate overall average confidence
            overall_average = total_confidence / total_pets if total_pets > 0 else 0.0
            logger.info(f"Processed {total_pets} pets with overall average confidence: {overall_average:.3f}")
            
            # Determine output path
            if output_path is None:
                output_path = input_path
            
            # Save the updated JSON
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Updated JSON saved to: {output_path}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def process_json_file(self, json_file_path: str, backup_original: bool = True) -> bool:
        """
        Process a JSON file by adding confidence scores and optionally backing up the original.
        
        Args:
            json_file_path: Path to the JSON file to process
            backup_original: Whether to create a backup of the original file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup if requested
            if backup_original and os.path.exists(json_file_path):
                backup_path = f"{json_file_path}.backup"
                import shutil
                shutil.copy2(json_file_path, backup_path)
                logger.info(f"Created backup at: {backup_path}")
            
            # Process the file
            return self.add_confidence_scores_to_json(json_file_path)
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return False

def main():
    """Main function to demonstrate usage."""
    print("🎯 Confidence Score Calculator")
    print("=" * 40)
    
    # Example usage
    calculator = ConfidenceScoreCalculator()
    
    # You can specify the input file path here
    input_file = "output/pet_insights.json"  # Default path from the agent
    
    if os.path.exists(input_file):
        print(f"Processing file: {input_file}")
        success = calculator.process_json_file(input_file)
        
        if success:
            print("✅ Successfully added confidence scores to the JSON file!")
        else:
            print("❌ Failed to process the JSON file")
    else:
        print(f"❌ File not found: {input_file}")
        print("Please ensure the JSON file exists or update the path in the script.")

if __name__ == "__main__":
    main() 