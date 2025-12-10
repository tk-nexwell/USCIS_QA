"""
Question selector module for USCIS QA app.
Implements weighted random selection algorithm.
"""
import random
import sqlite3
from logic.db import get_db_connection, get_all_questions


def get_next_question(db_conn=None):
    """
    Get the next question using weighted random selection.
    
    Algorithm:
    - If questions have very few attempts (<3), prioritize them 1.5×
    - Weight = 1 + (fail_rate * 3)
    - Use weighted random selection
    
    Args:
        db_conn: Optional database connection (if None, creates new one)
    
    Returns:
        dict: Question data with computed fail_rate
    """
    questions = get_all_questions()
    
    if not questions:
        return None
    
    # Compute weights for each question
    weights = []
    for q in questions:
        weight = 1.0
        
        # Boost questions with few attempts (<3)
        if q['times_seen'] < 3:
            weight *= 1.5
        
        # Add weight based on fail_rate
        fail_rate = q['fail_rate'] if q['times_seen'] > 0 else 0.0
        weight += (fail_rate * 3)
        
        weights.append(weight)
    
    # Weighted random selection
    selected = random.choices(questions, weights=weights, k=1)[0]
    
    return selected

