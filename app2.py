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
    """Get real data from JSON files for customer 5812, fallback to mock data for others"""
    import random
    
    data = {}
    
    # For customer 5812, use real JSON data
    if customer_id == "5812":
        customer_dir = os.path.join(OUTPUT_DIR, customer_id)
        
        # 1. Food Consumption Data
        try:
            with open(os.path.join(customer_dir, "yearly_food_count.json"), 'r') as f:
                food_data = json.load(f)
                if food_data:
                    total_lbs = food_data[0].get("TOTAL_LBS_CONSUMED_BY_CUSTOMER", 0)
                    top_product = food_data[0].get("PRODUCT_NAME", "Premium Pet Food")
                    data['food_consumption'] = {
                        'total_lbs': str(total_lbs),
                        'top_product': top_product
                    }
                else:
                    data['food_consumption'] = {
                        'total_lbs': "0",
                        'top_product': "Premium Pet Food"
                    }
        except Exception as e:
            print(f"Error reading food data: {e}")
            data['food_consumption'] = {
                'total_lbs': "0",
                'top_product': "Premium Pet Food"
            }
        
        # 2. Donations Data
        try:
            with open(os.path.join(customer_dir, "amount_donated.json"), 'r') as f:
                donation_data = json.load(f)
                if donation_data and donation_data[0].get("AMT_DONATED") is not None:
                    amount = donation_data[0]["AMT_DONATED"]
                    data['donations'] = {
                        'total_donations': f'${amount}',
                        'summary': f'You helped feed shelter pets this year! Your generosity makes a real difference.'
                    }
                else:
                    data['donations'] = {
                        'total_donations': '$0',
                        'summary': 'Start donating to help shelter pets! Every contribution makes a difference.'
                    }
        except Exception as e:
            print(f"Error reading donation data: {e}")
            data['donations'] = {
                'total_donations': '$0',
                'summary': 'Start donating to help shelter pets! Every contribution makes a difference.'
            }
        
        # 3. Milestone Data (Months with Chewy)
        try:
            with open(os.path.join(customer_dir, "total_months.json"), 'r') as f:
                months_data = json.load(f)
                if months_data:
                    months = months_data[0].get("MONTHS_WITH_CHEWY", 0)
                    data['milestone'] = {
                        'months': str(months),
                        'message': f'Thank you for being a loyal Chewy customer for {months} amazing {"month" if months == 1 else "months"}! Your trust means the world to us.'
                    }
                else:
                    data['milestone'] = {
                        'months': "0",
                        'message': 'Welcome to Chewy! We\'re excited to have you as part of our family.'
                    }
        except Exception as e:
            print(f"Error reading months data: {e}")
            data['milestone'] = {
                'months': "0",
                'message': 'Welcome to Chewy! We\'re excited to have you as part of our family.'
            }
        
        # 4. Most Reordered Data
        try:
            with open(os.path.join(customer_dir, "most_ordered.json"), 'r') as f:
                reorder_data = json.load(f)
                if reorder_data:
                    product_name = reorder_data[0].get("NAME", "Premium Pet Product")
                    times_ordered = reorder_data[0].get("TOTAL_QUANTITY_ORDERED", 0)
                    # Estimate total spent (assuming average $20 per order)
                    total_spent = times_ordered * 20
                    data['most_reordered'] = {
                        'product_name': product_name,
                        'times_ordered': str(times_ordered),
                        'total_spent': str(total_spent)
                    }
                else:
                    data['most_reordered'] = {
                        'product_name': "Premium Pet Product",
                        'times_ordered': "0",
                        'total_spent': "0"
                    }
        except Exception as e:
            print(f"Error reading reorder data: {e}")
            data['most_reordered'] = {
                'product_name': "Premium Pet Product",
                'times_ordered': "0",
                'total_spent': "0"
            }
        
        # 5. Busiest Month Data
        try:
            with open(os.path.join(customer_dir, "cuddliest_month.json"), 'r') as f:
                month_data = json.load(f)
                if month_data:
                    month = month_data[0].get("MONTH", "January")
                    orders = month_data[0].get("TOTAL_ORDERS", 0)
                    # Generate realistic interactions and spending based on orders
                    interactions = orders * 3  # Assume 3 interactions per order
                    total_spent = orders * 50  # Assume $50 average per order
                    data['cuddliest_month'] = {
                        'month': month,
                        'orders': str(orders),
                        'interactions': str(interactions),
                        'total_spent': str(total_spent)
                    }
                else:
                    data['cuddliest_month'] = {
                        'month': "January",
                        'orders': "0",
                        'interactions': "0",
                        'total_spent': "0"
                    }
        except Exception as e:
            print(f"Error reading month data: {e}")
            data['cuddliest_month'] = {
                'month': "January",
                'orders': "0",
                'interactions': "0",
                'total_spent': "0"
            }
        
        # 6. Autoship Savings Data
        try:
            with open(os.path.join(customer_dir, "autoship_savings.json"), 'r') as f:
                savings_data = json.load(f)
                if savings_data and len(savings_data) > 0:
                    # If there's data, use it; otherwise use default
                    amount_saved = savings_data[0] if isinstance(savings_data[0], (int, float)) else 0
                    data['autoship_savings'] = {
                        'amount_saved': str(amount_saved),
                        'message': f'You saved money with autoship this year! That\'s smart shopping!'
                    }
                else:
                    data['autoship_savings'] = {
                        'amount_saved': "0",
                        'message': 'Start using autoship to save money on your pet supplies!'
                    }
        except Exception as e:
            print(f"Error reading savings data: {e}")
            data['autoship_savings'] = {
                'amount_saved': "0",
                'message': 'Start using autoship to save money on your pet supplies!'
            }
        
        # Add mock data for other slides that don't have JSON files
        data['profile'] = {
            'customer_id': customer_id,
            'pet_name': "Buddy",
            'pet_type': 'Dog',
            'breed': 'Golden Retriever',
            'age': 5,
            'weight': 65,
            'favorite_toy': 'Tennis Ball',
            'favorite_treat': 'Peanut Butter Treats'
        }
        
        data['badge'] = {
            'badge': "The Explorer",
            'description': 'Buddy is the explorer! This personality type shows their unique character and behavior patterns.',
            'traits': ['Loyal', 'Playful', 'Curious', 'Energetic']
        }
        
        data['letter'] = """Dear Human,

I hope this letter finds you well! I wanted to take a moment to thank you for being the most amazing pet parent ever. You've given me the best life filled with love, treats, and endless belly rubs.

This year has been incredible! We've shared so many wonderful moments together - from our daily walks to our cozy cuddle sessions. You always know exactly what I need, whether it's my favorite Peanut Butter Treats or a good game with my Tennis Ball.

I'm so grateful for all the care you provide, from the premium food you choose to the vet visits that keep me healthy. You truly are my best friend and I love you more than words can express.

Thank you for being my person. I promise to continue being the best dog I can be and to love you unconditionally every single day.

With endless love and wagging tail,
Buddy 🐾

P.S. Can we have more treats? Pretty please? 🥺"""
        
        data['portrait'] = "/static/customer_images/5812/collective_pet_portrait.png"
        
        data['food_fun_fact'] = {
            'fact': "Did you know? Buddy has eaten enough food this year to fill 5 bathtubs! That's a lot of delicious meals!",
            'calories_consumed': 75000,
            'meals_served': 300
        }
        
        data['predicted_breed'] = {
            'customer_id': customer_id,
            'pet_name': "Buddy",
            'predicted_breed': 'Golden Retriever',
            'confidence': 0.95
        }
        
        data['unknowns'] = {
            'unknown_products': 2,
            'unknown_categories': 1,
            'total_products': 25,
            'unknown_attributes': {
                "Buddy": {
                    'unknown_products': 1,
                    'unknown_categories': 0,
                    'total_products': 20
                }
            }
        }
        
    else:
        # For other customers, use the original mock data generation
        import random
        
        # Generate random but consistent data based on customer_id
        try:
            random.seed(hash(str(customer_id)) % 1000)
        except:
            random.seed(42)  # fallback seed
        
        # Pet names and breeds for variety
        pet_names = ["Buddy", "Luna", "Max", "Bella", "Charlie", "Lucy", "Cooper", "Daisy", "Rocky", "Molly", "Bear", "Sophie", "Duke", "Chloe", "Jack", "Lola", "Tucker", "Zoe", "Oliver", "Ruby"]
        dog_breeds = ["Golden Retriever", "Labrador Retriever", "German Shepherd", "Bulldog", "Beagle", "Poodle", "Rottweiler", "Yorkshire Terrier", "Boxer", "Dachshund"]
        cat_breeds = ["Persian", "Maine Coon", "Siamese", "Ragdoll", "British Shorthair", "Abyssinian", "Russian Blue", "Sphynx", "Bengal", "Scottish Fold"]
        food_products = ["Premium Dog Food", "Grain-Free Cat Food", "Organic Puppy Food", "Senior Dog Formula", "Weight Management Cat Food", "Hypoallergenic Dog Food", "Wet Cat Food Variety Pack", "Raw Dog Food", "Limited Ingredient Cat Food", "Puppy Training Treats"]
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        personality_badges = ["The Explorer", "The Cuddler", "The Guardian", "The Scholar", "The Athlete", "The Diva", "The Nurturer", "The Trickster", "The Daydreamer", "The Shadow"]
        
        # Generate data based on customer_id
        pet_name = random.choice(pet_names)
        is_dog = random.choice([True, False])
        breed = random.choice(dog_breeds if is_dog else cat_breeds)
        food_lbs = random.randint(50, 300)
        top_product = random.choice(food_products)
        donation_amount = random.randint(10, 100)
        years_with_chewy = random.randint(1, 8)
        reorder_count = random.randint(5, 25)
        reorder_spent = reorder_count * random.randint(15, 30)
        busiest_month = random.choice(months)
        month_orders = random.randint(5, 15)
        month_interactions = random.randint(10, 25)
        month_spent = random.randint(100, 300)
        autoship_savings = random.randint(20, 80)
        personality_badge = random.choice(personality_badges)
        
        # Mock enriched pet profile
        data['profile'] = {
            'customer_id': customer_id,
            'pet_name': pet_name,
            'pet_type': 'Dog' if is_dog else 'Cat',
            'breed': breed,
            'age': random.randint(1, 12),
            'weight': random.randint(5, 80),
            'favorite_toy': random.choice(['Tennis Ball', 'Squeaky Toy', 'Rope Toy', 'Laser Pointer', 'Feather Wand', 'Mouse Toy']),
            'favorite_treat': random.choice(['Peanut Butter Treats', 'Salmon Bites', 'Chicken Strips', 'Cheese Cubes', 'Carrot Sticks', 'Tuna Flakes'])
        }
        
        # Mock personality badge
        data['badge'] = {
            'badge': personality_badge,
            'description': f'{pet_name} is {personality_badge.lower()}! This personality type shows their unique character and behavior patterns.',
            'traits': random.sample(['Loyal', 'Playful', 'Curious', 'Gentle', 'Energetic', 'Calm', 'Protective', 'Friendly'], 4)
        }
        
        # Mock pet letter
        data['letter'] = f"""Dear Human,

I hope this letter finds you well! I wanted to take a moment to thank you for being the most amazing pet parent ever. You've given me the best life filled with love, treats, and endless belly rubs.

This year has been incredible! We've shared so many wonderful moments together - from our daily walks to our cozy cuddle sessions. You always know exactly what I need, whether it's my favorite {data['profile']['favorite_treat']} or a good game with my {data['profile']['favorite_toy']}.

I'm so grateful for all the care you provide, from the premium food you choose to the vet visits that keep me healthy. You truly are my best friend and I love you more than words can express.

Thank you for being my person. I promise to continue being the best {data['profile']['pet_type'].lower()} I can be and to love you unconditionally every single day.

With endless love and wagging tail,
{pet_name} 🐾

P.S. Can we have more treats? Pretty please? 🥺"""
        
        # Mock pet portrait (use a default image)
        data['portrait'] = "/static/customer_images/5038/collective_pet_portrait.png"
        
        # Mock food fun fact
        data['food_fun_fact'] = {
            'fact': f"Did you know? {pet_name} has eaten enough food this year to fill {random.randint(3, 8)} bathtubs! That's a lot of delicious meals!",
            'calories_consumed': random.randint(50000, 150000),
            'meals_served': random.randint(200, 500)
        }
        
        # Mock predicted breed
        data['predicted_breed'] = {
            'customer_id': customer_id,
            'pet_name': pet_name,
            'predicted_breed': breed,
            'confidence': round(random.uniform(0.75, 0.98), 2)
        }
        
        # Mock unknowns data
        data['unknowns'] = {
            'unknown_products': random.randint(0, 5),
            'unknown_categories': random.randint(0, 3),
            'total_products': random.randint(20, 50),
            'unknown_attributes': {
                pet_name: {
                    'unknown_products': random.randint(0, 3),
                    'unknown_categories': random.randint(0, 2),
                    'total_products': random.randint(15, 40)
                }
            }
        }
        
        # New slides data
        data['food_consumption'] = {
            'total_lbs': str(food_lbs),
            'top_product': top_product
        }
        
        data['donations'] = {
            'total_donations': f'${donation_amount}',
            'summary': f'You helped feed {random.randint(3, 10)} shelter pets this year! Your generosity makes a real difference.'
        }
        
        data['milestone'] = {
            'months': str(years_with_chewy * 12),
            'message': f'Thank you for being a loyal Chewy customer for {years_with_chewy * 12} amazing {"month" if years_with_chewy * 12 == 1 else "months"}! Your trust means the world to us.'
        }
        
        data['most_reordered'] = {
            'product_name': top_product,
            'times_ordered': str(reorder_count),
            'total_spent': str(reorder_spent)
        }
        
        data['cuddliest_month'] = {
            'month': busiest_month,
            'orders': str(month_orders),
            'interactions': str(month_interactions),
            'total_spent': str(month_spent)
        }
        
        data['autoship_savings'] = {
            'amount_saved': str(autoship_savings),
            'message': f'You saved {random.randint(10, 25)}% on all autoship orders this year! That\'s smart shopping!'
        }
    
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
    
    return render_template('experience2.html', 
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