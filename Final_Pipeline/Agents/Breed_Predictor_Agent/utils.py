"""
Utility functions for the Breed Predictor project.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import json
import os

def analyze_purchase_patterns(reviews_df: pd.DataFrame) -> Dict:
    """Analyze purchase patterns across all customers."""
    analysis = {
        'total_reviews': len(reviews_df),
        'unique_customers': reviews_df['customer_id'].nunique(),
        'unique_pets': reviews_df['pet_id'].nunique(),
        'category_distribution': reviews_df['product_category'].value_counts().to_dict(),
        'average_rating': reviews_df['rating'].mean() if 'rating' in reviews_df.columns else None,
        'reviews_per_pet': reviews_df.groupby('pet_id').size().to_dict()
    }
    return analysis

def create_breed_comparison_chart(predictions: Dict[str, Dict[str, float]], 
                                breed_definitions: Dict, 
                                save_path: str = None) -> None:
    """Create a comparison chart of breed predictions for multiple pets."""
    
    # Prepare data for plotting
    pets = list(predictions.keys())
    all_breeds = set()
    for pred in predictions.values():
        all_breeds.update(pred.keys())
    
    # Create DataFrame for plotting
    plot_data = []
    for pet_id, breed_dist in predictions.items():
        for breed, percentage in breed_dist.items():
            breed_name = breed_definitions.get(breed, {}).get('name', breed)
            plot_data.append({
                'Pet': pet_id,
                'Breed': breed_name,
                'Percentage': percentage
            })
    
    df = pd.DataFrame(plot_data)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    sns.barplot(data=df, x='Pet', y='Percentage', hue='Breed')
    plt.title('Breed Predictions by Pet')
    plt.ylabel('Percentage (%)')
    plt.xlabel('Pet ID')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()

def generate_breed_health_report(breed_definitions: Dict) -> pd.DataFrame:
    """Generate a report of breed health characteristics."""
    
    health_data = []
    for breed_key, breed_info in breed_definitions.items():
        health_data.append({
            'Breed': breed_info.get('name', breed_key),
            'Health_Issues_Score': int(breed_info.get('health_issues', 3)),
            'Exercise_Needs': int(breed_info.get('exercise_needs', 3)),
            'Grooming_Needs': int(breed_info.get('grooming_needs', 3)),
            'Good_With_Kids': int(breed_info.get('good_with_kids', 3)),
            'Life_Expectancy': breed_info.get('life_expectancy', 'Unknown'),
            'Weight': breed_info.get('weight', 'Unknown')
        })
    
    return pd.DataFrame(health_data)

def export_predictions_to_csv(predictions: Dict[str, Dict[str, float]], 
                            breed_definitions: Dict,
                            output_path: str) -> None:
    """Export breed predictions to CSV format."""
    
    export_data = []
    for pet_id, breed_dist in predictions.items():
        for breed_key, percentage in breed_dist.items():
            breed_name = breed_definitions.get(breed_key, {}).get('name', breed_key)
            export_data.append({
                'Pet_ID': pet_id,
                'Breed_Key': breed_key,
                'Breed_Name': breed_name,
                'Percentage': percentage
            })
    
    df = pd.DataFrame(export_data)
    df.to_csv(output_path, index=False)
    print(f"Predictions exported to {output_path}")

def validate_breed_data(breed_definitions: Dict) -> List[str]:
    """Validate breed definition data and return any issues found."""
    issues = []
    
    required_fields = ['name', 'health_issues', 'exercise_needs', 'weight']
    
    for breed_key, breed_data in breed_definitions.items():
        for field in required_fields:
            if field not in breed_data:
                issues.append(f"Missing '{field}' for breed: {breed_key}")
        
        # Check if numeric fields are valid
        numeric_fields = ['health_issues', 'exercise_needs', 'grooming_needs']
        for field in numeric_fields:
            if field in breed_data:
                try:
                    value = int(breed_data[field])
                    if not 1 <= value <= 5:
                        issues.append(f"Invalid {field} value for {breed_key}: {value} (should be 1-5)")
                except (ValueError, TypeError):
                    issues.append(f"Invalid {field} type for {breed_key}: {breed_data[field]}")
    
    return issues

def get_breed_recommendations(pet_data: Dict, breed_definitions: Dict, 
                            top_n: int = 3) -> List[Dict]:
    """Get breed recommendations based on pet characteristics."""
    
    recommendations = []
    pet_size = pet_data.get('size', '').lower()
    pet_health_issues = pet_data.get('health_issues', [])
    
    for breed_key, breed_info in breed_definitions.items():
        score = 0
        reasons = []
        
        # Size matching
        breed_weight = breed_info.get('weight', '').lower()
        if pet_size == 'small' and any(term in breed_weight for term in ['4-6', '6-9', 'small']):
            score += 3
            reasons.append("Size match (small)")
        elif pet_size == 'large' and any(term in breed_weight for term in ['65-75', '80', 'large']):
            score += 3
            reasons.append("Size match (large)")
        elif pet_size == 'medium':
            score += 1
            reasons.append("Size compatible")
        
        # Health issues matching
        health_desc = breed_info.get('health_description', '').lower()
        for issue in pet_health_issues:
            if issue.lower() in health_desc:
                score += 2
                reasons.append(f"Common health issue: {issue}")
        
        # Life expectancy consideration
        if pet_data.get('age', 0) >= 7:  # Senior dog
            life_exp = breed_info.get('life_expectancy', '')
            if '12' in life_exp or '14' in life_exp or '16' in life_exp:
                score += 1
                reasons.append("Good longevity for senior dog")
        
        recommendations.append({
            'breed_key': breed_key,
            'breed_name': breed_info.get('name', breed_key),
            'score': score,
            'reasons': reasons
        })
    
    # Sort by score and return top N
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:top_n] 