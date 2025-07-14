#!/usr/bin/env python3
"""
Test script for ZIP Code Visual Aesthetics Generator
Demonstrates how to use the generator with different ZIP codes.
"""

from zip_visual_aesthetics import ZIPVisualAestheticsGenerator


def test_zip_aesthetics():
    """Test the ZIP visual aesthetics generator with different ZIP codes."""
    
    # Initialize the generator
    try:
        generator = ZIPVisualAestheticsGenerator()
        print("✅ ZIP Visual Aesthetics Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return
    
    # Test ZIP codes
    test_zip_codes = [
        "10001",  # New York, NY
        "90210",  # Beverly Hills, CA
        "33139",  # Miami Beach, FL
        "60601",  # Chicago, IL
        "98101"   # Seattle, WA
    ]
    
    print("\n🎨 Testing ZIP Code Visual Aesthetics Generator")
    print("=" * 50)
    
    for zip_code in test_zip_codes:
        print(f"\n📍 ZIP Code: {zip_code}")
        print("-" * 30)
        
        try:
            aesthetics = generator.generate_aesthetics(zip_code)
            print(f"✅ Successfully generated aesthetics for {zip_code}")
            
            # The results are already printed in the expected format by the generator
            # But we can also access them programmatically:
            print(f"   Visual Style: {aesthetics['visual_style']}")
            print(f"   Color Texture: {aesthetics['color_texture']}")
            print(f"   Art Style: {aesthetics['art_style']}")
            
        except Exception as e:
            print(f"❌ Error processing ZIP code {zip_code}: {e}")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_zip_aesthetics() 