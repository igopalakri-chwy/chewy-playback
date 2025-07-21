#!/usr/bin/env python3
"""
Food Consumption Analyzer
Parses pet food data from query_5 and provides fun weight comparisons
"""
import json
from typing import List, Dict, Any

def parse_food_data(food_data: List[Dict[str, Any]]) -> float:
    """
    Parse food consumption data from query_5 results.
    
    Args:
        food_data (List[Dict[str, Any]]): List of food consumption records from query_5
        
    Returns:
        float: Total food consumption in pounds
    """
    total_food_lbs = 0.0
    
    try:
        for row in food_data:
            # Check if total_food_lbs exists in the row
            if 'TOTAL_FOOD_LBS' in row and row['TOTAL_FOOD_LBS'] is not None:
                try:
                    total_food_lbs += float(row['TOTAL_FOOD_LBS'])
                except (ValueError, TypeError):
                    continue
        
        return total_food_lbs
    except Exception as e:
        print(f"Error parsing food data: {e}")
        return 0.0

def get_weight_range(weight: float) -> int:
    """Get the weight range for fun fact lookup."""
    return int(weight // 100) * 100

def get_fun_facts(weight_range: int) -> List[str]:
    """Get fun facts based on weight range."""
    facts_database = {
        0: [
            "That's about the weight of a large golden retriever!",
            "That's equivalent to about 400 hamburgers!",
            "That's about as much as a baby grand piano bench!"
        ],
        100: [
            "That's about the weight of a baby elephant!",
            "That's equivalent to roughly 1,600 apples!",
            "That's about as much as a large motorcycle!"
        ],
        200: [
            "That's about the weight of a young adult lion!",
            "That's equivalent to roughly 800 cans of soda!",
            "That's about as much as a large refrigerator!"
        ],
        300: [
            "That's about the weight of a small horse!",
            "That's equivalent to roughly 1,200 bananas!",
            "That's about as much as a grand piano!"
        ],
        400: [
            "That's about the weight of a young grizzly bear!",
            "That's equivalent to roughly 6,400 eggs!",
            "That's about as much as a small car!"
        ],
        500: [
            "That's about the weight of a large Arabian horse!",
            "That's equivalent to roughly 2,000 potatoes!",
            "That's about as much as a baby grand piano!"
        ],
        600: [
            "That's about the weight of a large dairy cow!",
            "That's equivalent to roughly 2,400 slices of bread!",
            "That's about as much as a small boat!"
        ],
        700: [
            "That's about the weight of a small car like a Smart Car!",
            "That's equivalent to roughly 2,800 oranges!",
            "That's about as much as a large motorcycle and rider!"
        ],
        800: [
            "That's about the weight of a large concert grand piano!",
            "That's equivalent to roughly 12,800 chicken nuggets!",
            "That's about as much as a small SUV!"
        ],
        900: [
            "That's about the weight of a small thoroughbred horse!",
            "That's equivalent to roughly 3,600 slices of pizza!",
            "That's about as much as a large hot tub (empty)!"
        ],
        1000: [
            "That's about the weight of a large bull!",
            "That's equivalent to roughly 16,000 tablespoons of peanut butter!",
            "That's about as much as a small sedan car!"
        ],
        1100: [
            "That's about the weight of a small boat with trailer!",
            "That's equivalent to roughly 4,400 hamburgers!",
            "That's about as much as a baby elephant!"
        ],
        1200: [
            "That's about the weight of a large riding lawn mower!",
            "That's equivalent to roughly 19,200 slices of cheese!",
            "That's about as much as a compact car!"
        ],
        1300: [
            "That's about the weight of a small pickup truck!",
            "That's equivalent to roughly 5,200 apples!",
            "That's about as much as a large spa/hot tub!"
        ],
        1400: [
            "That's about the weight of a large horse and rider!",
            "That's equivalent to roughly 22,400 chicken wings!",
            "That's about as much as a mid-size sedan!"
        ],
        1500: [
            "That's about the weight of a small elephant!",
            "That's equivalent to roughly 6,000 bananas!",
            "That's about as much as a large SUV!"
        ],
        1600: [
            "That's about the weight of a small adult elephant!",
            "That's equivalent to roughly 25,600 slices of pizza!",
            "That's about as much as a full-size pickup truck!"
        ],
        1700: [
            "That's about the weight of a large riding horse!",
            "That's equivalent to roughly 6,800 apples!",
            "That's about as much as a mid-size SUV!"
        ],
        1800: [
            "That's about the weight of a small car plus a motorcycle!",
            "That's equivalent to roughly 28,800 chicken nuggets!",
            "That's about as much as a large sedan!"
        ],
        1900: [
            "That's about the weight of a young adult elephant!",
            "That's equivalent to roughly 7,600 hamburgers!",
            "That's about as much as a small truck!"
        ],
        2000: [
            "That's about the weight of a full-grown male elephant!",
            "That's equivalent to roughly 32,000 tablespoons of peanut butter!",
            "That's about as much as a compact car!"
        ],
        2100: [
            "That's about the weight of a large adult male horse!",
            "That's equivalent to roughly 8,400 apples!",
            "That's about as much as a large pickup truck!"
        ],
        2200: [
            "That's about the weight of a small rhinoceros!",
            "That's equivalent to roughly 35,200 chicken nuggets!",
            "That's about as much as a mid-size truck!"
        ],
        2300: [
            "That's about the weight of a large grand piano plus a motorcycle!",
            "That's equivalent to roughly 9,200 hamburgers!",
            "That's about as much as a small boat and trailer!"
        ],
        2400: [
            "That's about the weight of a young adult hippopotamus!",
            "That's equivalent to roughly 38,400 slices of bread!",
            "That's about as much as a large SUV plus luggage!"
        ],
        2500: [
            "That's about the weight of a small adult rhinoceros!",
            "That's equivalent to roughly 10,000 bananas!",
            "That's about as much as a full-size truck with cargo!"
        ]
    }
    
    # Find the closest range
    closest_range = min(facts_database.keys(), key=lambda x: abs(x - weight_range))
    return facts_database.get(closest_range, [
        f"That's about {weight_range} pounds of pure pet love!",
        f"That's equivalent to a lot of happy meals!",
        f"That's about as much as... well, {weight_range} pounds!"
    ])

def analyze_food_consumption(food_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze food consumption data and return fun facts.
    
    Args:
        food_data (List[Dict[str, Any]]): Food consumption data from query_5
        
    Returns:
        Dict[str, Any]: Analysis results with fun facts
    """
    total_weight = parse_food_data(food_data)
    
    if total_weight <= 0:
        return {
            "total_food_lbs": 0.0,
            "weight_range": 0,
            "fun_facts": [
                "Your pets are just getting started on their food journey!",
                "Every great feast begins with a single kibble!",
                "The best is yet to come for your furry friends!"
            ],
            "message": "No food consumption data available yet."
        }
    
    weight_range = get_weight_range(total_weight)
    fun_facts = get_fun_facts(weight_range)
    
    return {
        "total_food_lbs": round(total_weight, 2),
        "weight_range": weight_range,
        "fun_facts": fun_facts,
        "message": f"Your pets have consumed {total_weight:.2f} pounds of food!"
    }

def generate_food_fun_fact_json(food_data: List[Dict[str, Any]]) -> str:
    """
    Generate a JSON string with food consumption analysis.
    
    Args:
        food_data (List[Dict[str, Any]]): Food consumption data from query_5
        
    Returns:
        str: JSON string with analysis results
    """
    analysis = analyze_food_consumption(food_data)
    return json.dumps(analysis, indent=2)

# For backward compatibility with the original script
def main():
    """Main function for standalone usage."""
    # This would be used if running the script directly
    # For pipeline integration, use generate_food_fun_fact_json()
    print("Food Consumption Analyzer - Use generate_food_fun_fact_json() for pipeline integration")

if __name__ == "__main__":
    main() 