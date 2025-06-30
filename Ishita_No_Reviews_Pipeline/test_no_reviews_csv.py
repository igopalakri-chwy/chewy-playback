#!/usr/bin/env python3
"""
Test script for the no reviews pipeline with new CSV structure
"""

import pandas as pd
import os
from pathlib import Path

def create_sample_csv():
    """Create a sample CSV file with the expected structure."""
    
    # Sample data with the required columns
    sample_data = {
        'customer_id': ['1183376', '1183376', '1183376', '1154095', '1154095'],
        'order_date': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-01-10', '2023-02-15'],
        'order_id': ['ORD001', 'ORD002', 'ORD003', 'ORD004', 'ORD005'],
        'product_id': ['PROD001', 'PROD002', 'PROD003', 'PROD004', 'PROD005'],
        'item_name': ['Blue Buffalo Dog Food', 'Kong Dog Toy', 'Greenies Dog Treats', 'Fancy Feast Cat Food', 'Catnip Mouse Toy'],
        'pet_name_1': ['Elwood', 'Elwood', 'Elwood', 'Sue Ling', 'Sue Ling'],
        'pet_name_2': ['Turbo', 'Turbo', 'Turbo', 'Sugar', 'Sugar']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Data directory if it doesn't exist
    data_dir = Path("../Data")
    data_dir.mkdir(exist_ok=True)
    
    # Save the sample CSV
    csv_path = data_dir / "no_review.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Created sample CSV at: {csv_path}")
    print(f"📊 Sample data preview:")
    print(df.head())
    
    return csv_path

def test_pipeline_loading():
    """Test that the pipeline can load the new CSV structure."""
    try:
        from chewy_playback_pipeline_no_reviews import OrderIntelligenceAgent
        
        # Create sample data
        csv_path = create_sample_csv()
        
        # Test the agent
        agent = OrderIntelligenceAgent("test_key")
        success = agent.load_data(str(csv_path))
        
        if success:
            print("✅ Pipeline successfully loaded the new CSV structure!")
            print(f"📋 Available columns: {list(agent.order_data.columns)}")
            
            # Test customer data retrieval
            customer_orders = agent._get_customer_orders('1183376')
            if customer_orders is not None and not customer_orders.empty:
                print(f"✅ Successfully retrieved orders for customer 1183376")
                print(f"📦 Number of orders: {len(customer_orders)}")
                print(f"🐾 Pet names found: {customer_orders['pet_name_1'].unique()}")
            else:
                print("❌ Failed to retrieve customer orders")
        else:
            print("❌ Failed to load CSV data")
            
    except Exception as e:
        print(f"❌ Error testing pipeline: {e}")

if __name__ == "__main__":
    print("🧪 Testing No Reviews Pipeline with New CSV Structure")
    print("=" * 60)
    test_pipeline_loading() 