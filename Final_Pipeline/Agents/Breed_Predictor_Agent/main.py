"""
Main application for the Breed Predictor.
Interactive interface for predicting dog breeds based on purchase history.
Updated to work with processed order data from predictorData.csv.
"""

import os
import sys
import json
from datetime import datetime
from predictor import BreedPredictor

def display_welcome():
    """Display welcome message and setup instructions."""
    print("DOG BREED PREDICTOR")
    print("=" * 50)
    print("Predict dog breeds based on Chewy purchase history!")
    print()
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("SETUP REQUIRED:")
        print("1. Get your OpenAI API key from: https://platform.openai.com/api-keys")
        print("2. Set it as environment variable: export OPENAI_API_KEY=your_key")
        print("3. Or create a .env file with: OPENAI_API_KEY=your_key")
        print()
        return False
    return True

def display_pet_summary(pet_data: dict) -> None:
    """Display a summary of pet information."""
    print(f"\nPET PROFILE:")
    print(f"   Name: {pet_data.get('name', 'Unknown')}")
    print(f"   Age: {pet_data.get('age', 'Unknown')} years")
    print(f"   Size: {pet_data.get('size', 'Unknown')}")
    print(f"   Gender: {pet_data.get('gender', 'Unknown')}")
    print(f"   Health Indicators: {', '.join(pet_data.get('health_indicators', [])) or 'None detected'}")
    print(f"   Total Orders: {len(pet_data.get('purchase_history', []))}")
    
    # Show purchase timeline
    purchase_history = pet_data.get('purchase_history', [])
    if purchase_history:
        first_order = purchase_history[0].get('order_date', 'Unknown')
        last_order = purchase_history[-1].get('order_date', 'Unknown')
        print(f"   Purchase Timeline: {first_order} to {last_order}")
        
        # Show top categories
        categories = {}
        for purchase in purchase_history:
            category = purchase.get('category', 'Other')
            categories[category] = categories.get(category, 0) + 1
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"   Top Purchase Categories: {', '.join([f'{cat} ({count})' for cat, count in top_categories])}")

def display_prediction_results(distribution: dict, breed_definitions: dict, explanations: dict) -> None:
    """Display breed prediction results with explanations."""
    print(f"\nBREED PREDICTION RESULTS:")
    print("=" * 40)
    
    sorted_breeds = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
    
    for i, (breed_key, percentage) in enumerate(sorted_breeds, 1):
        breed_info = breed_definitions.get(breed_key, {})
        breed_name = breed_info.get('name', breed_key.replace('_', ' ').title())
        
        # Create percentage bar
        bar_length = int(percentage / 5)  # Scale to fit display
        bar = "█" * bar_length + "░" * (20 - bar_length)
        
        print(f"{i}. {breed_name:<20} {percentage:6.1f}% [{bar}]")
        
        # Show explanation if available (for breeds >2% or top 4)
        if breed_key in explanations:
            print(f"   → {explanations[breed_key]}")
        
        # Add breed characteristics for top 3 (but not if we already showed explanation)
        elif i <= 3 and breed_info:
            characteristics = []
            if breed_info.get('size'):
                characteristics.append(f"Size: {breed_info['size']}")
            if breed_info.get('temperament'):
                characteristics.append(f"Temperament: {breed_info['temperament'][:50]}...")
            if characteristics:
                print(f"   {' | '.join(characteristics)}")
    
    # Summary
    top_breed = sorted_breeds[0]
    print(f"\nANALYSIS:")
    print(f"   Most Likely Breed: {breed_definitions.get(top_breed[0], {}).get('name', top_breed[0])} ({top_breed[1]:.1f}%)")
    print(f"   Confidence Level: {'High' if top_breed[1] > 40 else 'Medium' if top_breed[1] > 25 else 'Low'}")
    
    # Show explanation summary
    if explanations:
        print(f"   Explanations provided for {len(explanations)} top matching breeds")

def collect_user_feedback(customer_id: str, pet_id: str, pet_data: dict, distribution: dict, breed_definitions: dict) -> None:
    """Collect user feedback on prediction accuracy."""
    print("\n" + "=" * 60)
    print("FEEDBACK COLLECTION")
    print("=" * 60)
    print("Help us improve our predictions by providing feedback!")
    
    while True:
        answer = input("\nWas our prediction correct? (y/n/skip): ").lower().strip()
        
        if answer == 'skip':
            print("Feedback skipped. Thank you!")
            return
            
        elif answer in ['y', 'yes']:
            # Prediction was correct - let user select which breed was right
            sorted_breeds = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
            
            print("\nWhich of our predicted breeds was correct?")
            for i, (breed_key, percentage) in enumerate(sorted_breeds, 1):
                breed_name = breed_definitions.get(breed_key, {}).get('name', breed_key.replace('_', ' ').title())
                print(f"{i}. {breed_name} ({percentage:.1f}%)")
            
            while True:
                try:
                    choice = input(f"\nEnter breed number (1-{len(sorted_breeds)}): ").strip()
                    breed_index = int(choice) - 1
                    
                    if 0 <= breed_index < len(sorted_breeds):
                        correct_breed_key = sorted_breeds[breed_index][0]
                        correct_breed_name = breed_definitions.get(correct_breed_key, {}).get('name', correct_breed_key)
                        
                        save_feedback(customer_id, pet_id, pet_data, distribution, correct_breed_key, True)
                        print(f"Thank you! Recorded that {correct_breed_name} was correct.")
                        return
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
                    
        elif answer in ['n', 'no']:
            # Prediction was wrong - let user type the correct breed
            print("\nWhat is the actual breed of your dog?")
            print("(You can enter the full breed name, e.g., 'Golden Retriever', 'Mixed Breed', etc.)")
            
            actual_breed = input("Actual breed: ").strip()
            
            if actual_breed:
                # Try to find matching breed key
                actual_breed_key = find_matching_breed_key(actual_breed, breed_definitions)
                
                save_feedback(customer_id, pet_id, pet_data, distribution, actual_breed_key or actual_breed, False)
                print(f"Thank you! Recorded that the actual breed was {actual_breed}.")
                return
            else:
                print("Please enter a breed name.")
                
        else:
            print("Please enter 'y' for yes, 'n' for no, or 'skip' to skip feedback.")

def find_matching_breed_key(user_input: str, breed_definitions: dict) -> str:
    """Try to find a matching breed key from user input."""
    user_input_lower = user_input.lower().strip()
    
    # First try exact match with breed names
    for breed_key, breed_info in breed_definitions.items():
        breed_name = breed_info.get('name', '').lower()
        if breed_name == user_input_lower:
            return breed_key
    
    # Then try partial match
    for breed_key, breed_info in breed_definitions.items():
        breed_name = breed_info.get('name', '').lower()
        if user_input_lower in breed_name or breed_name in user_input_lower:
            return breed_key
    
    # Try matching with breed key format (e.g., "golden retriever" -> "goldenRetriever")
    formatted_input = ''.join(word.capitalize() for word in user_input_lower.split())
    formatted_input = formatted_input[0].lower() + formatted_input[1:] if formatted_input else ''
    
    if formatted_input in breed_definitions:
        return formatted_input
    
    return None

def save_feedback(customer_id: str, pet_id: str, pet_data: dict, distribution: dict, correct_breed: str, was_correct: bool) -> None:
    """Save user feedback to the feedback file."""
    feedback_file = 'data/user_feedback.json'
    
    # Create feedback entry
    feedback_entry = {
        "customer_id": customer_id,
        "pet_id": pet_id,
        "pet_characteristics": {
            "name": pet_data.get('name', 'Unknown'),
            "age": pet_data.get('age'),
            "size": pet_data.get('size'),
            "gender": pet_data.get('gender'),
            "health_indicators": pet_data.get('health_indicators', [])
        },
        "predictions": distribution,
        "correct_breed": correct_breed,
        "was_prediction_correct": was_correct,
        "timestamp": str(datetime.now())
    }
    
    # Load existing feedback
    try:
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
        else:
            feedback_data = []
    except Exception as e:
        print(f"Warning: Could not load existing feedback file: {e}")
        feedback_data = []
    
    # Add new feedback
    feedback_data.append(feedback_entry)
    
    # Save updated feedback
    try:
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save feedback: {e}")

def list_available_pets(customers: dict) -> list:
    """List all available pets and return as options."""
    pets = []
    print("\nAVAILABLE PETS:")
    print("-" * 50)
    
    for customer_id, customer_data in customers.items():
        customer_name = customer_data.get('customer_info', {}).get('name', f'Customer {customer_id}')
        for pet_id, pet_data in customer_data.get('pets', {}).items():
            pet_name = pet_data.get('name', 'Unknown')
            pet_age = pet_data.get('age', 'Unknown')
            pet_size = pet_data.get('size', 'Unknown')
            order_count = len(pet_data.get('purchase_history', []))
            
            pets.append((customer_id, pet_id, pet_data))
            print(f"{len(pets):2d}. {pet_name:<15} (Age: {pet_age}, Size: {pet_size}, Orders: {order_count}) - {customer_name}")
    
    return pets

def main():
    """Main application entry point."""
    
    if not display_welcome():
        return
    
    try:
        # Initialize the predictor
        print("Loading breed predictor...")
        predictor = BreedPredictor()
        customers, _ = predictor.load_data()
        
        print(f"Loaded data for {len(customers)} customers")
        total_pets = sum(len(c.get('pets', {})) for c in customers.values())
        print(f"Found {total_pets} pets with purchase history")
        print(f"Loaded {len(predictor.breed_definitions)} breed definitions")
        
        while True:
            print("\n" + "=" * 60)
            print("BREED PREDICTOR MENU")
            print("=" * 60)
            print("1. View all available pets")
            print("2. Predict breed for a specific pet")
            print("3. Exit")
            print("-" * 60)
            
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                pets = list_available_pets(customers)
                if not pets:
                    print("No pets found in the database.")
                    
            elif choice == '2':
                pets = list_available_pets(customers)
                
                if not pets:
                    print("No pets available for prediction.")
                    continue
                
                try:
                    pet_choice = input(f"\nEnter pet number (1-{len(pets)}): ").strip()
                    pet_index = int(pet_choice) - 1
                    
                    if 0 <= pet_index < len(pets):
                        customer_id, pet_id, pet_data = pets[pet_index]
                        
                        print(f"\nAnalyzing {pet_data.get('name', 'Unknown')}...")
                        display_pet_summary(pet_data)
                        
                        print(f"\nRunning breed prediction...")
                        distribution, confidence_result, explanations = predictor.predict_breed_distribution(customer_id, pet_id)
                        
                        display_prediction_results(distribution, predictor.breed_definitions, explanations)
                        
                        # Display confidence information
                        print(f"\nCONFIDENCE ASSESSMENT:")
                        print(f"- Overall Confidence: {confidence_result['confidence_score']}% ({confidence_result['confidence_level']})")
                        
                        if confidence_result['reliability_flags']:
                            print(f"- Reliability Issues: {', '.join(confidence_result['reliability_flags'])}")
                        
                        if confidence_result['confidence_score'] < 30:
                            print("WARNING: Very low confidence - predictions may be unreliable")
                        elif confidence_result['confidence_score'] < 50:
                            print("CAUTION: Low confidence - use predictions with care")
                        
                        # Show top recommendations
                        if confidence_result['recommendations']:
                            print(f"\nTOP RECOMMENDATIONS:")
                            for i, rec in enumerate(confidence_result['recommendations'][:2], 1):
                                print(f"{i}. {rec}")
                        
                        # Collect user feedback
                        collect_user_feedback(customer_id, pet_id, pet_data, distribution, predictor.breed_definitions)
                        
                    else:
                        print("Invalid pet number. Please try again.")
                        
                except ValueError:
                    print("Please enter a valid number.")
                except Exception as e:
                    print(f"Error during prediction: {e}")
                    print("This might be due to missing OpenAI API key or network issues.")
                    
            elif choice == '3':
                print("Thank you for using the Breed Predictor!")
                break
                
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    except FileNotFoundError as e:
        print(f"Error: Could not find required data files.")
        print(f"   Details: {e}")
        print("Make sure the data directory contains pet_data_1pet.json and breed definitions.")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main() 