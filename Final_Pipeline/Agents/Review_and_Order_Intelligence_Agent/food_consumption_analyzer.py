#!/usr/bin/env python3
"""
Food Consumption Analyzer with Location-Based Fun Facts
Parses pet food data and generates personalized fun facts based on location
"""
import json
import requests
from typing import List, Dict, Any, Tuple, Optional

def get_location_from_zip(zip_code: str) -> Tuple[str, str]:
    """
    Get city and state from zip code using a free API.
    Returns (city, state) tuple.
    """
    try:
        # Clean the zip code - extract first 5 digits if ZIP+4 format
        zip_code = zip_code.strip()
        if '-' in zip_code:
            zip_code = zip_code.split('-')[0]  # Take only the first 5 digits
        
        # Using the free zipcodeapi.com API (no key required for basic usage)
        url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            city = data['places'][0]['place name']
            state = data['places'][0]['state abbreviation']
            return city, state
        else:
            # Error: API failed to return location data
            raise ValueError(f"Failed to get location data for ZIP code {zip_code}. API returned status {response.status_code}.")
    except Exception as e:
        # Error: Network or other issues
        raise ValueError(f"Failed to get location data for ZIP code {zip_code}: {str(e)}")

def parse_food_data(food_data: List[Dict[str, Any]]) -> float:
    """
    Parse food consumption data from query results.
    
    Args:
        food_data (List[Dict[str, Any]]): List of food consumption records
        
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

def get_food_fun_fact(zip_code: str, total_lbs: float) -> str:
    """
    Generate a personalized fun fact based on pet food consumption and location.
    
    Args:
        zip_code: 5-digit zip code string
        total_lbs: Total food consumed in pounds
    
    Returns:
        Friendly message with location-based fun fact
    """
    # Get location from zip code
    city, state = get_location_from_zip(zip_code)
    
    # Determine tier based on food amount
    if total_lbs < 1:
        tier = 1
    elif total_lbs < 10:
        tier = 2
    elif total_lbs < 30:
        tier = 3
    elif total_lbs < 100:
        tier = 4
    else:
        tier = 5
    
    # Check if it's an iconic city
    iconic_cities = {
        'New York': {
            1: ("iPhones", 0.5),
            2: ("bowling balls", 8),
            3: ("microwave ovens", 25),
            4: ("small refrigerators", 60),
            5: ("grand pianos", 500)
        },
        'Los Angeles': {
            1: ("surfboards", 0.8),
            2: ("yoga mats", 3),
            3: ("beach umbrellas", 15),
            4: ("palm trees", 50),
            5: ("Hollywood sign letters", 300)
        },
        'Chicago': {
            1: ("Giordano's deep dish pizzas", 2),
            2: ("Chicago Bulls basketballs", 1.5),
            3: ("Chicago hot dog carts", 20),
            4: ("Chicago taxi cabs", 60),
            5: ("steel beams", 400)
        },
        'Miami': {
            1: ("fresh coconuts", 0.5),
            2: ("beach balls", 2),
            3: ("pink flamingos", 15),
            4: ("palm trees", 50),
            5: ("cruise ship anchors", 250)
        },
        'Las Vegas': {
            1: ("casino decks of cards", 0.1),
            2: ("slot machines", 5),
            3: ("roulette wheels", 25),
            4: ("poker tables", 60),
            5: ("Bellagio chandeliers", 200)
        },
        'Seattle': {
            1: ("Starbucks coffee cups", 0.5),
            2: ("REI rain jackets", 2),
            3: ("Fender guitars", 15),
            4: ("mountain bikes", 50),
            5: ("kayaks", 200)
        },
        'Austin': {
            1: ("guitar picks", 0.01),
            2: ("cowboy hats", 2),
            3: ("Texas barbecue grills", 25),
            4: ("Austin food trucks", 60),
            5: ("electric guitars", 300)
        },
        'Nashville': {
            1: ("guitar strings", 0.05),
            2: ("Lucchese cowboy boots", 2),
            3: ("banjos", 15),
            4: ("honky-tonk pianos", 50),
            5: ("steel guitars", 200)
        },
        'New Orleans': {
            1: ("Café du Monde beignets", 0.1),
            2: ("jazz trumpets", 2),
            3: ("Mardi Gras masks", 0.5),
            4: ("St. Charles streetcars", 50),
            5: ("streetcar benches", 200)
        },
        'Portland': {
            1: ("craft beer growlers", 0.5),
            2: ("bicycles", 25),
            3: ("Portland food carts", 20),
            4: ("Stumptown coffee roasters", 50),
            5: ("bicycle racks", 200)
        }
    }
    
    # State fun facts dictionary - Complete 50-state coverage
    state_facts = {
        'AL': {  # Alabama
            1: ("football helmets", 0.5),
            2: ("barbecue smokers", 8),
            3: ("fishing boats", 25),
            4: ("cotton bales", 50),
            5: ("Two Alabama Linebackers", 500)
        },
        'AK': {  # Alaska
            1: ("snowflakes", 0.001),
            2: ("fishing rods", 2),
            3: ("sled dogs", 15),
            4: ("moose", 50),
            5: ("glacier chunks", 200)
        },
        'AZ': {  # Arizona
            1: ("cacti", 0.5),
            2: ("hiking boots", 2),
            3: ("mountain bikes", 25),
            4: ("saguaro cacti", 50),
            5: ("Grand Canyon rocks", 200)
        },
        'AR': {  # Arkansas
            1: ("diamonds", 0.01),
            2: ("fishing lures", 0.5),
            3: ("duck calls", 0.3),
            4: ("rice silos", 50),
            5: ("hot tubs", 50)
        },
        'CA': {  # California
            1: ("surfboards", 8),
            2: ("Napa Valley wine bottles", 3),
            3: ("redwood saplings", 25),
            4: ("Hollywood cameras", 50),
            5: ("surfboards", 300)
        },
        'CO': {  # Colorado
            1: ("ski lift tickets", 0.1),
            2: ("hiking boots", 2),
            3: ("mountain bikes", 25),
            4: ("ski resort gondolas", 60),
            5: ("mountain lions", 150)
        },
        'CT': {  # Connecticut
            1: ("lobster rolls", 1),
            2: ("sailboats", 20),
            3: ("lighthouses", 15),
            4: ("submarines", 200),
            5: ("harbor seals", 200)
        },
        'DE': {  # Delaware
            1: ("blue hens", 3),
            2: ("beach umbrellas", 5),
            3: ("fishing nets", 10),
            4: ("office buildings", 100),
            5: ("horseshoe crabs", 5)
        },
        'FL': {  # Florida
            1: ("Florida oranges", 0.3),
            2: ("Florida alligators", 15),
            3: ("palm trees", 35),
            4: ("Disney World rides", 80),
            5: ("space shuttles", 500)
        },
        'GA': {  # Georgia
            1: ("peaches", 0.2),
            2: ("golf clubs", 2),
            3: ("peach trees", 15),
            4: ("golf carts", 50),
            5: ("stone mountains", 200)
        },
        'HI': {  # Hawaii
            1: ("pineapples", 0.5),
            2: ("surfboards", 8),
            3: ("hula skirts", 0.5),
            4: ("volcano rocks", 50),
            5: ("hula dancers", 200)
        },
        'ID': {  # Idaho
            1: ("potatoes", 0.3),
            2: ("fishing rods", 2),
            3: ("mountain bikes", 25),
            4: ("potato farms", 50),
            5: ("whitewater rafts", 200)
        },
        'IL': {  # Illinois
            1: ("deep dish pizzas", 2),
            2: ("Chicago hot dogs", 0.5),
            3: ("skyscrapers", 100),
            4: ("corn fields", 50),
            5: ("Willis Tower", 500)
        },
        'IN': {  # Indiana
            1: ("basketballs", 1),
            2: ("race cars", 20),
            3: ("corn stalks", 0.5),
            4: ("race tracks", 100),
            5: ("basketball hoops", 200)
        },
        'IA': {  # Iowa
            1: ("corn cobs", 0.2),
            2: ("tractors", 50),
            3: ("corn fields", 50),
            4: ("grain silos", 100),
            5: ("corn mazes", 200)
        },
        'KS': {  # Kansas
            1: ("wheat stalks", 0.1),
            2: ("tornadoes", 0.1),
            3: ("wheat fields", 50),
            4: ("grain elevators", 100),
            5: ("prairie dogs", 200)
        },
        'KY': {  # Kentucky
            1: ("bourbon bottles", 1),
            2: ("race horses", 20),
            3: ("bourbon barrels", 50),
            4: ("race tracks", 100),
            5: ("thoroughbreds", 200)
        },
        'LA': {  # Louisiana
            1: ("crawfish", 0.1),
            2: ("jazz trumpets", 2),
            3: ("gumbo pots", 15),
            4: ("steamboats", 50),
            5: ("Mardi Gras floats", 200)
        },
        'ME': {  # Maine
            1: ("lobsters", 2),
            2: ("lighthouses", 15),
            3: ("maple syrup", 1),
            4: ("fishing boats", 50),
            5: ("moose", 200)
        },
        'MD': {  # Maryland
            1: ("crab cakes", 0.5),
            2: ("sailboats", 20),
            3: ("blue crabs", 5),
            4: ("harbor bridges", 100),
            5: ("sailing ships", 200)
        },
        'MA': {  # Massachusetts
            1: ("clam chowder", 1),
            2: ("sailboats", 20),
            3: ("lighthouses", 15),
            4: ("harbor seals", 50),
            5: ("whale watching boats", 200)
        },
        'MI': {  # Michigan
            1: ("cherries", 0.1),
            2: ("fishing rods", 2),
            3: ("cherry trees", 15),
            4: ("Great Lakes ships", 100),
            5: ("automobiles", 200)
        },
        'MN': {  # Minnesota
            1: ("wild rice", 0.1),
            2: ("fishing rods", 2),
            3: ("canoes", 15),
            4: ("lakes", 50),
            5: ("moose", 200)
        },
        'MS': {  # Mississippi
            1: ("catfish", 2),
            2: ("fishing rods", 2),
            3: ("river boats", 25),
            4: ("cotton fields", 50),
            5: ("steamboats", 200)
        },
        'MO': {  # Missouri
            1: ("barbecue ribs", 1),
            2: ("fishing rods", 2),
            3: ("river boats", 25),
            4: ("Gateway Arch", 100),
            5: ("steamboats", 200)
        },
        'MT': {  # Montana
            1: ("bison", 40),
            2: ("fishing rods", 2),
            3: ("mountain goats", 15),
            4: ("camping gear", 50),
            5: ("grizzly bears", 200)
        },
        'NE': {  # Nebraska
            1: ("corn cobs", 0.2),
            2: ("footballs", 1),
            3: ("corn fields", 50),
            4: ("grain silos", 100),
            5: ("prairie dogs", 200)
        },
        'NV': {  # Nevada
            1: ("slot machines", 3),
            2: ("poker chips", 0.1),
            3: ("roulette wheels", 25),
            4: ("casino tables", 60),
            5: ("desert mountains", 200)
        },
        'NH': {  # New Hampshire
            1: ("maple syrup", 1),
            2: ("ski poles", 2),
            3: ("mountain bikes", 25),
            4: ("ski resorts", 50),
            5: ("white mountains", 200)
        },
        'NJ': {  # New Jersey
            1: ("pizza slices", 0.5),
            2: ("beach umbrellas", 5),
            3: ("boardwalks", 15),
            4: ("beach houses", 50),
            5: ("lighthouses", 200)
        },
        'NM': {  # New Mexico
            1: ("chili peppers", 0.1),
            2: ("hiking boots", 2),
            3: ("adobe houses", 25),
            4: ("desert cacti", 50),
            5: ("hot air balloons", 200)
        },
        'NY': {  # New York
            1: ("bagels", 0.3),
            2: ("taxi cabs", 60),
            3: ("hot dog carts", 12),
            4: ("steel beams", 200),
            5: ("copper statues", 300)
        },
        'NC': {  # North Carolina
            1: ("barbecue ribs", 1),
            2: ("golf clubs", 2),
            3: ("tobacco leaves", 0.1),
            4: ("golf courses", 50),
            5: ("blue ridge mountains", 200)
        },
        'ND': {  # North Dakota
            1: ("wheat stalks", 0.1),
            2: ("fishing rods", 2),
            3: ("wheat fields", 50),
            4: ("grain elevators", 100),
            5: ("bison", 200)
        },
        'OH': {  # Ohio
            1: ("buckeyes", 0.1),
            2: ("footballs", 1),
            3: ("buckeye trees", 15),
            4: ("football stadiums", 100),
            5: ("rock and roll halls", 200)
        },
        'OK': {  # Oklahoma
            1: ("oil barrels", 5),
            2: ("cowboy boots", 2),
            3: ("oil rigs", 50),
            4: ("cattle ranches", 100),
            5: ("tornadoes", 0.1)
        },
        'OR': {  # Oregon
            1: ("coffee beans", 0.1),
            2: ("hiking boots", 2),
            3: ("Douglas firs", 25),
            4: ("coffee roasters", 50),
            5: ("crater lakes", 200)
        },
        'PA': {  # Pennsylvania
            1: ("cheesesteaks", 1),
            2: ("footballs", 1),
            3: ("liberty bells", 15),
            4: ("steel mills", 100),
            5: ("amish buggies", 200)
        },
        'RI': {  # Rhode Island
            1: ("clam cakes", 0.5),
            2: ("sailboats", 20),
            3: ("lighthouses", 15),
            4: ("harbor bridges", 50),
            5: ("sailing ships", 200)
        },
        'SC': {  # South Carolina
            1: ("peaches", 0.2),
            2: ("golf clubs", 2),
            3: ("palmetto trees", 15),
            4: ("golf courses", 50),
            5: ("beach houses", 200)
        },
        'SD': {  # South Dakota
            1: ("bison", 40),
            2: ("fishing rods", 2),
            3: ("mount rushmore", 100),
            4: ("badlands", 50),
            5: ("prairie dogs", 200)
        },
        'TN': {  # Tennessee
            1: ("guitar picks", 0.01),
            2: ("cowboy boots", 2),
            3: ("guitars", 15),
            4: ("music studios", 50),
            5: ("grand ole opry", 200)
        },
        'TX': {  # Texas
            1: ("cowboy boots", 2),
            2: ("barbecue smokers", 8),
            3: ("oil rigs", 50),
            4: ("Texas longhorns", 80),
            5: ("alamo", 200)
        },
        'UT': {  # Utah
            1: ("ski poles", 2),
            2: ("hiking boots", 2),
            3: ("mountain bikes", 25),
            4: ("ski resorts", 50),
            5: ("arches", 200)
        },
        'VT': {  # Vermont
            1: ("maple leaves", 0.01),
            2: ("hiking boots", 2),
            3: ("moose", 40),
            4: ("ski equipment", 50),
            5: ("black bears", 300)
        },
        'VA': {  # Virginia
            1: ("peanuts", 0.1),
            2: ("tobacco leaves", 0.1),
            3: ("lighthouses", 15),
            4: ("mountain bikes", 50),
            5: ("white-tailed deer", 150)
        },
        'WA': {  # Washington
            1: ("Washington apples", 0.3),
            2: ("hiking boots", 2),
            3: ("Pacific salmon", 8),
            4: ("coffee roasters", 40),
            5: ("black bears", 300)
        },
        'WV': {  # West Virginia
            1: ("coal", 0.5),
            2: ("fishing rods", 2),
            3: ("mountain bikes", 50),
            4: ("river barges", 50),
            5: ("black bears", 300)
        },
        'WI': {  # Wisconsin
            1: ("Wisconsin cheese wheels", 20),
            2: ("fishing rods", 2),
            3: ("dairy cows", 30),
            4: ("cargo ships", 500),
            5: ("white-tailed deer", 150)
        },
        'WY': {  # Wyoming
            1: ("bison", 40),
            2: ("cowboy hats", 1),
            3: ("mountain goats", 15),
            4: ("camping gear", 50),
            5: ("elk", 700)
        }
    }
    
    # Choose fun fact based on location
    if city in iconic_cities:
        item_name, item_weight = iconic_cities[city][tier]
        location_desc = f"vibrant {city}"
    elif state in state_facts:
        item_name, item_weight = state_facts[state][tier]
        location_desc = f"beautiful {state}"
    else:
        # Error: Location not supported for fun facts
        raise ValueError(f"Location-based fun facts not available for {city}, {state}. Only supported locations can generate personalized fun facts.")
    
    # Calculate quantity
    quantity = int(total_lbs / item_weight)
    if quantity == 0:
        quantity = 1
    
    # Handle pluralization
    if quantity == 1:
        item_text = f"1 {item_name.rstrip('s')}"
    else:
        item_text = f"{quantity} {item_name}"
    
    # Generate the fun fact message
    message = f"You've fed your pet {total_lbs} lbs of food—about the same weight as {item_text}. That's some serious love from {location_desc}!"
    
    return message

def analyze_food_consumption(food_data: List[Dict[str, Any]], zip_code: str = None) -> Dict[str, Any]:
    """
    Analyze food consumption data and return fun facts.
    
    Args:
        food_data (List[Dict[str, Any]]): Food consumption data from query
        zip_code (str): Customer's zip code for location-based fun facts
        
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
    
    # Generate location-based fun fact if zip code is provided
    if zip_code and zip_code.strip():
        try:
            location_fun_fact = get_food_fun_fact(zip_code, total_weight)
            fun_facts = [location_fun_fact]
        except Exception as e:
            # Fallback to generic fun facts if location-based fails
            fun_facts = [
                f"That's about {total_weight:.1f} pounds of pure pet love!",
                f"That's equivalent to a lot of happy meals!",
                f"That's about as much as... well, {total_weight:.1f} pounds!"
            ]
    else:
        # Use generic fun facts when no zip code is available
        fun_facts = [
            f"That's about {total_weight:.1f} pounds of pure pet love!",
            f"That's equivalent to a lot of happy meals!",
            f"That's about as much as... well, {total_weight:.1f} pounds!"
        ]
    
    return {
        "total_food_lbs": round(total_weight, 2),
        "weight_range": int(total_weight // 100) * 100,
        "fun_facts": fun_facts,
        "message": f"Your pets have consumed {total_weight:.2f} pounds of food!"
    }

def generate_food_fun_fact_json(food_data: List[Dict[str, Any]], zip_code: str = None) -> str:
    """
    Generate a JSON string with food consumption analysis.
    
    Args:
        food_data (List[Dict[str, Any]]): Food consumption data from query
        zip_code (str): Customer's zip code for location-based fun facts
        
    Returns:
        str: JSON string with analysis results
    """
    analysis = analyze_food_consumption(food_data, zip_code)
    return json.dumps(analysis, indent=2, ensure_ascii=False)

# For backward compatibility with the original script
def main():
    """Main function for standalone usage and testing."""
    # Test cases to verify the enhanced fun fact generator
    test_cases = [
        ("94105", 38.2),  # San Francisco, CA
        ("10001", 5.5),   # New York, NY
        ("90210", 150.0), # Beverly Hills, CA
        ("60601", 12.3),  # Chicago, IL
        ("33101", 0.5),   # Miami, FL
        ("12345", 75.8),  # Unknown location
        ("99501", 25.0),  # Anchorage, AK
        ("85001", 8.5),   # Phoenix, AZ
        ("80201", 45.2),  # Denver, CO
        ("98101", 12.8),  # Seattle, WA
    ]
    
    print("Enhanced Food Consumption Analyzer - 50-State Coverage")
    print("=" * 60)
    
    for zip_code, lbs in test_cases:
        fun_fact = get_food_fun_fact(zip_code, lbs)
        print(f"\nZip: {zip_code}, Food: {lbs} lbs")
        print(f"Fun Fact: {fun_fact}")

if __name__ == "__main__":
    main() 