#!/usr/bin/env python3
"""
Extract cached data from pipeline and create consolidated JSON file
"""

import json
import sys
from pathlib import Path

# Add the Final_Pipeline directory to the path
sys.path.append('Final_Pipeline')

from snowflake_data_connector import SnowflakeDataConnector

def extract_cached_data(customer_id: str):
    """Extract cached data and create consolidated JSON file"""
    
    # Initialize Snowflake connector
    connector = SnowflakeDataConnector()
    
    # Get customer data
    print(f"🔍 Fetching data for customer {customer_id}...")
    customer_data = connector.get_customer_data(customer_id)
    
    # Extract the 6 query results for generic experience
    consolidated_data = {}
    
    # Extract amount donated
    if 'get_amt_donated' in customer_data and customer_data['get_amt_donated']:
        amount = customer_data['get_amt_donated'][0].get('AMOUNT_DONATED', 0)
        consolidated_data['amount_donated'] = float(amount) if amount else 0.0
        print(f"💰 Amount donated: {consolidated_data['amount_donated']}")
    
    # Extract cuddliest month
    if 'get_cudd_month' in customer_data and customer_data['get_cudd_month']:
        month = customer_data['get_cudd_month'][0].get('CUDDLIEST_MONTH', 'N/A')
        consolidated_data['cuddliest_month'] = month
        print(f"📅 Cuddliest month: {consolidated_data['cuddliest_month']}")
    
    # Extract total months
    if 'get_total_months' in customer_data and customer_data['get_total_months']:
        months = customer_data['get_total_months'][0].get('TOTAL_MONTHS', 0)
        consolidated_data['total_months'] = int(months) if months else 0
        print(f"🎊 Total months: {consolidated_data['total_months']}")
    
    # Extract autoship savings
    if 'get_autoship_savings' in customer_data and customer_data['get_autoship_savings']:
        savings = customer_data['get_autoship_savings'][0].get('AUTOSHIP_SAVINGS', 0)
        consolidated_data['autoship_savings'] = float(savings) if savings else 0.0
        print(f"💰 Autoship savings: {consolidated_data['autoship_savings']}")
    
    # Extract most ordered
    if 'get_most_ordered' in customer_data and customer_data['get_most_ordered']:
        product = customer_data['get_most_ordered'][0].get('MOST_ORDERED_PRODUCT', 'No data available')
        consolidated_data['most_ordered'] = product
        print(f"🔄 Most ordered: {consolidated_data['most_ordered']}")
    
    # Extract yearly food count
    if 'get_yearly_food_count' in customer_data and customer_data['get_yearly_food_count']:
        food_count = len(customer_data['get_yearly_food_count'])
        consolidated_data['yearly_food_count'] = food_count
        print(f"🍽️ Yearly food count: {consolidated_data['yearly_food_count']}")
    
    # Create output directory
    output_dir = Path('Final_Pipeline/Output') / customer_id
    output_dir.mkdir(exist_ok=True)
    
    # Save consolidated JSON file
    json_path = output_dir / f"{customer_id}.json"
    with open(json_path, 'w') as f:
        json.dump(consolidated_data, f, indent=2)
    
    print(f"✅ Created consolidated JSON file: {json_path}")
    print(f"📊 Data extracted: {consolidated_data}")
    
    return consolidated_data

if __name__ == "__main__":
    customer_id = "958100772"
    extract_cached_data(customer_id) 