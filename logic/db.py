"""
Database module for USCIS QA app.
Handles SQLite database operations.
"""
import sqlite3
import os
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "qa.db"


def get_db_connection():
    """Get a database connection."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database():
    """Initialize the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            question_text TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            category TEXT,
            times_seen INTEGER DEFAULT 0,
            times_failed INTEGER DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()


def get_question_count():
    """Get the total number of questions in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def update_question_stats(question_id, passed):
    """Update statistics for a question after user answers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if passed:
        cursor.execute("""
            UPDATE questions 
            SET times_seen = times_seen + 1
            WHERE id = ?
        """, (question_id,))
    else:
        cursor.execute("""
            UPDATE questions 
            SET times_seen = times_seen + 1,
                times_failed = times_failed + 1
            WHERE id = ?
        """, (question_id,))
    
    conn.commit()
    conn.close()


def reset_all_statistics():
    """Reset all statistics (times_seen and times_failed) to 0."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE questions 
        SET times_seen = 0, times_failed = 0
    """)
    conn.commit()
    conn.close()


def get_question_by_id(question_id):
    """Get a question by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_all_questions():
    """Get all questions with computed fail_rate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        q = dict(row)
        # Compute fail_rate
        if q['times_seen'] > 0:
            q['fail_rate'] = q['times_failed'] / q['times_seen']
        else:
            q['fail_rate'] = 0.0
        questions.append(q)
    
    return questions


def get_most_missed_questions(limit=10):
    """Get questions sorted by fail_rate and times_failed."""
    questions = get_all_questions()
    
    # Sort by fail_rate desc, then times_failed desc
    questions.sort(key=lambda x: (x['fail_rate'], x['times_failed']), reverse=True)
    
    return questions[:limit]

