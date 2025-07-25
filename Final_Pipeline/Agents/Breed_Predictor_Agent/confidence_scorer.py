"""
Confidence Scorer for Breed Predictor
Evaluates prediction reliability based on data quality, sparsity, and consistency.
"""

import json
from typing import Dict, List, Tuple
from datetime import datetime
import math

class ConfidenceScorer:
    def __init__(self):
        """Initialize confidence scorer with scoring parameters."""
        
        # Minimum thresholds for reliable predictions
        self.min_purchases = 15  # Minimum purchases for medium confidence
        self.min_categories = 3  # Minimum product categories
        self.min_time_span = 90  # Minimum days of purchase history
        
        # Category importance weights
        self.category_weights = {
            'grooming': 3.0,     # High breed specificity
            'toys': 2.5,         # Good activity/size indicators
            'food': 1.5,         # Some breed specificity
            'accessories': 2.0,   # Size/style indicators
            'health': 3.0,       # Strong breed predisposition indicators
            'other': 1.0         # Low specificity
        }
        
        # Confidence level thresholds
        self.confidence_levels = {
            'very_high': 85,
            'high': 70,
            'medium': 50,
            'low': 30,
            'very_low': 15
        }
    
    def calculate_confidence(self, pet_data: Dict, purchase_history: List[Dict], 
                           predictions: Dict[str, float], prediction_metadata: Dict = None) -> Dict:
        """
        Calculate comprehensive confidence score for breed predictions.
        
        Returns:
            Dict with confidence score, level, factors, and recommendations
        """
        
        confidence_factors = {}
        
        # 1. Data Quantity Score (0-25 points)
        quantity_score = self._score_data_quantity(purchase_history)
        confidence_factors['data_quantity'] = quantity_score
        
        # 2. Data Quality Score (0-25 points)
        quality_score = self._score_data_quality(purchase_history)
        confidence_factors['data_quality'] = quality_score
        
        # 3. Data Diversity Score (0-20 points)
        diversity_score = self._score_data_diversity(purchase_history)
        confidence_factors['data_diversity'] = diversity_score
        
        # 4. Temporal Coverage Score (0-15 points)
        temporal_score = self._score_temporal_coverage(purchase_history)
        confidence_factors['temporal_coverage'] = temporal_score
        
        # 5. Prediction Consistency Score (0-15 points)
        consistency_score = self._score_prediction_consistency(predictions, prediction_metadata)
        confidence_factors['prediction_consistency'] = consistency_score
        
        # Calculate total confidence (0-100)
        total_confidence = sum(confidence_factors.values())
        
        # Apply penalties for critical issues
        penalties = self._calculate_penalties(pet_data, purchase_history, predictions)
        confidence_factors['penalties'] = penalties
        
        final_confidence = max(0, total_confidence - penalties)
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(final_confidence)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(confidence_factors, pet_data, purchase_history)
        
        return {
            'confidence_score': round(final_confidence, 1),
            'confidence_level': confidence_level,
            'factors': confidence_factors,
            'recommendations': recommendations,
            'reliability_flags': self._get_reliability_flags(confidence_factors, pet_data, purchase_history)
        }
    
    def _score_data_quantity(self, purchase_history: List[Dict]) -> float:
        """Score based on number of purchases (0-25 points)."""
        num_purchases = len(purchase_history)
        
        if num_purchases >= 50:
            return 25.0
        elif num_purchases >= 30:
            return 20.0 + (num_purchases - 30) * 0.25  # 20-25 points
        elif num_purchases >= 15:
            return 15.0 + (num_purchases - 15) * 0.33  # 15-20 points
        elif num_purchases >= 8:
            return 8.0 + (num_purchases - 8) * 1.0     # 8-15 points
        elif num_purchases >= 3:
            return 3.0 + (num_purchases - 3) * 1.0     # 3-8 points
        else:
            return num_purchases * 1.0                 # 0-3 points
    
    def _score_data_quality(self, purchase_history: List[Dict]) -> float:
        """Score based on purchase detail quality (0-25 points)."""
        if not purchase_history:
            return 0.0
        
        quality_indicators = 0
        total_possible = len(purchase_history) * 4  # 4 quality indicators per purchase
        
        for purchase in purchase_history:
            # Check for detailed item descriptions
            if len(purchase.get('item_desc', '')) > 100:
                quality_indicators += 1
            
            # Check for specific product names
            if len(purchase.get('item_name', '')) > 20:
                quality_indicators += 1
            
            # Check for category information
            if purchase.get('category', '').lower() != 'other':
                quality_indicators += 1
            
            # Check for date information
            if purchase.get('order_date'):
                quality_indicators += 1
        
        quality_ratio = quality_indicators / total_possible if total_possible > 0 else 0
        return quality_ratio * 25.0
    
    def _score_data_diversity(self, purchase_history: List[Dict]) -> float:
        """Score based on variety of purchase categories (0-20 points)."""
        categories = set()
        for purchase in purchase_history:
            category = purchase.get('category', 'other').lower()
            categories.add(category)
        
        num_categories = len(categories)
        
        if num_categories >= 5:
            return 20.0
        elif num_categories >= 4:
            return 16.0
        elif num_categories >= 3:
            return 12.0
        elif num_categories >= 2:
            return 8.0
        else:
            return 4.0
    
    def _score_temporal_coverage(self, purchase_history: List[Dict]) -> float:
        """Score based on time span of purchases (0-15 points)."""
        if len(purchase_history) < 2:
            return 2.0
        
        dates = []
        for purchase in purchase_history:
            try:
                date_str = purchase.get('order_date', '')
                if date_str:
                    dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
            except:
                continue
        
        if len(dates) < 2:
            return 2.0
        
        time_span = (max(dates) - min(dates)).days
        
        if time_span >= 365:  # Over a year
            return 15.0
        elif time_span >= 180:  # 6+ months
            return 12.0
        elif time_span >= 90:   # 3+ months
            return 9.0
        elif time_span >= 30:   # 1+ month
            return 6.0
        else:
            return 3.0
    
    def _score_prediction_consistency(self, predictions: Dict[str, float], 
                                    prediction_metadata: Dict = None) -> float:
        """Score based on prediction consistency and strength (0-15 points)."""
        if not predictions:
            return 0.0
        
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        
        # Check top prediction strength
        top_percentage = sorted_predictions[0][1] if sorted_predictions else 0
        
        if top_percentage >= 50:
            strength_score = 10.0
        elif top_percentage >= 30:
            strength_score = 7.0
        elif top_percentage >= 20:
            strength_score = 5.0
        else:
            strength_score = 2.0
        
        # Check prediction spread (lower spread = higher confidence)
        if len(sorted_predictions) >= 2:
            top_two_diff = sorted_predictions[0][1] - sorted_predictions[1][1]
            if top_two_diff >= 20:
                spread_score = 5.0
            elif top_two_diff >= 10:
                spread_score = 3.0
            else:
                spread_score = 1.0
        else:
            spread_score = 0.0
        
        return strength_score + spread_score
    
    def _calculate_penalties(self, pet_data: Dict, purchase_history: List[Dict], 
                           predictions: Dict[str, float]) -> float:
        """Calculate penalty points for reliability issues."""
        penalties = 0.0
        
        # Moderate data sparsity penalty (reduced from severe)
        if len(purchase_history) < 2:
            penalty = 15.0
            penalties += penalty
        elif len(purchase_history) < 5:
            penalty = 8.0
            penalties += penalty  
        elif len(purchase_history) < 10:
            penalty = 3.0
            penalties += penalty
        
        # Single category penalty (reduced)
        categories = set(p.get('category', 'other').lower() for p in purchase_history)
        if len(categories) == 1:
            penalty = 8.0  # Reduced from 15.0
            penalties += penalty
        
        # Generic purchases penalty (reduced threshold)
        other_count = sum(1 for p in purchase_history if p.get('category', '').lower() == 'other')
        if other_count > len(purchase_history) * 0.8:  # Changed from 70% to 80%
            penalty = 5.0  # Reduced from 10.0
            penalties += penalty
        
        # Size inconsistency penalty
        pet_size = pet_data.get('size', '').upper()
        if pet_size and predictions:
            # This would need breed size data to implement fully
            # For now, just flag if we have size info but low confidence
            pass
        
        # More reasonable prediction scores penalty
        if predictions:
            max_prediction = max(predictions.values())
            if max_prediction < 10:  # Very low threshold
                penalty = 10.0  # Reduced from 15.0
                penalties += penalty
            elif max_prediction < 20:  # Lowered threshold from 25
                penalty = 4.0  # Reduced from 8.0
                penalties += penalty
        
        return penalties
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numeric score to confidence level."""
        if score >= self.confidence_levels['very_high']:
            return 'Very High'
        elif score >= self.confidence_levels['high']:
            return 'High'
        elif score >= self.confidence_levels['medium']:
            return 'Medium'
        elif score >= self.confidence_levels['low']:
            return 'Low'
        else:
            return 'Very Low'
    
    def _generate_recommendations(self, factors: Dict, pet_data: Dict, 
                                purchase_history: List[Dict]) -> List[str]:
        """Generate recommendations to improve prediction confidence."""
        recommendations = []
        
        # Data quantity recommendations
        if factors.get('data_quantity', 0) < 15:
            recommendations.append("Collect more purchase history data (target: 15+ purchases)")
        
        # Data diversity recommendations
        if factors.get('data_diversity', 0) < 12:
            recommendations.append("Encourage purchases across different categories (toys, grooming, accessories)")
        
        # Temporal coverage recommendations
        if factors.get('temporal_coverage', 0) < 9:
            recommendations.append("Extend observation period to capture seasonal purchase patterns")
        
        # Quality recommendations
        if factors.get('data_quality', 0) < 15:
            recommendations.append("Ensure detailed product descriptions and categorization")
        
        # Specific category recommendations
        categories = set(p.get('category', 'other').lower() for p in purchase_history)
        missing_important = []
        
        if 'grooming' not in categories:
            missing_important.append('grooming products')
        if 'toys' not in categories:
            missing_important.append('toys/enrichment items')
        if 'accessories' not in categories:
            missing_important.append('accessories (collars, leashes)')
        
        if missing_important:
            recommendations.append(f"Consider purchases in: {', '.join(missing_important)}")
        
        return recommendations
    
    def _get_reliability_flags(self, factors: Dict, pet_data: Dict, 
                             purchase_history: List[Dict]) -> List[str]:
        """Generate reliability warning flags."""
        flags = []
        
        if len(purchase_history) < 8:
            flags.append("INSUFFICIENT_DATA")
        
        if factors.get('data_diversity', 0) < 8:
            flags.append("LIMITED_CATEGORIES")
        
        if factors.get('temporal_coverage', 0) < 6:
            flags.append("SHORT_TIME_SPAN")
        
        if factors.get('prediction_consistency', 0) < 5:
            flags.append("WEAK_PREDICTIONS")
        
        # Check for single-category dominance
        categories = {}
        for purchase in purchase_history:
            cat = purchase.get('category', 'other').lower()
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            max_cat_pct = max(categories.values()) / len(purchase_history)
            if max_cat_pct > 0.8:
                flags.append("SINGLE_CATEGORY_DOMINANT")
        
        return flags

def main():
    """Test the confidence scorer."""
    scorer = ConfidenceScorer()
    
    # Test case 1: Sparse data (like Buddy)
    sparse_pet = {'name': 'Buddy', 'size': 'SM', 'age': 10}
    sparse_purchases = [
        {'item_name': 'Dog Food', 'category': 'Food', 'order_date': '2020-01-01'},
        {'item_name': 'Dog Food', 'category': 'Food', 'order_date': '2020-02-01'},
        {'item_name': 'Dog Food', 'category': 'Food', 'order_date': '2020-03-01'},
    ]
    sparse_predictions = {'dachshund': 33.3, 'chihuahua': 25.3, 'yorkshireTerrier': 17.4}
    
    print("CONFIDENCE SCORER TEST")
    print("=" * 50)
    print("\nTest Case 1: Sparse Data (Buddy-like)")
    result = scorer.calculate_confidence(sparse_pet, sparse_purchases, sparse_predictions)
    
    print(f"Confidence Score: {result['confidence_score']}%")
    print(f"Confidence Level: {result['confidence_level']}")
    print(f"Reliability Flags: {result['reliability_flags']}")
    print(f"Recommendations: {result['recommendations'][:3]}")  # Show first 3
    
    # Test case 2: Rich data
    rich_pet = {'name': 'Parker', 'size': 'M', 'age': 5}
    rich_purchases = [
        {'item_name': 'Premium Dog Food', 'item_desc': 'High-quality protein-rich food for active dogs', 'category': 'Food', 'order_date': '2020-01-01'},
        {'item_name': 'Grooming Brush', 'item_desc': 'Professional slicker brush for long-haired breeds', 'category': 'Grooming', 'order_date': '2020-01-15'},
        {'item_name': 'Interactive Toy', 'item_desc': 'Puzzle toy for intelligent breeds', 'category': 'Toys', 'order_date': '2020-02-01'},
        {'item_name': 'Leather Collar', 'item_desc': 'Adjustable collar for medium dogs', 'category': 'Accessories', 'order_date': '2020-02-15'},
        {'item_name': 'Joint Supplement', 'item_desc': 'Glucosamine for active breeds', 'category': 'Health', 'order_date': '2020-03-01'},
    ] * 4  # Simulate 20 purchases
    rich_predictions = {'poodle': 45.2, 'goldenRetriever': 25.8, 'australianShepherd': 15.3}
    
    print(f"\nTest Case 2: Rich Data (Parker-like)")
    result2 = scorer.calculate_confidence(rich_pet, rich_purchases, rich_predictions)
    
    print(f"Confidence Score: {result2['confidence_score']}%")
    print(f"Confidence Level: {result2['confidence_level']}")
    print(f"Reliability Flags: {result2['reliability_flags']}")

if __name__ == "__main__":
    main() 