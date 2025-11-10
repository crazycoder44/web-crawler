# scheduler/fingerprinting.py

"""
Fingerprinting module for detecting changes in book content.
Integrates with crawler's existing hash and comparison functionality.
"""

import hashlib
import json
from typing import Dict, Any, Tuple, Set
from datetime import datetime


def detect_changes(old_content: Dict[str, Any], new_content: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Compare two versions of book content and generate change records in crawler format.
    
    Args:
        old_content: Previous version of the book data
        new_content: Current version of the book data
        
    Returns:
        Dict[str, Dict[str, Any]]: Changes in format {field: {'old': old_value, 'new': new_value}}
    """
    changes = {}
    tracked_fields = {
        'title', 'description', 'category', 'price_incl_tax', 'price_excl_tax',
        'availability', 'num_reviews', 'rating'
    }
    
    for field in tracked_fields:
        old_value = old_content.get(field)
        new_value = new_content.get(field)
        
        if old_value != new_value:
            changes[field] = {
                'old': old_value,
                'new': new_value
            }
    
    return changes


def is_significant_change(changes: Dict[str, Dict[str, Any]]) -> bool:
    """
    Determine if changes are significant enough to trigger alerts.
    
    Args:
        changes: Dictionary of changes in crawler format
        
    Returns:
        bool: True if changes are significant
    """
    significant_fields = {'title', 'description', 'category'}
    price_fields = {'price_incl_tax', 'price_excl_tax'}
    
    # Any change to significant fields is considered significant
    if any(field in changes for field in significant_fields):
        return True
        
    # Check for significant price changes
    for field in price_fields:
        if field in changes:
            old_price = float(changes[field]['old'] or 0)
            new_price = float(changes[field]['new'] or 0)
            if is_significant_price_change(old_price, new_price):
                return True
                
    return False


def is_significant_price_change(old_price: float, new_price: float, threshold: float = 0.05) -> bool:
    """
    Determine if a price change is significant based on a threshold.
    
    Args:
        old_price: Previous price
        new_price: New price
        threshold: Minimum percentage change to consider significant (default 5%)
        
    Returns:
        bool: True if the change is significant
    """
    if old_price == 0:
        return new_price > 0
        
    price_change = abs(new_price - old_price) / old_price
    return price_change > threshold


def summarize_changes(changes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a summary of changes for reporting.
    
    Args:
        changes: Dictionary of changes in crawler format
        
    Returns:
        Dict[str, Any]: Summary of changes with counts by type
    """
    summary = {
        'total_changes': len(changes),
        'fields_changed': list(changes.keys()),
        'has_significant_changes': is_significant_change(changes),
        'timestamp': datetime.utcnow()
    }
    
    # Count changes by type
    change_types = {
        'price': len([f for f in changes if f.startswith('price_')]),
        'availability': 1 if 'availability' in changes else 0,
        'metadata': len([f for f in changes if f in {'title', 'description', 'category'}]),
        'ratings': len([f for f in changes if f in {'rating', 'num_reviews'}])
    }
    summary['change_types'] = change_types
    
    return summary