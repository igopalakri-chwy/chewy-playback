#!/usr/bin/env python3
"""
Test the fix for the customer_id scope error in _parse_llm_response method.
"""

import sys
import json
from pathlib import Path

# Add the pipeline path to sys.path
current_dir = Path(__file__).parent
pipeline_path = current_dir / 'Final_Pipeline'
sys.path.append(str(pipeline_path))

from chewy_playback_pipeline import OrderIntelligenceAgent

def test_parse_llm_response_with_valid_json():
    """Test _parse_llm_response with valid JSON response."""
    
    agent = OrderIntelligenceAgent("fake_api_key")
    
    # Valid JSON response
    valid_json_response = '''
    Here is the analysis:
    {
        "PetType": "dog",
        "PetTypeScore": 0.8,
        "Breed": "Mixed",
        "BreedScore": 0.6
    }
    '''
    
    customer_id = "12345"
    
    try:
        result = agent._parse_llm_response(valid_json_response, customer_id)
        print("✅ SUCCESS: Valid JSON parsed correctly")
        print(f"   Result: {result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Valid JSON parsing failed: {e}")
        return False

def test_parse_llm_response_with_invalid_json():
    """Test _parse_llm_response with invalid JSON response (should trigger error handling)."""
    
    agent = OrderIntelligenceAgent("fake_api_key")
    
    # Invalid response with no JSON
    invalid_response = "This is just text with no JSON structure"
    
    customer_id = "12345"
    
    try:
        result = agent._parse_llm_response(invalid_response, customer_id)
        print("❌ FAILED: Invalid JSON should have raised an exception")
        return False
    except RuntimeError as e:
        # Check if the error message contains the customer_id (proving scope is fixed)
        if customer_id in str(e):
            print("✅ SUCCESS: Invalid JSON triggered correct error with customer_id")
            print(f"   Error message: {str(e)}")
            return True
        else:
            print(f"❌ FAILED: Error message missing customer_id: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected exception type: {type(e).__name__}: {e}")
        return False

def test_parse_llm_response_with_malformed_json():
    """Test _parse_llm_response with malformed JSON (should trigger JSON decode error)."""
    
    agent = OrderIntelligenceAgent("fake_api_key")
    
    # Malformed JSON
    malformed_json_response = '''
    Here is the analysis:
    {
        "PetType": "dog",
        "PetTypeScore": 0.8,
        "Breed": "Mixed"  // missing closing brace
    '''
    
    customer_id = "67890"
    
    try:
        result = agent._parse_llm_response(malformed_json_response, customer_id)
        print("❌ FAILED: Malformed JSON should have raised an exception")
        return False
    except RuntimeError as e:
        # Check if the error message contains the customer_id (proving scope is fixed)
        if customer_id in str(e):
            print("✅ SUCCESS: Malformed JSON triggered correct error with customer_id")
            print(f"   Error message: {str(e)}")
            return True
        else:
            print(f"❌ FAILED: Error message missing customer_id: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected exception type: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("Testing _parse_llm_response customer_id scope fix")
    print("=" * 60)
    
    # Test valid JSON
    test1_passed = test_parse_llm_response_with_valid_json()
    
    print()
    
    # Test invalid JSON (no JSON found)
    test2_passed = test_parse_llm_response_with_invalid_json()
    
    print()
    
    # Test malformed JSON (JSON decode error)
    test3_passed = test_parse_llm_response_with_malformed_json()
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"  Valid JSON test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Invalid JSON test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"  Malformed JSON test: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 ALL TESTS PASSED! The customer_id scope fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. The fix needs further investigation.")