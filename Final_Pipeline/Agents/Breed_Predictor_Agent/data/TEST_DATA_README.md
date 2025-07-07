# Test Data Documentation

This document describes the curated test dataset used for breed prediction testing.

## Dataset: test_data_1pet.json

The test dataset contains 3 carefully selected customers with rich purchase histories and diverse pet profiles. These customers were chosen from the full `pet_data_1pet.json` dataset based on:

1. **Purchase Volume**: High number of orders indicating rich data
2. **Health Indicators**: Multiple health-related purchase patterns
3. **Diversity**: Different age, size, and gender profiles for comprehensive testing

## Selected Test Cases

### 1. Caden (Customer 74699010)
- **Profile**: 3.9 years old, Medium size, Male
- **Purchase Data**: 53 orders spanning multiple categories
- **Health Indicators**: 5 indicators (dental, skin, joint, weight, digestive)
- **Top Categories**: Toys (31 orders), Food (22 orders)
- **Why Selected**: Youngest pet with highest health indicator diversity

### 2. Pickles (Customer 13384731)  
- **Profile**: 11.3 years old, Extra Small size, Female
- **Purchase Data**: 53 orders with consistent patterns
- **Health Indicators**: 4 indicators (weight, dental, skin, joint)
- **Top Categories**: Food (31 orders), Other (18 orders)
- **Why Selected**: Senior small breed with weight management focus

### 3. Charlee (Customer 4868964)
- **Profile**: 14.0 years old, Extra Large size, Female  
- **Purchase Data**: 35 orders with senior-focused products
- **Health Indicators**: 6 indicators (dental, skin, joint, weight, digestive, senior)
- **Top Categories**: Food (20 orders), Grooming (12 orders)
- **Why Selected**: Oldest pet with most comprehensive health indicators

## Data Structure

Each test case follows the same structure as the main dataset:

```json
{
  "customer_id": {
    "pets": {
      "pet_id": {
        "name": "Pet Name",
        "age": 0.0,
        "birthday": "YYYY-MM-DD",
        "size": "SIZE_CODE",
        "gender": "GENDER",
        "breed": "Unknown",
        "purchase_history": [...],
        "health_indicators": [...]
      }
    }
  }
}
```

## Usage

This test dataset is used by:
- `test_predictor.py` - Main testing script
- `demo.py` - Demonstration system
- Any testing that requires consistent, high-quality data

The test data provides reliable benchmarks for evaluating breed prediction accuracy and system performance.

## Important Note

All breed information has been completely removed from this dataset. The `breed` field is always set to "Unknown" to ensure the prediction system cannot access actual breed data during testing.
