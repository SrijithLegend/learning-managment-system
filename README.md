# FastAPI LMS Question Bank AI System

## Overview

FastAPI LMS Question Bank AI System is a backend-focused Learning Management System (LMS) assessment module designed for question bank management, dataset analytics, machine learning-based question classification, and automated question paper generation.

The system is built using FastAPI, Pandas, Scikit-learn, and Jinja2 templates. It uses an Excel-based Question Bank dataset and exposes both template-rendered pages and Swagger-documented REST endpoints.

This project demonstrates the implementation of a lightweight educational assessment engine capable of:

- Managing LMS question bank operations
- Performing dataset analysis
- Predicting question topic and difficulty
- Comparing actual vs predicted labels
- Evaluating ML classification accuracy
- Automatically generating question papers using configurable constraints

---

# Core Functionalities

---

## 1. Question Bank Management System

The application supports complete CRUD operations for LMS question management.

### Supported Operations

- Add Questions
- Update Questions
- Delete Questions
- View Questions
- Duplicate Validation
- Question Filtering

### Question Data Schema

Each question contains:

| Field | Description |
|---|---|
| question_id | Unique identifier |
| question_text | Main question statement |
| subject | Domain/subject category |
| topic | Topic label |
| question_type | MCQ / True-False / Fill / Short Answer |
| difficulty | Easy / Medium / Hard |
| marks | Assigned marks |
| options | MCQ options |
| correct_answer | Correct answer |
| explanation | Solution explanation |

---

## 2. Dataset Analytics Engine

The analytics module performs dataset-level inspection and summarization using Pandas.

### Generated Analytics

- Total question count
- Subject-wise distribution
- Topic-wise distribution
- Difficulty-wise distribution
- Question-type distribution
- Total marks available
- Missing value analysis
- Duplicate question detection

### Sample Analytics Output

```json
{
  "total_questions": 522,
  "questions_by_subject": {
    "Python": 62,
    "MongoDB": 31
  },
  "questions_by_difficulty": {
    "Easy": 201,
    "Medium": 233,
    "Hard": 88
  },
  "duplicate_questions": 0
}
