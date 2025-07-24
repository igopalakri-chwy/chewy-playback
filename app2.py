from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from pathlib import Path

app = Flask(__name__)

# Configuration
OUTPUT_DIR = "Final_Pipeline/Output"
PERSONALITY_BADGES_DIR = "personalityzipped"

def get_all_customer_ids():
    """Get all customer IDs from the Output directory"""
    if not os.path.exists(OUTPUT_DIR):
        return []
    
    customer_ids = []
    for item in os.listdir(OUTPUT_DIR):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(item_path):
            customer_ids.append(item)
    
    return sorted(customer_ids, key=lambda x: int(x) if x.isdigit() else 0)

def get_customer_data(customer_id):
    """Retrieve all data for a given customer ID"""
    customer_dir = os.path.join(OUTPUT_DIR, str(customer_id))
    
    if not os.path.exists(customer_dir):
        return None
    
    data = {}
    
    # Get enriched pet profile
    profile_path = os.path.join(customer_dir, "enriched_pet_profile.json")
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            data['profile'] = json.load(f)
    
    # Get personality badge
    badge_path = os.path.join(customer_dir, "personality_badge.json")
    if os.path.exists(badge_path):
        with open(badge_path, 'r') as f:
            data['badge'] = json.load(f)
    
    # Get pet letter
    letter_path = os.path.join(customer_dir, "pet_letters.txt")
    if os.path.exists(letter_path):
        with open(letter_path, 'r') as f:
            data['letter'] = f.read()
    
    # Get pet portrait
    portrait_path = os.path.join(customer_dir, "images", "collective_pet_portrait.png")
    if os.path.exists(portrait_path):
        data['portrait'] = f"/static/customer_images/{customer_id}/collective_pet_portrait.png"
    
    # Get food fun fact
    food_fun_fact_path = os.path.join(customer_dir, "food_fun_fact.json")
    if os.path.exists(food_fun_fact_path):
        with open(food_fun_fact_path, 'r') as f:
            data['food_fun_fact'] = json.load(f)
    
    # Get predicted breed
    predicted_breed_path = os.path.join(customer_dir, "predicted_breed.json")
    if os.path.exists(predicted_breed_path):
        with open(predicted_breed_path, 'r') as f:
            breed_data = json.load(f)
            
            # Handle different data structures
            if isinstance(breed_data, dict):
                # Check if it's the nested structure (like customer 5038)
                if len(breed_data) == 1 and list(breed_data.keys())[0] in breed_data:
                    pet_data = breed_data[list(breed_data.keys())[0]]
                    breed_name = pet_data.get('top_predicted_breed', {}).get('breed', '')
                    data['predicted_breed'] = {
                        'customer_id': pet_data.get('customer_id'),
                        'pet_name': pet_data.get('pet_name'),
                        'predicted_breed': format_breed_name(breed_name),
                        'confidence': pet_data.get('confidence', {}).get('score', 0)
                    }
                else:
                    # Standard structure (like customer 887148270)
                    breed_name = breed_data.get('predicted_breed', '')
                    breed_data['predicted_breed'] = format_breed_name(breed_name)
                    data['predicted_breed'] = breed_data
    
    # Get unknowns data
    unknowns_path = os.path.join(customer_dir, "unknowns.json")
    if os.path.exists(unknowns_path):
        with open(unknowns_path, 'r') as f:
            data['unknowns'] = json.load(f)
    
    return data

def format_breed_name(breed_name):
    """Format breed name by adding spaces between camelCase words"""
    import re
    
    # Handle common breed name patterns (including lowercase variants)
    breed_mappings = {
        # Common breeds with proper spacing
        "Germanshepherd": "German Shepherd",
        "GermanShepherd": "German Shepherd",
        "goldenRetriever": "Golden Retriever",
        "GoldenRetriever": "Golden Retriever",
        "labradorRetriever": "Labrador Retriever",
        "LabradorRetriever": "Labrador Retriever",
        "cockerSpaniel": "Cocker Spaniel",
        "CockerSpaniel": "Cocker Spaniel",
        "englishBulldog": "English Bulldog",
        "EnglishBulldog": "English Bulldog",
        "frenchBulldog": "French Bulldog",
        "FrenchBulldog": "French Bulldog",
        "australianShepherd": "Australian Shepherd",
        "AustralianShepherd": "Australian Shepherd",
        "borderCollie": "Border Collie",
        "BorderCollie": "Border Collie",
        "berneseMountainDog": "Bernese Mountain Dog",
        "BerneseMountainDog": "Bernese Mountain Dog",
        "greatDane": "Great Dane",
        "GreatDane": "Great Dane",
        "saintBernard": "Saint Bernard",
        "SaintBernard": "Saint Bernard",
        "newfoundland": "Newfoundland",
        "Newfoundland": "Newfoundland",
        "irishSetter": "Irish Setter",
        "IrishSetter": "Irish Setter",
        "englishSetter": "English Setter",
        "EnglishSetter": "English Setter",
        "gordonSetter": "Gordon Setter",
        "GordonSetter": "Gordon Setter",
        "englishSpringerSpaniel": "English Springer Spaniel",
        "EnglishSpringerSpaniel": "English Springer Spaniel",
        "welshCorgi": "Welsh Corgi",
        "WelshCorgi": "Welsh Corgi",
        "pembrokeWelshCorgi": "Pembroke Welsh Corgi",
        "PembrokeWelshCorgi": "Pembroke Welsh Corgi",
        "cardiganWelshCorgi": "Cardigan Welsh Corgi",
        "CardiganWelshCorgi": "Cardigan Welsh Corgi",
        "jackRussellTerrier": "Jack Russell Terrier",
        "JackRussellTerrier": "Jack Russell Terrier",
        "westHighlandWhiteTerrier": "West Highland White Terrier",
        "WestHighlandWhiteTerrier": "West Highland White Terrier",
        "scottishTerrier": "Scottish Terrier",
        "ScottishTerrier": "Scottish Terrier",
        "yorkshireTerrier": "Yorkshire Terrier",
        "YorkshireTerrier": "Yorkshire Terrier",
        "cairnTerrier": "Cairn Terrier",
        "CairnTerrier": "Cairn Terrier",
        "norfolkTerrier": "Norfolk Terrier",
        "NorfolkTerrier": "Norfolk Terrier",
        "norwichTerrier": "Norwich Terrier",
        "NorwichTerrier": "Norwich Terrier",
        "lakelandTerrier": "Lakeland Terrier",
        "LakelandTerrier": "Lakeland Terrier",
        "borderTerrier": "Border Terrier",
        "BorderTerrier": "Border Terrier",
        "bedlingtonTerrier": "Bedlington Terrier",
        "BedlingtonTerrier": "Bedlington Terrier",
        "kerryBlueTerrier": "Kerry Blue Terrier",
        "KerryBlueTerrier": "Kerry Blue Terrier",
        "irishTerrier": "Irish Terrier",
        "IrishTerrier": "Irish Terrier",
        "welshTerrier": "Welsh Terrier",
        "WelshTerrier": "Welsh Terrier",
        "airedaleTerrier": "Airedale Terrier",
        "AiredaleTerrier": "Airedale Terrier",
        "bullTerrier": "Bull Terrier",
        "BullTerrier": "Bull Terrier",
        "staffordshireBullTerrier": "Staffordshire Bull Terrier",
        "StaffordshireBullTerrier": "Staffordshire Bull Terrier",
        "americanStaffordshireTerrier": "American Staffordshire Terrier",
        "AmericanStaffordshireTerrier": "American Staffordshire Terrier",
        "americanPitBullTerrier": "American Pit Bull Terrier",
        "AmericanPitBullTerrier": "American Pit Bull Terrier",
        "rhodesianRidgeback": "Rhodesian Ridgeback",
        "RhodesianRidgeback": "Rhodesian Ridgeback",
        "chesapeakeBayRetriever": "Chesapeake Bay Retriever",
        "ChesapeakeBayRetriever": "Chesapeake Bay Retriever",
        "flatCoatedRetriever": "Flat Coated Retriever",
        "FlatCoatedRetriever": "Flat Coated Retriever",
        "curlyCoatedRetriever": "Curly Coated Retriever",
        "CurlyCoatedRetriever": "Curly Coated Retriever",
        "novaScotiaDuckTollingRetriever": "Nova Scotia Duck Tolling Retriever",
        "NovaScotiaDuckTollingRetriever": "Nova Scotia Duck Tolling Retriever",
        "irishWaterSpaniel": "Irish Water Spaniel",
        "IrishWaterSpaniel": "Irish Water Spaniel",
        "americanWaterSpaniel": "American Water Spaniel",
        "AmericanWaterSpaniel": "American Water Spaniel",
        "fieldSpaniel": "Field Spaniel",
        "FieldSpaniel": "Field Spaniel",
        "sussexSpaniel": "Sussex Spaniel",
        "SussexSpaniel": "Sussex Spaniel",
        "clumberSpaniel": "Clumber Spaniel",
        "ClumberSpaniel": "Clumber Spaniel",
        "brittanySpaniel": "Brittany Spaniel",
        "BrittanySpaniel": "Brittany Spaniel",
        "englishCockerSpaniel": "English Cocker Spaniel",
        "EnglishCockerSpaniel": "English Cocker Spaniel",
        "americanCockerSpaniel": "American Cocker Spaniel",
        "AmericanCockerSpaniel": "American Cocker Spaniel",
        "boykinSpaniel": "Boykin Spaniel",
        "BoykinSpaniel": "Boykin Spaniel",
        "welshSpringerSpaniel": "Welsh Springer Spaniel",
        "WelshSpringerSpaniel": "Welsh Springer Spaniel",
        "germanShorthairedPointer": "German Shorthaired Pointer",
        "GermanShorthairedPointer": "German Shorthaired Pointer",
        "germanWirehairedPointer": "German Wirehaired Pointer",
        "GermanWirehairedPointer": "German Wirehaired Pointer",
        "englishPointer": "English Pointer",
        "EnglishPointer": "English Pointer",
        "irishRedandWhiteSetter": "Irish Red and White Setter",
        "IrishRedandWhiteSetter": "Irish Red and White Setter",
        "greaterSwissMountainDog": "Greater Swiss Mountain Dog",
        "GreaterSwissMountainDog": "Greater Swiss Mountain Dog",
        "entlebucherMountainDog": "Entlebucher Mountain Dog",
        "EntlebucherMountainDog": "Entlebucher Mountain Dog",
        "appenzellerSennenhund": "Appenzeller Sennenhund",
        "AppenzellerSennenhund": "Appenzeller Sennenhund",
        "bouvierDesFlandres": "Bouvier des Flandres",
        "BouvierDesFlandres": "Bouvier des Flandres",
        "briard": "Briard",
        "Briard": "Briard",
        "beauceron": "Beauceron",
        "Beauceron": "Beauceron",
        "belgianMalinois": "Belgian Malinois",
        "BelgianMalinois": "Belgian Malinois",
        "belgianShepherd": "Belgian Shepherd",
        "BelgianShepherd": "Belgian Shepherd",
        "belgianTervuren": "Belgian Tervuren",
        "BelgianTervuren": "Belgian Tervuren",
        "belgianGroenendael": "Belgian Groenendael",
        "BelgianGroenendael": "Belgian Groenendael",
        "dutchShepherd": "Dutch Shepherd",
        "DutchShepherd": "Dutch Shepherd",
        "anatolianShepherd": "Anatolian Shepherd",
        "AnatolianShepherd": "Anatolian Shepherd",
        "greatPyrenees": "Great Pyrenees",
        "GreatPyrenees": "Great Pyrenees",
        "komondor": "Komondor",
        "Komondor": "Komondor",
        "kuvasz": "Kuvasz",
        "Kuvasz": "Kuvasz",
        "maremmaSheepdog": "Maremma Sheepdog",
        "MaremmaSheepdog": "Maremma Sheepdog",
        "polishLowlandSheepdog": "Polish Lowland Sheepdog",
        "PolishLowlandSheepdog": "Polish Lowland Sheepdog",
        "puli": "Puli",
        "Puli": "Puli",
        "pumi": "Pumi",
        "Pumi": "Pumi",
        "schapendoes": "Schapendoes",
        "Schapendoes": "Schapendoes",
        "shetlandSheepdog": "Shetland Sheepdog",
        "ShetlandSheepdog": "Shetland Sheepdog",
        "oldEnglishSheepdog": "Old English Sheepdog",
        "OldEnglishSheepdog": "Old English Sheepdog",
        "beardedCollie": "Bearded Collie",
        "BeardedCollie": "Bearded Collie",
        "australianCattleDog": "Australian Cattle Dog",
        "AustralianCattleDog": "Australian Cattle Dog",
        "australianKelpie": "Australian Kelpie",
        "AustralianKelpie": "Australian Kelpie",
        "blueHeeler": "Blue Heeler",
        "BlueHeeler": "Blue Heeler",
        "redHeeler": "Red Heeler",
        "RedHeeler": "Red Heeler",
        "queenslandHeeler": "Queensland Heeler",
        "QueenslandHeeler": "Queensland Heeler",
        "lancashireHeeler": "Lancashire Heeler",
        "LancashireHeeler": "Lancashire Heeler",
        "swedishVallhund": "Swedish Vallhund",
        "SwedishVallhund": "Swedish Vallhund",
        "norwegianBuhund": "Norwegian Buhund",
        "NorwegianBuhund": "Norwegian Buhund",
        "icelandicSheepdog": "Icelandic Sheepdog",
        "IcelandicSheepdog": "Icelandic Sheepdog",
        "finnishLapphund": "Finnish Lapphund",
        "FinnishLapphund": "Finnish Lapphund",
        "lapponianHerder": "Lapponian Herder",
        "LapponianHerder": "Lapponian Herder",
        "norwegianElkhound": "Norwegian Elkhound",
        "NorwegianElkhound": "Norwegian Elkhound",
        "swedishElkhound": "Swedish Elkhound",
        "SwedishElkhound": "Swedish Elkhound",
        "finnishSpitz": "Finnish Spitz",
        "FinnishSpitz": "Finnish Spitz",
        "karelianBearDog": "Karelian Bear Dog",
        "KarelianBearDog": "Karelian Bear Dog",
        "russianEuropeanLaika": "Russian European Laika",
        "RussianEuropeanLaika": "Russian European Laika",
        "westSiberianLaika": "West Siberian Laika",
        "WestSiberianLaika": "West Siberian Laika",
        "eastSiberianLaika": "East Siberian Laika",
        "EastSiberianLaika": "East Siberian Laika",
        "yakutianLaika": "Yakutian Laika",
        "YakutianLaika": "Yakutian Laika",
        "norwegianLundehund": "Norwegian Lundehund",
        "NorwegianLundehund": "Norwegian Lundehund"
    }
    
    # Check if we have a direct mapping
    if breed_name in breed_mappings:
        return breed_mappings[breed_name]
    
    # Fallback: Add space before capital letters that follow lowercase letters
    formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', breed_name)
    return formatted

def get_badge_image_path(badge_name):
    """Map badge name to image file path"""
    badge_mapping = {
        "The Diva": "badge_diva copy.png",
        "The Cuddler": "badge_cuddler copy.png",
        "The Daydreamer": "badge_daydreamer copy.png",
        "The Explorer": "badge_explorer copy.png",
        "The Guardian": "badge_guardian copy.png",
        "The Nurturer": "badge_nurturer copy.png",
        "The Scholar": "badge_scholar copy.png",
        "The Shadow": "badge_shadow copy.png",
        "The Trickster": "badge_trickster copy.png",
        "The Athlete": "badge_athlete copy.png"
    }
    
    badge_file = badge_mapping.get(badge_name, "badge_athlete copy.png")
    return f"/static/badges/{badge_file}"

@app.route('/')
def index():
    """Landing page with customer ID input and list of all customers"""
    customer_ids = get_all_customer_ids()
    return render_template('index.html', customer_ids=customer_ids)

@app.route('/customers')
def customers():
    """Page showing all available customers"""
    customer_ids = get_all_customer_ids()
    return render_template('customers.html', customer_ids=customer_ids)

@app.route('/experience/<customer_id>')
def experience(customer_id):
    """Main experience page with all slides"""
    customer_data = get_customer_data(customer_id)
    
    if not customer_data:
        return render_template('error.html', message="Customer not found"), 404
    
    return render_template('experience.html', 
                         customer_id=customer_id, 
                         customer_data=customer_data)

@app.route('/api/customer/<customer_id>')
def api_customer_data(customer_id):
    """API endpoint to get customer data"""
    customer_data = get_customer_data(customer_id)
    
    if not customer_data:
        return jsonify({"error": "Customer not found"}), 404
    
    # Add badge image path
    if 'badge' in customer_data:
        customer_data['badge']['image_path'] = get_badge_image_path(customer_data['badge']['badge'])
    
    return jsonify(customer_data)

@app.route('/static/customer_images/<customer_id>/<filename>')
def customer_image(customer_id, filename):
    """Serve customer-specific images"""
    return send_from_directory(os.path.join(OUTPUT_DIR, customer_id, "images"), filename)

@app.route('/static/badges/<filename>')
def badge_image(filename):
    """Serve badge images"""
    return send_from_directory(PERSONALITY_BADGES_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002) 