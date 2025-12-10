# USCIS Questions Practice App

A Streamlit-based practice application for USCIS citizenship questions with intelligent question selection and performance tracking.

## Features

- 📚 **Practice Mode**: Answer questions with Pass/Fail tracking
- 📊 **Statistics Dashboard**: View most missed questions with charts
- 🎯 **Smart Selection**: Weighted algorithm prioritizes questions you struggle with
- 📱 **Mobile-Friendly**: Optimized for both phone and desktop
- 💾 **Persistent Storage**: SQLite database tracks your progress

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the app:
```bash
streamlit run app.py
```

2. Upload your Excel files:
   - Use the sidebar to upload your questions Excel file
   - If questions and answers are in separate files, upload both
   - The app will automatically detect and load the data

3. Practice:
   - Click "Show Answer" to reveal the answer
   - Click "Pass" or "Fail" to record your response
   - The app automatically loads the next question

4. View Statistics:
   - Click "Most Missed Questions" to see performance charts
   - View detailed statistics and fail rates

## Excel File Format

The app supports flexible Excel formats. It will automatically detect columns with:
- **Questions**: Column names like "Question", "Q", "question_text"
- **Answers**: Column names like "Answer", "A", "answer_text"
- **Categories**: Optional column names like "Category", "Cat", "Type"

You can have:
- Single file with both questions and answers
- Separate files for questions and answers
- Questions and answers merged by ID or by row index

## Project Structure

```
USCIS_QA/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── data/
│   ├── qa_loader.py      # Excel import functionality
│   └── qa.db            # SQLite database (auto-created)
└── logic/
    ├── db.py            # Database operations
    └── question_selector.py  # Weighted question selection
```

## Question Selection Algorithm

The app uses a weighted random selection:
- Questions with <3 attempts get 1.5× priority
- Weight = 1 + (fail_rate × 3)
- Higher fail rates = more frequent appearance
- Ensures all questions are eventually seen

## Reset Statistics

Use the "Reset Statistics" button in the sidebar to clear all progress and start fresh.

