#!/usr/bin/env python3
"""
Data preprocessing script to convert actual CSV format to the format expected by the agent.
"""

import pandas as pd
import os

def preprocess_order_history(input_path, output_path):
    """Preprocess order history data to match expected format."""
    print(f"📊 Preprocessing order history from {input_path}")
    
    # Read the original data
    df = pd.read_csv(input_path)
    
    # Create the expected format
    processed_df = pd.DataFrame({
        'CustomerID': df['CUSTOMER_ID'].astype(str),
        'ProductID': df['PRODUCT_ID'].astype(str),
        'ProductName': df['ITEM_NAME'].fillna('Unknown Product'),
        'OrderDate': df['ORDER_DATE'],
        'Quantity': df['QUANTITY'],
        'Price': df['UNIT_PRICE']
    })
    
    # Save processed data
    processed_df.to_csv(output_path, index=False)
    print(f"✅ Processed order history saved to {output_path}")
    print(f"   - Records: {len(processed_df):,}")
    
    return processed_df

def preprocess_qualifying_reviews(input_path, output_path):
    """Preprocess qualifying reviews data to match expected format."""
    print(f"📊 Preprocessing qualifying reviews from {input_path}")
    
    # Read the original data
    df = pd.read_csv(input_path)
    
    # Create separate rows for each pet
    processed_rows = []
    
    for _, row in df.iterrows():
        # Process first pet (PET_NAME1)
        if pd.notna(row['PET_NAME1']) and row['PET_NAME1'].strip():
            processed_rows.append({
                'CustomerID': str(row['CUSTOMER_ID']),
                'PetName': row['PET_NAME1'].strip(),
                'ReviewText': str(row['REVIEW_TXT']) if pd.notna(row['REVIEW_TXT']) else '',
                'PetType': str(row['PET_TYPE1']) if pd.notna(row['PET_TYPE1']) else 'UNK',
                'Breed': str(row['PET_BREED1']) if pd.notna(row['PET_BREED1']) else 'UNK',
                'LifeStage': str(row['LIFE_STAGE1']) if pd.notna(row['LIFE_STAGE1']) else 'UNK',
                'Gender': str(row['PET_GENDER1']) if pd.notna(row['PET_GENDER1']) else 'UNK',
                'SizeCategory': str(row['PET_SIZE1']) if pd.notna(row['PET_SIZE1']) else 'UNK',
                'Weight': str(row['PET_WEIGHT_TYPE1']) if pd.notna(row['PET_WEIGHT_TYPE1']) else 'UNK',
                'Birthday': str(row['PET_BIRTHDAY1']) if pd.notna(row['PET_BIRTHDAY1']) else 'UNK',
                'ProductID': str(row['PRODUCT_PART_NUMBER']) if pd.notna(row['PRODUCT_PART_NUMBER']) else 'UNK',
                'ProductName': str(row['PRODUCT_NAME']) if pd.notna(row['PRODUCT_NAME']) else 'Unknown Product',
                'Rating': row['RATING'] if pd.notna(row['RATING']) else 0,
                'ReviewDate': str(row['REVIEW_DATE']) if pd.notna(row['REVIEW_DATE']) else 'UNK'
            })
        
        # Process second pet (PET_NAME2) if it exists
        if pd.notna(row['PET_NAME2']) and row['PET_NAME2'].strip():
            processed_rows.append({
                'CustomerID': str(row['CUSTOMER_ID']),
                'PetName': row['PET_NAME2'].strip(),
                'ReviewText': str(row['REVIEW_TXT']) if pd.notna(row['REVIEW_TXT']) else '',
                'PetType': str(row['PET_TYPE2']) if pd.notna(row['PET_TYPE2']) else 'UNK',
                'Breed': str(row['PET_BREED2']) if pd.notna(row['PET_BREED2']) else 'UNK',
                'LifeStage': str(row['LIFE_STAGE2']) if pd.notna(row['LIFE_STAGE2']) else 'UNK',
                'Gender': str(row['PET_GENDER2']) if pd.notna(row['PET_GENDER2']) else 'UNK',
                'SizeCategory': str(row['PET_SIZE2']) if pd.notna(row['PET_SIZE2']) else 'UNK',
                'Weight': str(row['PET_WEIGHT_TYPE2']) if pd.notna(row['PET_WEIGHT_TYPE2']) else 'UNK',
                'Birthday': str(row['PET_BIRTHDAY2']) if pd.notna(row['PET_BIRTHDAY2']) else 'UNK',
                'ProductID': str(row['PRODUCT_PART_NUMBER']) if pd.notna(row['PRODUCT_PART_NUMBER']) else 'UNK',
                'ProductName': str(row['PRODUCT_NAME']) if pd.notna(row['PRODUCT_NAME']) else 'Unknown Product',
                'Rating': row['RATING'] if pd.notna(row['RATING']) else 0,
                'ReviewDate': str(row['REVIEW_DATE']) if pd.notna(row['REVIEW_DATE']) else 'UNK'
            })
    
    # Create DataFrame from processed rows
    processed_df = pd.DataFrame(processed_rows)
    
    # Save processed data
    processed_df.to_csv(output_path, index=False)
    print(f"✅ Processed qualifying reviews saved to {output_path}")
    print(f"   - Records: {len(processed_df):,}")
    
    return processed_df

def filter_customer_data(customer_id, order_df, review_df):
    """Filter data for a specific customer."""
    print(f"🔍 Filtering data for customer {customer_id}")
    
    # Filter order data
    customer_orders = order_df[order_df['CustomerID'] == str(customer_id)]
    print(f"   - Orders: {len(customer_orders)}")
    
    # Filter review data
    customer_reviews = review_df[review_df['CustomerID'] == str(customer_id)]
    print(f"   - Reviews: {len(customer_reviews)}")
    
    return customer_orders, customer_reviews

def main():
    """Main preprocessing function."""
    print("🔄 Data Preprocessing for Review and Order Intelligence Agent")
    print("=" * 70)
    
    # Define paths for new files - correct relative paths from agent directory
    original_order_path = "../../Data/order_history.csv"
    original_review_path = "../../Data/qualifying_reviews.csv"
    
    processed_order_path = "processed_orderhistory.csv"
    processed_review_path = "processed_qualifyingreviews.csv"
    
    # Check if original files exist
    if not os.path.exists(original_order_path):
        print(f"❌ Order history file not found: {original_order_path}")
        return False
    
    if not os.path.exists(original_review_path):
        print(f"❌ Qualifying reviews file not found: {original_review_path}")
        return False
    
    try:
        # Preprocess order history
        order_df = preprocess_order_history(original_order_path, processed_order_path)
        
        # Preprocess qualifying reviews
        review_df = preprocess_qualifying_reviews(original_review_path, processed_review_path)
        
        # Check for customer 1183376 (the one with 3 pets mentioned but 2 registered)
        customer_id = "1183376"
        customer_orders, customer_reviews = filter_customer_data(customer_id, order_df, review_df)
        
        if customer_orders.empty:
            print(f"❌ Customer {customer_id} not found in order history")
            return False
        
        if customer_reviews.empty:
            print(f"❌ Customer {customer_id} not found in qualifying reviews")
            return False
        
        print(f"\n✅ Customer {customer_id} data found:")
        print(f"   - Orders: {len(customer_orders)}")
        print(f"   - Reviews: {len(customer_reviews)}")
        
        # Show pets for this customer
        pets = customer_reviews['PetName'].unique()
        print(f"   - Pets: {pets.tolist()}")
        
        # Show sample of customer data
        print(f"\n📋 Sample order data for customer {customer_id}:")
        print(customer_orders[['ProductName', 'Quantity', 'Price']].head())
        
        print(f"\n📋 Sample review data for customer {customer_id}:")
        print(customer_reviews[['PetName', 'PetType', 'Breed', 'Gender', 'ProductName', 'Rating']].head())
        
        print(f"\n🎉 Preprocessing completed successfully!")
        print(f"📁 Processed files:")
        print(f"   - {processed_order_path}")
        print(f"   - {processed_review_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during preprocessing: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n💥 Preprocessing failed. Please check the error messages above.")
        exit(1) 