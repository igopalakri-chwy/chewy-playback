#!/usr/bin/env python3

# Test script for French Bulldog reordering functionality

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

def reorder_breeds_for_french_bulldog_filter(breed_distribution):
    """Reorder breed predictions so French Bulldog appears in the middle"""
    if not breed_distribution:
        return breed_distribution
    
    # Convert to list of tuples for easier manipulation
    breeds = list(breed_distribution.items())
    
    # Find French Bulldog (check for various possible keys)
    french_bulldog_key = None
    for breed_key, percentage in breeds:
        if (breed_key.lower() in ['frenchbulldog', 'french_bulldog', 'french bulldog'] or 
            format_breed_name_simple_filter(breed_key).lower() == 'french bulldog'):
            french_bulldog_key = breed_key
            break
    
    if not french_bulldog_key:
        # If French Bulldog not found, return original order
        return breed_distribution
    
    # Remove French Bulldog from the list
    breeds_without_french = [(k, v) for k, v in breeds if k != french_bulldog_key]
    french_bulldog_percentage = breed_distribution[french_bulldog_key]
    
    # Calculate middle position
    total_breeds = len(breeds)
    middle_index = total_breeds // 2
    
    # Create new ordered list
    reordered_breeds = []
    
    # Add breeds before French Bulldog
    for i in range(middle_index):
        if i < len(breeds_without_french):
            reordered_breeds.append(breeds_without_french[i])
    
    # Add French Bulldog in the middle
    reordered_breeds.append((french_bulldog_key, french_bulldog_percentage))
    
    # Add remaining breeds after French Bulldog
    for i in range(middle_index, len(breeds_without_french)):
        reordered_breeds.append(breeds_without_french[i])
    
    # Convert back to dictionary
    return dict(reordered_breeds)

# Test cases
def test_french_bulldog_reordering():
    print("Testing French Bulldog reordering functionality...")
    
    # Test case 1: French Bulldog in the middle of 5 breeds
    test_breeds = {
        'goldenRetriever': 25,
        'labradorRetriever': 20,
        'frenchBulldog': 30,
        'poodle': 15,
        'beagle': 10
    }
    
    print(f"\nOriginal order: {list(test_breeds.keys())}")
    reordered = reorder_breeds_for_french_bulldog_filter(test_breeds)
    print(f"Reordered: {list(reordered.keys())}")
    
    # Check if French Bulldog is in the middle
    breeds_list = list(reordered.keys())
    french_index = breeds_list.index('frenchBulldog')
    middle_index = len(breeds_list) // 2
    
    print(f"French Bulldog position: {french_index}, Middle position: {middle_index}")
    print(f"✅ French Bulldog is in the middle: {french_index == middle_index}")
    
    # Test case 2: French Bulldog not present
    test_breeds_no_french = {
        'goldenRetriever': 30,
        'labradorRetriever': 25,
        'poodle': 20,
        'beagle': 15,
        'bulldog': 10
    }
    
    print(f"\nOriginal order (no French Bulldog): {list(test_breeds_no_french.keys())}")
    reordered_no_french = reorder_breeds_for_french_bulldog_filter(test_breeds_no_french)
    print(f"Reordered (should be same): {list(reordered_no_french.keys())}")
    print(f"✅ No change when French Bulldog not present: {list(test_breeds_no_french.keys()) == list(reordered_no_french.keys())}")
    
    # Test case 3: French Bulldog with different naming
    test_breeds_different_name = {
        'goldenRetriever': 25,
        'french_bulldog': 30,
        'labradorRetriever': 20,
        'poodle': 15,
        'beagle': 10
    }
    
    print(f"\nOriginal order (french_bulldog): {list(test_breeds_different_name.keys())}")
    reordered_different = reorder_breeds_for_french_bulldog_filter(test_breeds_different_name)
    print(f"Reordered: {list(reordered_different.keys())}")
    
    breeds_list_different = list(reordered_different.keys())
    french_index_different = breeds_list_different.index('french_bulldog')
    middle_index_different = len(breeds_list_different) // 2
    
    print(f"French Bulldog position: {french_index_different}, Middle position: {middle_index_different}")
    print(f"✅ French Bulldog is in the middle: {french_index_different == middle_index_different}")

if __name__ == "__main__":
    test_french_bulldog_reordering() 