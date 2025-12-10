"""
Excel loader module for USCIS QA app.
Handles importing questions from Excel files.
"""
import pandas as pd
import sqlite3
from pathlib import Path
from logic.db import get_db_connection, init_database


def normalize_excel_data(df_questions, df_answers=None):
    """
    Normalize Excel data into a standard format.
    
    Args:
        df_questions: DataFrame with questions
        df_answers: Optional DataFrame with answers (if separate)
    
    Returns:
        List of dicts with normalized question data
    """
    questions = []
    
    # If answers are in a separate sheet, handle them separately
    if df_answers is not None:
        # Get the first column from each sheet (handles cases where column name is a category)
        question_col = df_questions.columns[0] if len(df_questions.columns) > 0 else None
        answer_col = df_answers.columns[0] if len(df_answers.columns) > 0 else None
        
        # Extract category from column name if it looks like a category
        category = None
        if question_col:
            col_name = str(question_col).strip()
            # Check if column name looks like a category (e.g., "A. Principles of American Government")
            if '.' in col_name or len(col_name) > 15:
                category = col_name
        
        # Match rows by index (same row number = same question/answer pair)
        max_rows = min(len(df_questions), len(df_answers))
        for idx in range(max_rows):
            question_text = None
            answer_text = None
            
            if question_col is not None:
                q_val = df_questions.iloc[idx][question_col]
                if pd.notna(q_val):
                    q_str = str(q_val).strip()
                    # Skip if it's just a number (row number)
                    if q_str and not q_str.isdigit():
                        question_text = q_str
            
            if answer_col is not None:
                a_val = df_answers.iloc[idx][answer_col]
                if pd.notna(a_val):
                    a_str = str(a_val).strip()
                    # Skip if it's just a number or empty
                    if a_str and not a_str.isdigit():
                        answer_text = a_str
            
            # Only add if we have both question and answer
            if question_text and answer_text:
                questions.append({
                    'question_text': question_text,
                    'answer_text': answer_text,
                    'category': category
                })
        
        return questions
    
    # Single dataframe - use standard column detection
    merged = df_questions.copy()
    
    # Normalize column names (case-insensitive, handle common variations)
    merged.columns = merged.columns.str.strip().str.lower()
    
    # Map common column name variations
    column_mapping = {
        'question': 'question_text',
        'q': 'question_text',
        'question_text': 'question_text',
        'answer': 'answer_text',
        'a': 'answer_text',
        'answer_text': 'answer_text',
        'category': 'category',
        'cat': 'category',
        'type': 'category',
    }
    
    # Rename columns
    for old_name, new_name in column_mapping.items():
        if old_name in merged.columns:
            merged.rename(columns={old_name: new_name}, inplace=True)
    
    # Extract data from single dataframe
    for idx, row in merged.iterrows():
        question_text = None
        answer_text = None
        category = None
        
        # Find question text
        if 'question_text' in merged.columns:
            question_text = str(row['question_text']) if pd.notna(row['question_text']) else None
        else:
            # Try to find any column that might contain questions
            for col in merged.columns:
                if 'question' in col.lower() or 'q' == col.lower():
                    question_text = str(row[col]) if pd.notna(row[col]) else None
                    break
        
        # Find answer text
        if 'answer_text' in merged.columns:
            answer_text = str(row['answer_text']) if pd.notna(row['answer_text']) else None
        else:
            # Try to find any column that might contain answers
            for col in merged.columns:
                if 'answer' in col.lower() or 'a' == col.lower():
                    answer_text = str(row[col]) if pd.notna(row[col]) else None
                    break
        
        # Find category
        if 'category' in merged.columns:
            category = str(row['category']) if pd.notna(row['category']) else None
        
        # Only add if we have both question and answer
        if question_text and answer_text and question_text.strip() and answer_text.strip():
            questions.append({
                'question_text': question_text.strip(),
                'answer_text': answer_text.strip(),
                'category': category.strip() if category else None
            })
    
    return questions


def load_excel_to_db(questions_file, answers_file=None):
    """
    Load questions from Excel file(s) into the database.
    
    Args:
        questions_file: Path to Excel file with questions (or single file with multiple sheets)
        answers_file: Optional path to separate Excel file with answers
                      If None and questions_file has multiple sheets, uses first 2 sheets
    """
    init_database()
    
    # Check if questions_file has multiple sheets
    try:
        xls = pd.ExcelFile(questions_file)
        sheet_names = xls.sheet_names
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
    
    df_questions = None
    df_answers = None
    
    # If single file has multiple sheets and no separate answers_file provided
    if len(sheet_names) > 1 and answers_file is None:
        # Use first sheet for questions, second sheet for answers
        try:
            df_questions = pd.read_excel(questions_file, sheet_name=sheet_names[0])
            df_answers = pd.read_excel(questions_file, sheet_name=sheet_names[1])
        except Exception as e:
            raise ValueError(f"Error reading sheets from Excel file: {e}")
    elif answers_file:
        # Separate files provided
        try:
            df_questions = pd.read_excel(questions_file)
            df_answers = pd.read_excel(answers_file)
        except Exception as e:
            raise ValueError(f"Error reading Excel files: {e}")
    else:
        # Single file, single sheet (or use first sheet)
        try:
            df_questions = pd.read_excel(questions_file, sheet_name=sheet_names[0])
        except Exception as e:
            raise ValueError(f"Error reading questions file: {e}")
    
    # Normalize data
    questions = normalize_excel_data(df_questions, df_answers)
    
    if not questions:
        raise ValueError("No valid questions found in Excel file(s)")
    
    # Insert into database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if questions already exist
    existing_count = cursor.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    
    if existing_count == 0:
        # Insert all questions
        for q in questions:
            cursor.execute("""
                INSERT INTO questions (question_text, answer_text, category)
                VALUES (?, ?, ?)
            """, (q['question_text'], q['answer_text'], q['category']))
    else:
        # Update existing questions or insert new ones
        # This is a simple approach: we'll update by matching question_text
        for q in questions:
            cursor.execute("""
                SELECT id FROM questions WHERE question_text = ?
            """, (q['question_text'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing question
                cursor.execute("""
                    UPDATE questions 
                    SET answer_text = ?, category = ?
                    WHERE id = ?
                """, (q['answer_text'], q['category'], existing[0]))
            else:
                # Insert new question
                cursor.execute("""
                    INSERT INTO questions (question_text, answer_text, category)
                    VALUES (?, ?, ?)
                """, (q['question_text'], q['answer_text'], q['category']))
    
    conn.commit()
    conn.close()
    
    return len(questions)

