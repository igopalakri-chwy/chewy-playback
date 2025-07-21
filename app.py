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
    
    return data

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
    app.run(debug=True, host='0.0.0.0', port=5001) 