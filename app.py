from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import subprocess
import sys
from pathlib import Path
import re
import threading
import time

app = Flask(__name__)

# Configuration
OUTPUT_DIR = "Final_Pipeline/Output"
PERSONALITY_BADGES_DIR = "personalityzipped"
PIPELINE_SCRIPT = "Final_Pipeline/chewy_playback_pipeline.py"

# Global tracking for running pipelines
running_pipelines = set()
pipeline_lock = threading.Lock()

def run_pipeline_for_customer(customer_id):
    """Run the chewy_playback_pipeline.py script for a specific customer"""
    global running_pipelines
    
    with pipeline_lock:
        # Check if pipeline is already running for this customer
        if customer_id in running_pipelines:
            print(f"⏳ Pipeline already running for customer {customer_id}")
            return True
        
        # Add customer to running set
        running_pipelines.add(customer_id)
    
    try:
        print(f"🚀 Triggering pipeline for customer {customer_id}...")
        
        # Change to the project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Run the pipeline script in background and redirect immediately
        cmd = [sys.executable, PIPELINE_SCRIPT, "--customers", customer_id]
        print(f"🚀 Pipeline started for customer {customer_id} - redirecting to experience...")
        
        # Use existing environment variables for Snowflake credentials
        env = os.environ.copy()
        
        # Start pipeline in background (non-blocking) with environment variables
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        
        # Start a thread to monitor the process and remove from running set when done
        def monitor_process():
            process.wait()
            with pipeline_lock:
                running_pipelines.discard(customer_id)
                print(f"✅ Pipeline completed for customer {customer_id}")
        
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()
        
        # Return True immediately to redirect to experience page
        return True
    except Exception as e:
        # Remove from running set on error
        with pipeline_lock:
            running_pipelines.discard(customer_id)
        print(f"❌ Error running pipeline for customer {customer_id}: {e}")
        return False

def check_customer_data_exists(customer_id):
    """Check if customer data already exists in the output directory"""
    customer_dir = os.path.join(OUTPUT_DIR, customer_id)
    enriched_profile_path = os.path.join(customer_dir, "enriched_pet_profile.json")
    basic_data_path = os.path.join(customer_dir, f"{customer_id}.json")
    
    enriched_exists = os.path.exists(enriched_profile_path)
    basic_exists = os.path.exists(basic_data_path)
    
    print(f"🔍 check_customer_data_exists for {customer_id}:")
    print(f"  📁 Customer dir: {customer_dir}")
    print(f"  📁 Dir exists: {os.path.exists(customer_dir)}")
    print(f"  📄 Enriched profile exists: {enriched_exists}")
    print(f"  📄 Basic data exists: {basic_exists}")
    
    # Check if either enriched profile exists OR basic data exists
    result = enriched_exists or basic_exists
    print(f"  ✅ Final result: {result}")
    return result

def is_pipeline_running(customer_id):
    """Check if a pipeline is currently running for a customer"""
    with pipeline_lock:
        return customer_id in running_pipelines

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

def load_customer_data(customer_id):
    """Load customer data from pipeline-generated files"""
    customer_dir = os.path.join(OUTPUT_DIR, customer_id)
    data = {}
    
    print(f"🔍 Loading data for customer {customer_id}")
    print(f"📁 Customer directory: {customer_dir}")
    print(f"📁 Directory exists: {os.path.exists(customer_dir)}")
    
    try:
        # List all files in customer directory for debugging
        if os.path.exists(customer_dir):
            files = os.listdir(customer_dir)
            print(f"📋 Files in customer directory: {files}")
        
        # 1. Load enriched pet profile
        enriched_profile_path = os.path.join(customer_dir, "enriched_pet_profile.json")
        print(f"🔍 Checking enriched profile: {enriched_profile_path}")
        print(f"🔍 Enriched profile exists: {os.path.exists(enriched_profile_path)}")
        if os.path.exists(enriched_profile_path):
            with open(enriched_profile_path, 'r') as f:
                enriched_profile = json.load(f)
                data['enriched_profile'] = enriched_profile
                
                # Extract pets data
                pets_data = {}
                for pet_name, pet_info in enriched_profile.items():
                    if isinstance(pet_info, dict) and 'PetName' in pet_info:
                        pets_data[pet_name] = pet_info
                data['pets'] = pets_data
        else:
            print(f"❌ No enriched pet profile found for customer {customer_id}")
            return None
        
        # 2. Load personality badge
        badge_path = os.path.join(customer_dir, "personality_badge.json")
        if os.path.exists(badge_path):
            with open(badge_path, 'r') as f:
                badge_data = json.load(f)
                # Add image path for the badge
                badge_data['image_path'] = get_badge_image_path(badge_data.get('badge', 'The Explorer'))
                data['badge'] = badge_data
        else:
            print(f"⚠️ No personality badge found for customer {customer_id}")
            data['badge'] = None
        
        # 3. Load breed predictions
        breed_path = os.path.join(customer_dir, "predicted_breed.json")
        if os.path.exists(breed_path):
            with open(breed_path, 'r') as f:
                breed_data = json.load(f)
                data['breed_prediction'] = breed_data
        else:
            print(f"⚠️ No breed predictions found for customer {customer_id}")
            data['breed_prediction'] = None
        
        # 4. Load food fun facts
        food_path = os.path.join(customer_dir, "food_fun_fact.json")
        if os.path.exists(food_path):
            with open(food_path, 'r') as f:
                food_data = json.load(f)
                data['food_consumption'] = food_data
        else:
            print(f"⚠️ No food data found for customer {customer_id}")
            data['food_consumption'] = None
        
        # 5. Load zip aesthetics
        zip_path = os.path.join(customer_dir, "zip_aesthetics.json")
        if os.path.exists(zip_path):
            with open(zip_path, 'r') as f:
                zip_data = json.load(f)
                data['zip_aesthetics'] = zip_data
        else:
            print(f"⚠️ No zip aesthetics found for customer {customer_id}")
            data['zip_aesthetics'] = None
        
        # 6. Load pet letters
        letters_path = os.path.join(customer_dir, "pet_letters.txt")
        if os.path.exists(letters_path):
            with open(letters_path, 'r') as f:
                letters_content = f.read()
                data['pet_letters'] = letters_content
        else:
            print(f"⚠️ No pet letters found for customer {customer_id}")
            data['pet_letters'] = None
        
        # 7. Load basic customer data (for generic customers)
        basic_data_path = os.path.join(customer_dir, f"{customer_id}.json")
        if os.path.exists(basic_data_path):
            with open(basic_data_path, 'r') as f:
                basic_data = json.load(f)
                # Merge basic data into main data object
                data.update(basic_data)
                print(f"✅ Loaded basic data for customer {customer_id}")
        else:
            print(f"⚠️ No basic data found for customer {customer_id}")
        
        # 8. Load additional pipeline data if available
        # Load unknowns data (this exists)
        unknowns_path = os.path.join(customer_dir, "unknowns.json")
        if os.path.exists(unknowns_path):
            with open(unknowns_path, 'r') as f:
                data['unknowns'] = json.load(f)
                print(f"✅ Loaded unknowns data for customer {customer_id}: {data['unknowns']}")
        else:
            print(f"⚠️ No unknowns data found for customer {customer_id}")
            data['unknowns'] = None
        
        # Load food fun fact data (this exists)
        food_fun_fact_path = os.path.join(customer_dir, "food_fun_fact.json")
        if os.path.exists(food_fun_fact_path):
            with open(food_fun_fact_path, 'r') as f:
                food_data = json.load(f)
                data['food_fun_fact'] = food_data
                # Also add as food_consumption for template compatibility
                data['food_consumption'] = {
                    'total_lbs': food_data.get('total_food_lbs', '0'),
                    'top_product': food_data.get('top_product', 'Unknown')
                }
        
        # Load zip aesthetics data (this exists)
        zip_aesthetics_path = os.path.join(customer_dir, "zip_aesthetics.json")
        if os.path.exists(zip_aesthetics_path):
            with open(zip_aesthetics_path, 'r') as f:
                data['zip_aesthetics'] = json.load(f)
        
        # 8. Load consolidated queries data (the 6 SQL queries)
        consolidated_path = os.path.join(customer_dir, f"{customer_id}.json")
        print(f"🔍 Looking for consolidated data at: {consolidated_path}")
        if os.path.exists(consolidated_path):
            print(f"✅ Found consolidated data for customer {customer_id}")
            with open(consolidated_path, 'r') as f:
                consolidated_data = json.load(f)
                print(f"📊 Loaded consolidated data: {consolidated_data}")
                data['consolidated_queries'] = consolidated_data
                # Extract individual query results for easy access
                data['amount_donated'] = consolidated_data.get('amount_donated')
                data['cuddliest_month'] = consolidated_data.get('cuddliest_month')
                data['total_months'] = consolidated_data.get('total_months')
                data['autoship_savings'] = consolidated_data.get('autoship_savings')
                data['most_ordered'] = consolidated_data.get('most_ordered')
                data['yearly_food_count'] = consolidated_data.get('yearly_food_count')
                data['zip_code'] = consolidated_data.get('zip_code')
                print(f"📋 Extracted data - donations: {data['amount_donated']}, cuddliest: {data['cuddliest_month']}, months: {data['total_months']}, savings: {data['autoship_savings']}")
        else:
            print(f"⚠️ No consolidated queries found for customer {customer_id}")
            data['consolidated_queries'] = None
            data['amount_donated'] = None
            data['cuddliest_month'] = None
            data['total_months'] = None
            data['autoship_savings'] = None
            data['most_ordered'] = None
            data['yearly_food_count'] = None
            data['zip_code'] = None
        
        # Use real breed prediction data if available
        if 'breed_prediction' in data and data['breed_prediction']:
            if data['breed_prediction'].get('multiple_predictions'):
                # Keep the full multiple_predictions data for the template
                # The template will handle displaying the first pet's predictions
                pass
            else:
                # For single prediction data, format the breed name
                if 'predicted_breed' in data['breed_prediction']:
                    data['breed_prediction']['predicted_breed'] = format_breed_name(data['breed_prediction']['predicted_breed'])
        
        # Use real letter data
        data['letter'] = data.get('pet_letters', 'No personalized letter available.')
        
        # Use real portrait data
        data['portrait'] = f"/static/customer_images/{customer_id}/collective_pet_portrait.png"
        
        # Add badge image path if badge exists
        if 'badge' in data and data['badge'] is not None:
            data['badge']['image_path'] = get_badge_image_path(data['badge']['badge'])
        
        # 8. Don't create fake data - only show real data
        # These fields will be None if not available from pipeline
        
        print(f"✅ Successfully loaded data for customer {customer_id}")
        print(f"📊 Data keys: {list(data.keys())}")
        return data
        
    except Exception as e:
        print(f"❌ Error loading customer data for {customer_id}: {e}")
        return None

def format_breed_name(breed_name):
    """Format breed name for display"""
    if not breed_name:
        return "Unknown"
    
    # Common breed name mappings
    breed_mappings = {
        "germanShepherd": "German Shepherd",
        "goldenRetriever": "Golden Retriever",
        "labradorRetriever": "Labrador Retriever",
        "borderCollie": "Border Collie",
        "australianShepherd": "Australian Shepherd",
        "beagle": "Beagle",
        "bulldog": "Bulldog",
        "poodle": "Poodle",
        "rottweiler": "Rottweiler",
        "siberianHusky": "Siberian Husky",
        "boxer": "Boxer",
        "dobermanPinscher": "Doberman Pinscher",
        "greatDane": "Great Dane",
        "berneseMountainDog": "Bernese Mountain Dog",
        "newfoundland": "Newfoundland",
        "saintBernard": "Saint Bernard",
        "mastiff": "Mastiff",
        "chowChow": "Chow Chow",
        "shibaInu": "Shiba Inu",
        "akita": "Akita",
        "samoyed": "Samoyed",
        "alaskanMalamute": "Alaskan Malamute",
        "husky": "Husky",
        "chihuahua": "Chihuahua",
        "pomeranian": "Pomeranian",
        "yorkshireTerrier": "Yorkshire Terrier",
        "maltese": "Maltese",
        "shihTzu": "Shih Tzu",
        "pug": "Pug",
        "bostonTerrier": "Boston Terrier",
        "frenchBulldog": "French Bulldog",
        "englishBulldog": "English Bulldog",
        "cavalierKingCharlesSpaniel": "Cavalier King Charles Spaniel",
        "cockerSpaniel": "Cocker Spaniel",
        "englishSpringerSpaniel": "English Springer Spaniel",
        "irishSetter": "Irish Setter",
        "goldenRetriever": "Golden Retriever",
        "labradorRetriever": "Labrador Retriever",
        "chesapeakeBayRetriever": "Chesapeake Bay Retriever",
        "flatCoatedRetriever": "Flat-Coated Retriever",
        "curlyCoatedRetriever": "Curly-Coated Retriever",
        "novaScotiaDuckTollingRetriever": "Nova Scotia Duck Tolling Retriever",
        "germanShorthairedPointer": "German Shorthaired Pointer",
        "germanWirehairedPointer": "German Wirehaired Pointer",
        "weimaraner": "Weimaraner",
        "vizsla": "Vizsla",
        "pointer": "Pointer",
        "setter": "Setter",
        "spaniel": "Spaniel",
        "terrier": "Terrier",
        "hound": "Hound",
        "herding": "Herding Dog",
        "working": "Working Dog",
        "toy": "Toy Dog",
        "sporting": "Sporting Dog",
        "nonSporting": "Non-Sporting Dog",
        "mixed": "Mixed Breed",
        "unknown": "Unknown Breed"
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

# Register template filter
@app.template_filter('format_breed_name')
def format_breed_name_filter(breed_name):
    return format_breed_name(breed_name)

@app.template_filter('format_breed_name_simple')
def format_breed_name_simple_filter(breed_name):
    """Simple breed name formatter for template use"""
    if not breed_name:
        return "Unknown"
    
    # Replace underscores with spaces and capitalize each word
    formatted = breed_name.replace('_', ' ')
    
    # Handle camelCase by adding spaces before capital letters
    import re
    formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', formatted)
    
    # Capitalize first letter of each word
    formatted = ' '.join(word.capitalize() for word in formatted.split())
    
    return formatted

@app.route('/')
def index():
    """Landing page with customer ID input and list of all customers"""
    customer_ids = get_all_customer_ids()
    return render_template('index.html', customer_ids=customer_ids)

@app.route('/customers')
def customers():
    """Page showing all available customers"""
    customer_ids = get_all_customer_ids()
    return render_template('index.html', customer_ids=customer_ids)

@app.route('/experience/<customer_id>')
def experience(customer_id):
    """Main experience page with all slides"""
    print(f"🎯 Experience route called for customer {customer_id}")
    
    # Check if data exists
    data_exists = check_customer_data_exists(customer_id)
    print(f"📁 Data exists for customer {customer_id}: {data_exists}")
    
    if not data_exists:
        # Check if pipeline is already running
        if is_pipeline_running(customer_id):
            print(f"⏳ Pipeline already running for customer {customer_id}")
            return render_template('loading.html', 
                                 customer_id=customer_id,
                                 message="Pipeline is already running in the background. Please refresh the page in a few moments.")
        
        print(f"📁 No existing data for customer {customer_id}, running pipeline...")
        run_pipeline_for_customer(customer_id)
        
        # Show loading page while pipeline runs in background
        return render_template('loading.html', 
                             customer_id=customer_id,
                             message="Pipeline is running in the background. Please refresh the page in a few moments.")
    
    customer_data = load_customer_data(customer_id)
    print(f"📊 Customer data loaded: {customer_data is not None}")
    
    if not customer_data:
        print(f"❌ No customer data returned for {customer_id}")
        return render_template('error.html', 
                             error_message=f"Could not load data for customer {customer_id}")
    
    # Determine if customer is personalized or generic
    is_personalized = customer_data.get('enriched_profile', {}).get('gets_personalized', False)
    print(f"🔍 Customer {customer_id} - gets_personalized: {is_personalized}")
    print(f"📊 Customer data keys: {list(customer_data.keys())}")
    print(f"🔍 Unknowns data: {customer_data.get('unknowns')}")
    if is_personalized:
        print(f"🎯 Rendering personalized experience for customer {customer_id}")
        return render_template('personalized_experience.html', customer_id=customer_id, customer_data=customer_data)
    else:
        print(f"📋 Rendering generic experience for customer {customer_id}")
        return render_template('generic_experience.html', customer_id=customer_id, customer_data=customer_data)

@app.route('/api/customer/<customer_id>')
def api_customer_data(customer_id):
    """API endpoint to get customer data"""
    # Check if data exists
    if not check_customer_data_exists(customer_id):
        # Check if pipeline is already running
        if is_pipeline_running(customer_id):
            print(f"⏳ Pipeline already running for customer {customer_id}")
            return jsonify({"status": "pipeline_running", "message": "Pipeline already running in background"}), 202
        
        print(f"📁 No existing data for customer {customer_id}, running pipeline...")
        run_pipeline_for_customer(customer_id)
        return jsonify({"status": "pipeline_running", "message": "Pipeline started in background"}), 202
    
    customer_data = load_customer_data(customer_id)
    
    if not customer_data:
        return jsonify({"error": "Customer not found"}), 404
    
    # Add badge image path
    if 'badge' in customer_data and customer_data['badge'] is not None:
        customer_data['badge']['image_path'] = get_badge_image_path(customer_data['badge']['badge'])
    
    return jsonify(customer_data)

@app.route('/api/trigger-pipeline/<customer_id>')
def trigger_pipeline(customer_id):
    """Manually trigger the pipeline for a customer"""
    try:
        success = run_pipeline_for_customer(customer_id)
        if success:
            return jsonify({"status": "success", "message": f"Pipeline completed for customer {customer_id}"})
        else:
            return jsonify({"status": "error", "message": f"Pipeline failed for customer {customer_id}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/static/customer_images/<customer_id>/<filename>')
def customer_image(customer_id, filename):
    """Serve customer-specific images"""
    return send_from_directory(os.path.join(OUTPUT_DIR, customer_id, "images"), filename)

@app.route('/static/badges/<filename>')
def badge_image(filename):
    """Serve badge images"""
    return send_from_directory(PERSONALITY_BADGES_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 