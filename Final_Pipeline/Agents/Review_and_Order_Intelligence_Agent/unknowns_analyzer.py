#!/usr/bin/env python3
"""
Unknowns Analyzer
Scans enriched_pet_profile.json files for "UNK" values and creates an unknowns.json file
with all unknown attributes for each customer and pet.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnknownsAnalyzer:
    """
    Analyzes enriched pet profiles to identify and document unknown attributes.
    """
    
    def __init__(self):
        """Initialize the Unknowns Analyzer."""
        self.unknown_attributes = {}
    
    def scan_profile_for_unknowns(self, profile_data: Dict[str, Any], customer_id: str) -> Dict[str, Any]:
        """
        Scan a single enriched pet profile for unknown attributes.
        
        Args:
            profile_data: The enriched pet profile data
            customer_id: The customer ID
            
        Returns:
            Dictionary containing all unknown attributes found
        """
        unknowns = {
            'customer_id': customer_id,
            'unknown_attributes': {},
            'total_unknowns': 0,
            'pets_with_unknowns': 0
        }
        
        # Handle different profile structures
        if isinstance(profile_data, dict):
            # Check if this is the new structure with nested pets
            if 'pets' in profile_data:
                pets_data = profile_data['pets']
                customer_confidence = profile_data.get('cust_confidence_score', 0.0)
            else:
                # Old structure - treat the whole dict as pets data
                pets_data = profile_data
                customer_confidence = 0.0
            
            unknowns['customer_confidence_score'] = customer_confidence
            
            # Scan each pet's data
            for pet_name, pet_data in pets_data.items():
                if isinstance(pet_data, dict):
                    pet_unknowns = self._scan_pet_data(pet_data, pet_name)
                    if pet_unknowns:
                        unknowns['unknown_attributes'][pet_name] = pet_unknowns
                        unknowns['pets_with_unknowns'] += 1
                        unknowns['total_unknowns'] += len(pet_unknowns['unknown_fields']) + len(pet_unknowns['unknown_scores']) + len(pet_unknowns['unknown_lists']) + len(pet_unknowns['unknown_dicts'])
        
        return unknowns
    
    def _scan_pet_data(self, pet_data: Dict[str, Any], pet_name: str) -> Dict[str, Any]:
        """
        Scan a single pet's data for unknown attributes.
        
        Args:
            pet_data: The pet's profile data
            pet_name: The pet's name
            
        Returns:
            Dictionary of unknown attributes for this pet
        """
        pet_unknowns = {
            'pet_name': pet_name,
            'unknown_fields': [],
            'unknown_scores': [],
            'unknown_lists': [],
            'unknown_dicts': []
        }
        
        # Fields to exclude from unknown analysis
        excluded_fields = {
            'MostOrderedProducts', 'DietaryPreferences', 'HealthMentions', 
            'BrandPreferences', 'PersonalityTraits', 'FavoriteProductCategories',
            'BehavioralCues'
        }
        
        # Score fields to exclude from unknown analysis
        excluded_score_fields = {
            'PersonalityScores', 'CategoryScores', 'BrandScores', 
            'DietaryScores', 'BehavioralScores', 'HealthScores',
            'SizeScore', 'WeightScore', 'ConfidenceScore'
        }
        
        for field_name, field_value in pet_data.items():
            # Skip excluded fields
            if field_name in excluded_fields:
                continue
                
            # Check for "UNK" values (but include Breed even if it's Mixed/Unknown or Other)
            if field_value == "UNK":
                # Special handling for Breed - include it even if it's Mixed/Unknown or Other
                if field_name == "Breed":
                    pet_unknowns['unknown_fields'].append(field_name)
                else:
                    pet_unknowns['unknown_fields'].append(field_name)
            
            # Check for score fields that are 0.0 (indicating unknown)
            elif field_name.endswith('Score') and isinstance(field_value, (int, float)) and field_value == 0.0:
                # Skip excluded score fields
                if field_name not in excluded_score_fields:
                    pet_unknowns['unknown_scores'].append(field_name)
            
            # Check for empty lists (might indicate unknown preferences)
            elif isinstance(field_value, list) and len(field_value) == 0:
                # Skip excluded list fields
                if field_name not in excluded_fields:
                    pet_unknowns['unknown_lists'].append(field_name)
            
            # Check for empty dictionaries (might indicate unknown preferences)
            elif isinstance(field_value, dict) and len(field_value) == 0:
                # Skip excluded dict fields
                if field_name not in excluded_score_fields:
                    pet_unknowns['unknown_dicts'].append(field_name)
        
        # Only return if there are unknowns
        if (pet_unknowns['unknown_fields'] or pet_unknowns['unknown_scores'] or 
            pet_unknowns['unknown_lists'] or pet_unknowns['unknown_dicts']):
            return pet_unknowns
        else:
            return None
    
    def analyze_customer_directory(self, customer_dir: Path) -> Dict[str, Any]:
        """
        Analyze a customer's output directory for unknown attributes.
        
        Args:
            customer_dir: Path to the customer's output directory
            
        Returns:
            Dictionary containing analysis results
        """
        profile_path = customer_dir / "enriched_pet_profile.json"
        
        if not profile_path.exists():
            logger.warning(f"Profile not found: {profile_path}")
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            
            customer_id = customer_dir.name
            unknowns = self.scan_profile_for_unknowns(profile_data, customer_id)
            
            return unknowns
            
        except Exception as e:
            logger.error(f"Error analyzing {profile_path}: {e}")
            return None
    
    def analyze_single_customer(self, customer_id: str, output_dir: Path) -> Dict[str, Any]:
        """
        Analyze a single customer's enriched profile for unknown attributes.
        
        Args:
            customer_id: The customer ID to analyze
            output_dir: Path to the output directory
            
        Returns:
            Dictionary containing analysis results for this customer
        """
        customer_dir = output_dir / customer_id
        return self.analyze_customer_directory(customer_dir)
    
    def save_unknowns_json(self, analysis_results: Dict[str, Any], output_path: Path) -> bool:
        """
        Save the unknowns analysis to a JSON file.
        
        Args:
            analysis_results: The analysis results
            output_path: Path where to save the unknowns.json file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(analysis_results, f, indent=2)
            
            logger.info(f"Unknowns analysis saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving unknowns analysis: {e}")
            return False


def main():
    """Main function to run the unknowns analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze enriched pet profiles for unknown attributes")
    parser.add_argument("--customer-id", required=True, help="Customer ID to analyze")
    parser.add_argument("--output-dir", default="Output", help="Path to output directory")
    
    args = parser.parse_args()
    
    try:
        output_dir = Path(args.output_dir)
        if not output_dir.exists():
            print(f"❌ Output directory not found: {output_dir}")
            return
        
        analyzer = UnknownsAnalyzer()
        analysis_results = analyzer.analyze_single_customer(args.customer_id, output_dir)
        
        if analysis_results:
            # Save unknowns.json in the customer's directory
            customer_dir = output_dir / args.customer_id
            customer_dir.mkdir(exist_ok=True)
            unknowns_path = customer_dir / "unknowns.json"
            success = analyzer.save_unknowns_json(analysis_results, unknowns_path)
            
            if success:
                print(f"✅ Unknowns analysis completed for customer {args.customer_id}!")
                print(f"📊 Summary:")
                print(f"   Total unknowns: {analysis_results['total_unknowns']}")
                print(f"   Pets with unknowns: {analysis_results['pets_with_unknowns']}")
                print(f"📁 Results saved to: {unknowns_path}")
                
                # Print details for each pet
                for pet_name, pet_unknowns in analysis_results['unknown_attributes'].items():
                    print(f"\n🐾 {pet_name}:")
                    if pet_unknowns['unknown_fields']:
                        print(f"   Unknown fields: {', '.join(pet_unknowns['unknown_fields'])}")
                    if pet_unknowns['unknown_scores']:
                        print(f"   Unknown scores: {', '.join(pet_unknowns['unknown_scores'])}")
                    if pet_unknowns['unknown_lists']:
                        print(f"   Empty lists: {', '.join(pet_unknowns['unknown_lists'])}")
                    if pet_unknowns['unknown_dicts']:
                        print(f"   Empty dicts: {', '.join(pet_unknowns['unknown_dicts'])}")
            else:
                print("❌ Failed to save unknowns analysis")
        else:
            print(f"❌ No analysis results generated for customer {args.customer_id}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 