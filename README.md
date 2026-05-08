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

Machine Learning Classification System

The application contains a lightweight NLP classification pipeline for predicting:

Question Topic
Question Difficulty

using only question text as input.

NLP Pipeline Architecture
Question Text
      ↓
TF-IDF Vectorization
      ↓
Feature Matrix
      ↓
ML Classification Model
      ↓
Predicted Label
1. Topic Classification
Model Used
TF-IDF Vectorizer + LinearSVC
Reason for Selection

LinearSVC performs effectively for sparse text classification problems and small-to-medium datasets.

Advantages:

Fast inference
Low memory usage
High performance on sparse TF-IDF features
Suitable for educational text classification
Prediction Flow
Question Text
      ↓
TF-IDF
      ↓
LinearSVC
      ↓
Predicted Topic
2. Difficulty Classification
Model Used
TF-IDF Vectorizer + Logistic Regression
Reason for Selection

Logistic Regression provides stable performance for multi-class educational classification tasks and works efficiently on small datasets.

Prediction Flow
Question Text
      ↓
TF-IDF
      ↓
Logistic Regression
      ↓
Predicted Difficulty
Classification Features
Single Question Prediction

The system can classify an individual question.

Input
{
  "question_text": "Which AWS service is used for serverless execution?"
}
Output
{
  "predicted_topic": "Cloud Services",
  "predicted_difficulty": "Medium"
}
Full Dataset Classification

The system can classify all questions from the dataset.

Generated Output

For every question:

Actual Topic
Predicted Topic
Actual Difficulty
Predicted Difficulty
Topic Match Status
Difficulty Match Status
Accuracy Evaluation

The application calculates basic classification accuracy.

Formula
Accuracy = Correct Predictions / Total Predictions × 100
Metrics
Topic Prediction Accuracy
Difficulty Prediction Accuracy
Sample Output
{
  "topic_accuracy": 82.44,
  "difficulty_accuracy": 76.13
}
Auto Question Paper Generator

The project includes an automated question paper generation engine.

Objective

Generate assessment papers dynamically using:

Subject
Total marks
Difficulty distribution

while:

Avoiding duplicate questions
Attempting to match requested marks
Maintaining difficulty-wise balance
Input Parameters
{
  "subject": "Python",
  "total_marks": 20,
  "easy_percent": 30,
  "medium_percent": 50,
  "hard_percent": 20
}
Internal Workflow
Receive Input
      ↓
Load Dataset
      ↓
Filter Subject Questions
      ↓
Remove Duplicates
      ↓
Calculate Difficulty-wise Marks
      ↓
Select Questions
      ↓
Validate Total Marks
      ↓
Generate Final Paper
Final Generated Output

The generated paper includes:

Selected Questions
Generated Total Marks
Question Count
Difficulty-wise Distribution
Topic-wise Distribution
Status Message
Example Response
{
  "subject": "Python",
  "requested_total_marks": 20,
  "generated_total_marks": 18,
  "question_count": 6,
  "difficulty_distribution": {
    "Easy": 2,
    "Medium": 3,
    "Hard": 1
  },
  "topic_distribution": {
    "Functions": 2,
    "OOP": 3,
    "Basics": 1
  },
  "message": "Question paper generated successfully"
}
Tech Stack
Backend Framework
FastAPI

Used for:

REST API development
Swagger/OpenAPI documentation
Request handling
Endpoint management

Advantages:

High performance
Automatic API docs
Type validation
Async support
Data Processing
Pandas

Used for:

Excel dataset manipulation
Filtering
Duplicate removal
Analytics
Question selection
Machine Learning
Scikit-learn

Used for:

TF-IDF feature extraction
Topic classification
Difficulty classification
Accuracy evaluation
Frontend Templates
Jinja2 + HTML + CSS

Used for:

Dynamic template rendering
CRUD forms
Prediction pages
Classification result pages
Dataset Storage
Excel (data.xlsx)

The project currently uses Excel as a lightweight persistence layer.

Advantages:

Simple setup
Easy dataset editing
Suitable for internship/demo projects

Limitations:

Not scalable
Unsafe for concurrent writes
No transactional guarantees
Project Structure
fastapi-lms-question-bank-ai/
│
├── script.py
├── prediction.py
├── data.xlsx
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── layout.html
│   ├── summary.html
│   ├── questions.html
│   ├── add_question.html
│   ├── update_question.html
│   ├── delete_question.html
│   ├── prediction.html
│   └── classification.html
│
└── __pycache__/
Installation
1. Clone Repository
git clone https://github.com/your-username/fastapi-lms-question-bank-ai.git
cd fastapi-lms-question-bank-ai
2. Create Virtual Environment
python -m venv .venv
3. Activate Environment
Windows
.venv\Scripts\activate
Linux/macOS
source .venv/bin/activate
4. Install Dependencies
pip install -r requirements.txt
5. Run Application
uvicorn script:app --reload
Swagger Documentation

FastAPI automatically generates Swagger UI.

Access:

http://127.0.0.1:8000/docs
API Endpoints
Dataset Analytics
GET /

Returns dataset analytics dashboard.

Question Management
View Questions
GET /questions
Add Question
GET /add_question
POST /add_question
Update Question
GET /update_question
POST /update_question
Delete Question
GET /delete_question
POST /delete_question
Machine Learning
Single Prediction
GET /prediction
POST /prediction
Full Classification
GET /classification
Accuracy Summary
GET /accuracy_summary
Question Paper Generation
Generate Question Paper
POST /generate_question_paper
Supported Subjects

The dataset currently contains questions from:

MongoDB
MySQL
BFSI
DevOps
.NET
Cybersecurity
Blockchain
Data Engineering with Python
Flutter
Machine Learning
AWS Cloud
Docker
Spring Boot
Angular
Node.js
React
Java
Python
Current Limitations
Uses Excel instead of a database
Models retrain during runtime
No persistent trained model storage
No authentication system
No asynchronous ML inference
No PDF export for generated papers
Evaluation uses training data itself
Future Improvements
MongoDB/MySQL integration
Joblib model persistence
JWT authentication
Role-based access control
Transformer-based NLP models
Real train-test evaluation
PDF question paper export
Docker containerization
Cloud deployment
Advanced marks optimization algorithm
Engineering Objectives

This project demonstrates:

Backend API engineering
FastAPI application architecture
Educational assessment workflows
Machine learning integration
NLP text classification
Dataset analytics
Auto paper generation systems
Template-based web rendering
Intended Use

This system is intended as:

LMS backend prototype
Internship-level assessment engine
Educational AI demonstration project
ML-integrated CRUD application
FastAPI learning project

It can be extended into a production-grade LMS assessment platform with database integration, authentication, scalable model serving, and advanced paper generation algorithms.
