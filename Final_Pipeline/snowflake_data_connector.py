#!/usr/bin/env python3
"""
Snowflake Data Connector for Chewy Playback Pipeline
Pulls customer data directly from Snowflake and formats it for the pipeline agents.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Try to import Snowflake connector
try:
    import snowflake.connector
    from snowflake.connector.errors import ProgrammingError, DatabaseError
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    print("⚠️  snowflake-connector-python not installed. Install with: pip install snowflake-connector-python")


class SnowflakeDataConnector:
    """
    Connects to Snowflake and pulls customer data for the Chewy Playback Pipeline.
    """
    
    def __init__(self):
        """Initialize the Snowflake data connector."""
        if not SNOWFLAKE_AVAILABLE:
            raise ImportError("snowflake-connector-python is not installed. Please install it first.")
        
        self.connection = None
        self.customer_queries = self._load_customer_queries()
        self._load_environment_variables()
    
    def _load_environment_variables(self):
        """Load environment variables from .env file or system."""
        try:
            load_dotenv()
            print("✅ Loaded credentials from .env file")
        except ImportError:
            print("⚠️  python-dotenv not available. Using system environment variables.")
        
        # Check for required environment variables
        self.user = os.getenv('SNOWFLAKE_USER')
        self.password = os.getenv('SNOWFLAKE_PASSWORD')
        self.account = os.getenv('SNOWFLAKE_ACCOUNT')
        self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
        self.database = os.getenv('SNOWFLAKE_DATABASE')
        self.schema = os.getenv('SNOWFLAKE_SCHEMA')
        self.authenticator = os.getenv('SNOWFLAKE_AUTHENTICATOR', 'externalbrowser')
        
        if not all([self.user, self.account, self.warehouse, self.database]):
            raise ValueError("Missing required Snowflake environment variables. Please check your .env file.")
        
        # Print connection info for debugging
        print(f"🔗 Snowflake Config:")
        print(f"   User: {self.user}")
        print(f"   Account: {self.account}")
        print(f"   Database: {self.database}")
        print(f"   Warehouse: {self.warehouse}")
        print(f"   Authenticator: {self.authenticator}")
    
    def _load_customer_queries(self) -> Dict[str, str]:
        """Load SQL query templates from JSON file."""
        try:
            # Try to load from Final_Pipeline directory first
            queries_path = Path(__file__).parent / "customer_queries.json"
            if not queries_path.exists():
                # Fall back to parent directory
                queries_path = Path(__file__).parent.parent / "customer_queries.json"
            
            with open(queries_path, 'r') as file:
                queries = json.load(file)
            print(f"✅ Successfully loaded {len(queries)} query templates from {queries_path}")
            return queries
        except Exception as e:
            print(f"❌ Error loading customer queries: {e}")
            raise
    
    def connect(self) -> bool:
        """Establish connection to Snowflake."""
        try:
            print("🔗 Connecting to Snowflake with browser authentication...")
            
            # Build connection parameters matching working script pattern
            credentials = {
                "user": self.user,
                "account": self.account,
                "authenticator": self.authenticator,
                "database": self.database,
                "warehouse": self.warehouse,
                "insecure_mode": True,  # For corporate environments
            }
            
            # Add schema if provided
            if self.schema:
                credentials["schema"] = self.schema
            
            # Add password if provided (but typically not needed for SSO)
            if self.password:
                credentials['password'] = self.password
            
            print("📖 Opening browser for authentication...")
            self.connection = snowflake.connector.connect(**credentials)
            print("✅ Connected to Snowflake successfully!")
            
            # Test the connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
            result = cursor.fetchone()
            print(f"✅ Active context: warehouse={result[0]}, database={result[1]}, schema={result[2]}")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Snowflake: {str(e)}")
            return False
    
    def disconnect(self):
        """Close the Snowflake connection."""
        if self.connection:
            self.connection.close()
            print("✅ Disconnected from Snowflake")
    
    def get_customer_data(self, customer_id: str, query_keys: list = None) -> Dict[str, Any]:
        """
        Get all data for a specific customer from Snowflake.
        
        Args:
            customer_id (str): Customer ID to query for
            query_keys (list, optional): List of query keys to run. If None, run all.
            
        Returns:
            Dict[str, Any]: Dictionary containing all customer data
        """
        if not self.connection:
            if not self.connect():
                raise RuntimeError("Failed to connect to Snowflake")
        
        customer_data = {}
        
        try:
            queries_to_run = self.customer_queries.items() if query_keys is None else [(k, self.customer_queries[k]) for k in query_keys if k in self.customer_queries]
            for query_name, query_template in queries_to_run:
                formatted_query = query_template.format(customer_id=customer_id)
                cursor = self.connection.cursor()
                cursor.execute(formatted_query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    results.append(row_dict)
                cursor.close()
                customer_data[query_name] = results
                print(f"✅ Query '{query_name}' executed successfully - {len(results)} rows returned")
        except Exception as e:
            print(f"❌ Error executing queries for customer {customer_id}: {e}")
            raise
        
        return customer_data
    
    def format_data_for_pipeline(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Snowflake data into the format expected by the pipeline agents.
        
        Args:
            customer_id (str): Customer ID
            customer_data (Dict[str, Any]): Raw data from Snowflake
            
        Returns:
            Dict[str, Any]: Formatted data for pipeline agents
        """
        formatted_data = {
            'customer_id': customer_id,
            'order_data': [],
            'review_data': [],
            'pet_data': [],
            'address_data': {}
        }
        
        # Process get_cust_orders (order data - now returns top products by quantity)
        if 'get_cust_orders' in customer_data:
            for row in customer_data['get_cust_orders']:
                order_record = {
                    'CustomerID': str(customer_id),
                    'ProductID': str(row.get('PRODUCT_ID', '')),
                    'ProductName': str(row.get('NAME', '')),
                    'Quantity': int(row.get('TOTAL_QUANTITY', 1))
                }
                formatted_data['order_data'].append(order_record)
        
        # Process get_pet_profiles (pet data)
        if 'get_pet_profiles' in customer_data:
            for row in customer_data['get_pet_profiles']:
                pet_record = {
                    'CustomerID': str(row.get('CUSTOMER_ID', customer_id)),
                    'PetName': str(row.get('PET_NAME', '')),
                    'PetType': str(row.get('PET_TYPE', '')),
                    'PetBreed': str(row.get('PET_BREED', '')),
                    'Weight': str(row.get('WEIGHT', '')),
                    'Gender': str(row.get('GENDER', '')),
                    'PetAge': str(row.get('PET_AGE', '')),
                    'Medication': str(row.get('MEDICATION', ''))
                }
                formatted_data['pet_data'].append(pet_record)
        
        # Process get_cust_reviews (review data)
        if 'get_cust_reviews' in customer_data:
            for row in customer_data['get_cust_reviews']:
                review_record = {
                    'CustomerID': str(row.get('CUSTOMER_ID', customer_id)),
                    'ReviewID': str(row.get('REVIEW_ID', '')),
                    'ReviewTitle': str(row.get('REVIEW_TITLE', '')),
                    'ReviewText': str(row.get('REVIEW_TXT', ''))
                }
                formatted_data['review_data'].append(review_record)
        
        # Process get_cust_zipcode (address data)
        if 'get_cust_zipcode' in customer_data and customer_data['get_cust_zipcode']:
            address_row = customer_data['get_cust_zipcode'][0]
            formatted_data['address_data'] = {
                'customer_id': str(address_row.get('CUSTOMER_ID', customer_id)),
                'zip_code': str(address_row.get('CUSTOMER_ADDRESS_ZIP', '')),
                'city': str(address_row.get('CUSTOMER_ADDRESS_CITY', ''))
            }
        
        # Process get_yearly_food_count (food consumption data)
        if 'get_yearly_food_count' in customer_data:
            formatted_data['food_consumption_data'] = customer_data['get_yearly_food_count']
        
        return formatted_data
    
    def get_customer_orders_dataframe(self, customer_id: str) -> pd.DataFrame:
        """
        Get customer orders as a pandas DataFrame for the pipeline agents.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            pd.DataFrame: Customer orders data
        """
        customer_data = self.get_customer_data(customer_id)
        formatted_data = self.format_data_for_pipeline(customer_id, customer_data)
        
        if formatted_data['order_data'] and len(formatted_data['order_data']) > 0:
            return pd.DataFrame(formatted_data['order_data'])
        else:
            return pd.DataFrame()
    
    def get_customer_reviews_dataframe(self, customer_id: str) -> pd.DataFrame:
        """
        Get customer reviews as a pandas DataFrame for the pipeline agents.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            pd.DataFrame: Customer reviews data
        """
        customer_data = self.get_customer_data(customer_id)
        formatted_data = self.format_data_for_pipeline(customer_id, customer_data)
        
        if formatted_data['review_data'] and len(formatted_data['review_data']) > 0:
            return pd.DataFrame(formatted_data['review_data'])
        else:
            return pd.DataFrame()
    
    def get_customer_pets_dataframe(self, customer_id: str) -> pd.DataFrame:
        """
        Get customer pets as a pandas DataFrame for the pipeline agents.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            pd.DataFrame: Customer pets data
        """
        customer_data = self.get_customer_data(customer_id)
        formatted_data = self.format_data_for_pipeline(customer_id, customer_data)
        
        if formatted_data['pet_data'] and len(formatted_data['pet_data']) > 0:
            return pd.DataFrame(formatted_data['pet_data'])
        else:
            return pd.DataFrame()
    
    def get_customer_address(self, customer_id: str) -> Dict[str, str]:
        """
        Get customer's primary address information.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            Dict[str, str]: Address information with zip_code and city
        """
        customer_data = self.get_customer_data(customer_id)
        formatted_data = self.format_data_for_pipeline(customer_id, customer_data)
        
        return formatted_data['address_data']
    
    def get_customer_food_consumption(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get customer's food consumption data from get_yearly_food_count.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            List[Dict[str, Any]]: Food consumption data
        """
        customer_data = self.get_customer_data(customer_id)
        formatted_data = self.format_data_for_pipeline(customer_id, customer_data)
        
        return formatted_data.get('food_consumption_data', [])
    
    def customer_has_reviews(self, customer_id: str) -> bool:
        """Check if a customer has any reviews."""
        try:
            reviews_df = self.get_customer_reviews_dataframe(customer_id)
            return not reviews_df.empty
        except Exception as e:
            print(f"Error checking reviews for customer {customer_id}: {e}")
            return False
    
    def _convert_query_to_dataframe(self, query_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert query results to pandas DataFrame.
        
        Args:
            query_results (List[Dict[str, Any]]): List of dictionaries from query results
            
        Returns:
            pd.DataFrame: Converted dataframe
        """
        if not query_results:
            return pd.DataFrame()
        
        try:
            return pd.DataFrame(query_results)
        except Exception as e:
            print(f"Error converting query results to dataframe: {e}")
            return pd.DataFrame()


def main():
    """Test function for the Snowflake data connector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Snowflake Data Connector")
    parser.add_argument("--customer-id", required=True, help="Customer ID to test")
    
    args = parser.parse_args()
    
    try:
        connector = SnowflakeDataConnector()
        customer_data = connector.get_customer_data(args.customer_id)
        formatted_data = connector.format_data_for_pipeline(args.customer_id, customer_data)
        
        print(f"\n📊 Customer {args.customer_id} Data Summary:")
        print(f"  Orders: {len(formatted_data['order_data'])}")
        print(f"  Pets: {len(formatted_data['pet_data'])}")
        print(f"  Reviews: {len(formatted_data['review_data'])}")
        print(f"  Address: {formatted_data['address_data']}")
        
        connector.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 