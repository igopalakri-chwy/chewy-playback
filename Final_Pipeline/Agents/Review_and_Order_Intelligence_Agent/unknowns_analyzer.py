#!/usr/bin/env python3
"""
Unknowns Analyzer
Scans query_2 pet profile data for null or "UNKN" values and creates an unknowns.json file
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
    Analyzes query_2 pet profile data to identify and document unknown attributes.
    """
    
    def __init__(self, snowflake_connector=None):
        """Initialize the Unknowns Analyzer."""
        self.unknown_attributes = {}
        self.snowflake_connector = snowflake_connector
    
    def scan_pet_profile_data_for_unknowns(self, pet_profile_data: List[Dict[str, Any]], customer_id: str) -> Dict[str, Any]:
        """
        Scan query_2 pet profile data for null or "UNKN" values.
        
        Args:
            pet_profile_data: The raw pet profile data from query_2
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
        
        if not pet_profile_data:
            return unknowns
        
        # Scan each pet's profile data
        for pet_record in pet_profile_data:
            if isinstance(pet_record, dict):
                pet_name = pet_record.get('PET_NAME', 'Unknown Pet')
                pet_unknowns = self._scan_pet_profile_record(pet_record, pet_name)
                if pet_unknowns:
                    unknowns['unknown_attributes'][pet_name] = pet_unknowns
                    unknowns['pets_with_unknowns'] += 1
                    unknowns['total_unknowns'] += len(pet_unknowns['unknown_fields'])
        
        return unknowns
    
    def _scan_pet_profile_record(self, pet_record: Dict[str, Any], pet_name: str) -> Dict[str, Any]:
        """
        Scan a single pet's profile record for null or "UNKN" values.
        
        Args:
            pet_record: The pet's profile record from query_2
            pet_name: The pet's name
            
        Returns:
            Dictionary of unknown attributes for this pet
        """
        pet_unknowns = {
            'pet_name': pet_name,
            'unknown_fields': []
        }
        
        # Fields to check for null or "UNKN" values
        fields_to_check = [
            'PET_TYPE', 'PET_BREED', 'WEIGHT', 'GENDER', 'PET_AGE', 'MEDICATION'
        ]
        
        # Values that indicate unknown information
        unknown_values = [None, "UNKN", "", "Mixed / Unknown", "Other", "None"]
        
        for field_name in fields_to_check:
            field_value = pet_record.get(field_name)
            
            # Check for null or unknown values
            if field_value in unknown_values:
                pet_unknowns['unknown_fields'].append(field_name)
        
        # Only return if there are unknowns
        if pet_unknowns['unknown_fields']:
            return pet_unknowns
        else:
            return None
    
    def analyze_customer_pet_profiles(self, customer_id: str) -> Dict[str, Any]:
        """
        Analyze a customer's pet profile data from query_2 for unknown attributes.
        
        Args:
            customer_id: The customer ID to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.snowflake_connector:
            logger.error("Snowflake connector not available")
            return None
        
        try:
            # Get pet profile data from cached data
            if hasattr(self, 'pipeline') and self.pipeline:
                # Use pipeline's cached data
                customer_data = self.pipeline._get_all_customer_data(customer_id)
                pet_profile_data = customer_data.get('get_pet_profiles', [])
            else:
                # No fallback - pipeline should always provide cached data
                logger.error(f"No pipeline reference available for customer {customer_id}")
                return None
            
            if not pet_profile_data:
                logger.warning(f"No pet profile data found for customer {customer_id}")
                return None
            unknowns = self.scan_pet_profile_data_for_unknowns(pet_profile_data, customer_id)
            
            return unknowns
            
        except Exception as e:
            logger.error(f"Error analyzing pet profiles for customer {customer_id}: {e}")
            return None
    
    def analyze_single_customer(self, customer_id: str, output_dir: Path) -> Dict[str, Any]:
        """
        Analyze a single customer's pet profile data for unknown attributes.
        
        Args:
            customer_id: The customer ID to analyze
            output_dir: Path to the output directory (not used in this version)
            
        Returns:
            Dictionary containing analysis results for this customer
        """
        return self.analyze_customer_pet_profiles(customer_id)
    
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
            logger.error(f"Error saving unknowns analysis to {output_path}: {e}")
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
            else:
                print("❌ Failed to save unknowns analysis")
        else:
            print(f"❌ No analysis results generated for customer {args.customer_id}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 