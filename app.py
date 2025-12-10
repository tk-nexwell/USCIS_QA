"""
USCIS Questions Practice App
Main Streamlit application
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from logic.db import (
    init_database, 
    get_question_count, 
    update_question_stats,
    reset_all_statistics,
    get_question_by_id,
    get_all_questions,
    get_most_missed_questions
)
from logic.question_selector import get_next_question
from data.qa_loader import load_excel_to_db


# Page configuration
st.set_page_config(
    page_title="USCIS Practice Questions",
    page_icon="🇺🇸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.2rem;
        border-radius: 0.5rem;
    }
    .answer-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .question-text {
        font-size: 1.3rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
if 'current_question_id' not in st.session_state:
    st.session_state.current_question_id = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'practice'  # 'practice' or 'stats'
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False


def auto_load_excel_file():
    """Automatically load Excel file from project folder if database is empty."""
    init_database()
    
    # Check if database already has questions
    if get_question_count() > 0:
        return True
    
    # Don't try to load again if we already tried
    if st.session_state.data_loaded:
        return False
    
    # Look for Excel file in project folder
    excel_files = [
        "QAs 128 USCIS.xlsx",
        "questions.xlsx",
        "qa.xlsx",
        "uscis.xlsx"
    ]
    
    excel_file = None
    for filename in excel_files:
        file_path = Path(filename)
        if file_path.exists():
            excel_file = file_path
            break
    
    if excel_file:
        try:
            count = load_excel_to_db(excel_file)
            st.session_state.data_loaded = True
            return True
        except Exception as e:
            st.error(f"Error loading {excel_file}: {e}")
            st.session_state.data_loaded = True  # Mark as attempted to avoid repeated errors
            return False
    
    st.session_state.data_loaded = True  # Mark as attempted
    return False


def load_initial_question():
    """Load the initial or next question."""
    init_database()
    
    # Auto-load Excel file if database is empty
    if get_question_count() == 0:
        if not auto_load_excel_file():
            return None
    
    question = get_next_question()
    if question:
        st.session_state.current_question_id = question['id']
        st.session_state.show_answer = False
        st.session_state.answered = False
    return question


def handle_pass_fail(passed):
    """Handle Pass/Fail button click."""
    if st.session_state.current_question_id:
        update_question_stats(st.session_state.current_question_id, passed)
        # Automatically load next question
        load_initial_question()
        st.rerun()


# Sidebar for navigation and file upload
with st.sidebar:
    st.title("🇺🇸 USCIS Practice")
    
    # Navigation
    if st.button("📚 Practice Questions", use_container_width=True):
        st.session_state.view_mode = 'practice'
        st.rerun()
    
    if st.button("📊 Most Missed Questions", use_container_width=True):
        st.session_state.view_mode = 'stats'
        st.rerun()
    
    st.divider()
    
    # Reload data button (for when Excel file is updated)
    st.subheader("Data Management")
    if st.button("🔄 Reload from Excel File", use_container_width=True):
        # Look for Excel file in project folder
        excel_files = [
            "QAs 128 USCIS.xlsx",
            "questions.xlsx",
            "qa.xlsx",
            "uscis.xlsx"
        ]
        
        excel_file = None
        for filename in excel_files:
            file_path = Path(filename)
            if file_path.exists():
                excel_file = file_path
                break
        
        if excel_file:
            try:
                with st.spinner("Reloading questions..."):
                    count = load_excel_to_db(excel_file)
                    st.success(f"✅ Reloaded {count} questions!")
                    load_initial_question()
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading {excel_file}: {e}")
        else:
            st.error("Excel file not found in project folder.")
    
    st.caption("Questions are automatically loaded from 'QAs 128 USCIS.xlsx' in the project folder.")
    
    st.divider()
    
    # Reset statistics button
    if st.button("🔄 Reset Statistics", use_container_width=True):
        reset_all_statistics()
        st.success("Statistics reset!")
        if st.session_state.view_mode == 'practice':
            load_initial_question()
        st.rerun()


# Main content area
if st.session_state.view_mode == 'stats':
    # Statistics view
    st.title("📊 Most Missed Questions")
    
    questions = get_all_questions()
    total_questions = len(questions)
    
    if total_questions == 0:
        st.warning("No questions in database. Please upload Excel files first.")
    else:
        # Overall statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_seen = sum(q['times_seen'] for q in questions)
        total_failed = sum(q['times_failed'] for q in questions)
        overall_pass_rate = ((total_seen - total_failed) / total_seen * 100) if total_seen > 0 else 0
        
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Total Attempts", total_seen)
        with col3:
            st.metric("Total Failed", total_failed)
        with col4:
            st.metric("Overall Pass Rate", f"{overall_pass_rate:.1f}%")
        
        st.divider()
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Top 10 Most Failed Questions")
            most_missed = get_most_missed_questions(10)
            
            if most_missed:
                df_chart = pd.DataFrame([
                    {
                        'Question': f"Q{q['id']}",
                        'Times Failed': q['times_failed'],
                        'Fail Rate': f"{q['fail_rate']*100:.1f}%"
                    }
                    for q in most_missed if q['times_failed'] > 0
                ])
                
                if not df_chart.empty:
                    fig = px.bar(
                        df_chart,
                        x='Question',
                        y='Times Failed',
                        title="Times Failed (Top 10)",
                        color='Times Failed',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No failed questions yet.")
        
        with col_chart2:
            st.subheader("Overall Pass Rate")
            if total_seen > 0:
                passed_count = total_seen - total_failed
                fig = go.Figure(data=[go.Pie(
                    labels=['Passed', 'Failed'],
                    values=[passed_count, total_failed],
                    hole=0.4,
                    marker_colors=['#2ecc71', '#e74c3c']
                )])
                fig.update_layout(height=400, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No attempts yet.")
        
        st.divider()
        
        # Most missed questions table
        st.subheader("Most Missed Questions (Detailed)")
        most_missed_all = get_most_missed_questions(50)
        
        if most_missed_all:
            df_table = pd.DataFrame([
                {
                    'ID': q['id'],
                    'Question': q['question_text'][:100] + "..." if len(q['question_text']) > 100 else q['question_text'],
                    'Times Seen': q['times_seen'],
                    'Times Failed': q['times_failed'],
                    'Fail Rate': f"{q['fail_rate']*100:.1f}%",
                    'Category': q['category'] or 'N/A'
                }
                for q in most_missed_all
            ])
            st.dataframe(df_table, use_container_width=True, hide_index=True)
        else:
            st.info("No questions with statistics yet.")

else:
    # Practice mode
    st.title("🇺🇸 USCIS Practice Questions")
    
    # Initialize database
    init_database()
    
    # Load question if needed
    if st.session_state.current_question_id is None:
        question = load_initial_question()
    else:
        question = get_question_by_id(st.session_state.current_question_id)
        if not question:
            question = load_initial_question()
    
    if question:
        # Compute fail_rate for display
        if question['times_seen'] > 0:
            question['fail_rate'] = question['times_failed'] / question['times_seen']
        else:
            question['fail_rate'] = 0.0
        
        # Display question number and stats
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Question #", question['id'])
        with col_info2:
            st.metric("Times Seen", question['times_seen'])
        with col_info3:
            st.metric("Fail Rate", f"{question['fail_rate']*100:.1f}%")
        
        st.divider()
        
        # Display question text
        st.markdown(f'<div class="question-text">{question["question_text"]}</div>', unsafe_allow_html=True)
        
        # Show Answer button
        if not st.session_state.show_answer:
            col_btn = st.columns([1, 2, 1])[1]  # Center the button
            with col_btn:
                if st.button("🔍 Show Answer", use_container_width=True, type="primary"):
                    st.session_state.show_answer = True
                    st.rerun()
        
        # Display answer if shown
        if st.session_state.show_answer:
            st.markdown('<div class="answer-box">', unsafe_allow_html=True)
            st.markdown("### Answer:")
            st.markdown(question['answer_text'])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Pass/Fail buttons
            col_pass, col_fail = st.columns(2)
            
            with col_pass:
                if st.button("✅ Pass", use_container_width=True, type="primary"):
                    handle_pass_fail(True)
            
            with col_fail:
                if st.button("❌ Fail", use_container_width=True, type="secondary"):
                    handle_pass_fail(False)
    else:
        st.info("No questions available. The app will automatically load from 'QAs 128 USCIS.xlsx' in the project folder.")
        
        # Show instructions
        with st.expander("📖 How to use this app"):
            st.markdown("""
            ### Getting Started
            
            1. **Excel File**: Place your Excel file named 'QAs 128 USCIS.xlsx' in the project folder.
               - The app automatically loads questions from this file on startup.
               - If questions and answers are in **2 separate sheets**, the app will use the first 2 sheets.
               - Use "Reload from Excel File" in the sidebar if you update the file.
            
            2. **Practice Questions**: 
               - Click "Show Answer" to reveal the answer
               - Click "Pass" if you got it right, or "Fail" if you got it wrong
               - The app will automatically load the next question
            
            3. **View Statistics**: 
               - Click "Most Missed Questions" to see your performance
               - View charts and detailed statistics
            
            4. **Reset**: 
               - Use "Reset Statistics" to clear all your progress
            """)

