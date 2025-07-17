#!/usr/bin/env python3
"""
Snowflake Customer Query Executor

This script connects to a Snowflake database, loads SQL query templates from a JSON file,
and executes them for a specified customer ID.

Author: Chewy Playback Team
Date: 2024
"""

import json
import argparse
import sys
import os
from typing import Dict, List, Any, Optional

# Try to import snowflake connector, but don't fail if not installed
try:
    import snowflake.connector
    from snowflake.connector.errors import ProgrammingError, DatabaseError
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    print("⚠️  Warning: snowflake-connector-python not installed.")
    print("   Install with: pip install snowflake-connector-python")
    print("   The script will show help but cannot connect to Snowflake without it.\n")

# Try to import dotenv for environment variable loading
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  Warning: python-dotenv not installed.")
    print("   Install with: pip install python-dotenv")
    print("   Credentials will need to be set as environment variables manually.\n")


def load_environment_variables():
    """
    Loads environment variables from .env file if available.
    """
    if DOTENV_AVAILABLE:
        # Load .env file if it exists
        if os.path.exists('.env'):
            load_dotenv()
            print("✅ Loaded credentials from .env file")
        else:
            print("⚠️  No .env file found. Using system environment variables.")
    else:
        print("⚠️  python-dotenv not available. Using system environment variables.")


def get_snowflake_connection():
    """
    Establishes a connection to Snowflake database using environment variables.
    
    Returns:
        snowflake.connector.SnowflakeConnection: Active Snowflake connection
        
    Raises:
        Exception: If connection fails or Snowflake connector not available
    """
    if not SNOWFLAKE_AVAILABLE:
        raise ImportError("snowflake-connector-python is not installed. Please install it first.")
    
    # Load environment variables
    load_environment_variables()
    
    # Get credentials from environment variables
    user = os.getenv('SNOWFLAKE_USER')
    password = os.getenv('SNOWFLAKE_PASSWORD')
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
    database = os.getenv('SNOWFLAKE_DATABASE')
    schema = os.getenv('SNOWFLAKE_SCHEMA')
    
    # Check if all required credentials are available
    missing_credentials = []
    if not user:
        missing_credentials.append('SNOWFLAKE_USER')
    if not account:
        missing_credentials.append('SNOWFLAKE_ACCOUNT')
    if not warehouse:
        missing_credentials.append('SNOWFLAKE_WAREHOUSE')
    if not database:
        missing_credentials.append('SNOWFLAKE_DATABASE')
    if not schema:
        missing_credentials.append('SNOWFLAKE_SCHEMA')
    
    # Password is optional if using external browser authentication
    if not password:
        print("⚠️  No password provided - using external browser authentication")
        password = None
    
    if missing_credentials:
        print(f"❌ Missing required environment variables: {', '.join(missing_credentials)}")
        print("Please set these in your .env file or as system environment variables.")
        print("\nExample .env file:")
        print("SNOWFLAKE_USER=your_username")
        print("SNOWFLAKE_PASSWORD=your_password")
        print("SNOWFLAKE_ACCOUNT=your_account")
        print("SNOWFLAKE_WAREHOUSE=your_warehouse")
        print("SNOWFLAKE_DATABASE=your_database")
        print("SNOWFLAKE_SCHEMA=your_schema")
        raise ValueError(f"Missing credentials: {', '.join(missing_credentials)}")
    
    try:
        # Build connection parameters (don't include warehouse in initial connection)
        conn_params = {
            'user': user,
            'account': account
        }
        
        # Add password if provided, otherwise use external browser auth
        if password:
            conn_params['password'] = password
        else:
            conn_params['authenticator'] = 'externalbrowser'
        
        connection = snowflake.connector.connect(**conn_params)
        
        # Set warehouse, database, and schema after connection
        cursor = connection.cursor()
        try:
            cursor.execute(f'USE WAREHOUSE "{warehouse}"')
            print(f"✅ Successfully set warehouse to {warehouse}")
        except Exception as warehouse_error:
            print(f"⚠️  Couldn't set warehouse {warehouse}: {warehouse_error}")
            print("   Continuing with default warehouse...")
        
        try:
            cursor.execute(f'USE DATABASE "{database}"')
            cursor.execute(f'USE SCHEMA "{schema}"')
            print(f"✅ Successfully set database to {database} and schema to {schema}")
        except Exception as db_error:
            print(f"⚠️  Couldn't set database/schema: {db_error}")
            print("   Continuing with current database/schema...")
        
        cursor.close()
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to Snowflake: {str(e)}")
        raise


def load_queries(json_file_path: str = 'customer_queries.json') -> Dict[str, str]:
    """
    Loads SQL query templates from a JSON file.
    
    Args:
        json_file_path (str): Path to the JSON file containing query templates
        
    Returns:
        Dict[str, str]: Dictionary mapping query names to SQL templates
        
    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON file is malformed
    """
    try:
        with open(json_file_path, 'r') as file:
            queries = json.load(file)
        print(f"✅ Successfully loaded {len(queries)} query templates from {json_file_path}")
        return queries
    except FileNotFoundError:
        print(f"❌ Query file not found: {json_file_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format in {json_file_path}: {str(e)}")
        raise


def execute_query(connection, 
                 query: str, 
                 query_name: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query against Snowflake and returns the results.
    
    Args:
        connection: Active Snowflake connection
        query (str): SQL query to execute
        query_name (str): Name/identifier for the query (for logging)
        
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries
        
    Raises:
        ProgrammingError: If query has syntax errors
        DatabaseError: If database operation fails
    """
    if not SNOWFLAKE_AVAILABLE:
        raise ImportError("snowflake-connector-python is not installed. Please install it first.")
    
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Fetch column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all rows and convert to list of dictionaries
        rows = cursor.fetchall()
        results = []
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            results.append(row_dict)
        
        cursor.close()
        print(f"✅ Query '{query_name}' executed successfully - {len(results)} rows returned")
        return results
        
    except ProgrammingError as e:
        print(f"❌ SQL Error in query '{query_name}': {str(e)}")
        raise
    except DatabaseError as e:
        print(f"❌ Database Error in query '{query_name}': {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error executing query '{query_name}': {str(e)}")
        raise


def get_customer_data(customer_id: str, 
                     queries: Dict[str, str], 
                     connection) -> Dict[str, List[Dict[str, Any]]]:
    """
    Executes all queries for a given customer ID and returns the results.
    
    Args:
        customer_id (str): Customer ID to query for
        queries (Dict[str, str]): Dictionary of query templates
        connection: Active Snowflake connection
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary mapping query names to results
    """
    results = {}
    
    for query_name, query_template in queries.items():
        try:
            # Format query with customer_id
            formatted_query = query_template.format(customer_id=customer_id)
            
            # Execute the query
            query_results = execute_query(connection, formatted_query, query_name)
            results[query_name] = query_results
            
        except Exception as e:
            print(f"❌ Failed to execute query '{query_name}': {str(e)}")
            results[query_name] = []  # Empty results for failed queries
    
    return results


def print_results(results: Dict[str, List[Dict[str, Any]]], customer_id: str):
    """
    Prints the query results in a formatted way.
    
    Args:
        results (Dict[str, List[Dict[str, Any]]]): Query results
        customer_id (str): Customer ID that was queried
    """
    print(f"\n{'='*60}")
    print(f"QUERY RESULTS FOR CUSTOMER ID: {customer_id}")
    print(f"{'='*60}")
    
    for query_name, query_results in results.items():
        print(f"\n📊 {query_name.upper()}")
        print(f"{'-'*40}")
        
        if not query_results:
            print("No results returned")
            continue
            
        # Print column headers
        if query_results:
            headers = list(query_results[0].keys())
            header_str = " | ".join(f"{h:<15}" for h in headers)
            print(header_str)
            print("-" * len(header_str))
            
            # Print data rows (limit to first 10 for readability)
            for i, row in enumerate(query_results[:10]):
                row_str = " | ".join(f"{str(v):<15}" for v in row.values())
                print(row_str)
                
            if len(query_results) > 10:
                print(f"... and {len(query_results) - 10} more rows")
        
        print(f"Total rows: {len(query_results)}")


def main():
    """
    Main function that orchestrates the entire process.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Execute Snowflake queries for a customer ID',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python snowflake_customer_queries.py
  python snowflake_customer_queries.py --customer-id 12345
  python snowflake_customer_queries.py -c 12345 --json-file custom_queries.json

Prerequisites:
  - Install snowflake-connector-python: pip install snowflake-connector-python
  - Create .env file with Snowflake credentials (see example below)
  - Ensure customer_queries.json exists with query templates

Environment Variables (.env file):
  SNOWFLAKE_USER=your_username
  SNOWFLAKE_PASSWORD=your_password
  SNOWFLAKE_ACCOUNT=your_account
  SNOWFLAKE_WAREHOUSE=your_warehouse
  SNOWFLAKE_DATABASE=your_database
  SNOWFLAKE_SCHEMA=your_schema
        """
    )
    parser.add_argument(
        '--customer-id', '-c',
        type=str,
        help='Customer ID to query for'
    )
    parser.add_argument(
        '--json-file', '-j',
        type=str,
        default='customer_queries.json',
        help='Path to JSON file containing query templates (default: customer_queries.json)'
    )
    
    args = parser.parse_args()
    
    # If just showing help, don't require Snowflake connector
    if len(sys.argv) == 1 or '--help' in sys.argv or '-h' in sys.argv:
        return
    
    # Check if Snowflake connector is available
    if not SNOWFLAKE_AVAILABLE:
        print("❌ Cannot proceed without snowflake-connector-python")
        print("   Install with: pip install snowflake-connector-python")
        sys.exit(1)
    
    # Get customer ID from command line or user input
    customer_id = args.customer_id
    if not customer_id:
        customer_id = input("Enter customer ID: ").strip()
        if not customer_id:
            print("❌ No customer ID provided. Exiting.")
            sys.exit(1)
    
    try:
        # Load query templates
        queries = load_queries(args.json_file)
        
        # Establish Snowflake connection
        connection = get_snowflake_connection()
        
        # Execute queries for the customer
        results = get_customer_data(customer_id, queries, connection)
        
        # Print results
        print_results(results, customer_id)
        
        # Close connection
        connection.close()
        print("\n✅ All operations completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 