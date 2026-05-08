# FastAPI LMS Question Bank AI System

A FastAPI-based Learning Management System (LMS) Question Bank module that supports question management, dataset analytics, machine learning-based question classification, and automatic question paper generation.

This project uses an Excel-based Question Bank dataset and provides API endpoints through FastAPI Swagger UI. It is designed as a backend module for managing LMS assessments, classifying question difficulty/topic, comparing actual vs predicted labels, and generating question papers based on subject, total marks, and difficulty distribution.

---

## Project Overview

This system is built for an LMS assessment workflow where trainers/admins can:

- Manage question bank data
- Analyze question distribution
- Predict topic and difficulty of a question
- Classify all questions from the dataset
- Compare actual vs predicted labels
- Calculate basic model accuracy
- Generate automatic question papers from the dataset

The system currently uses `data.xlsx` as the primary data source.

---

## Core Features

### 1. Question Bank Management

- Add new questions
- Update existing questions
- Delete questions
- View all questions
- Avoid duplicate question entries
- Store question data in Excel format

---

### 2. Dataset Analytics

The system analyzes the question bank and returns:

- Total number of questions
- Questions by subject
- Questions by topic
- Questions by difficulty
- Questions by question type
- Total marks available
- Missing values check
- Duplicate question check

---

### 3. Machine Learning Classification

The system predicts:

- Question topic
- Question difficulty

using question text as input.

#### ML Flow

```text
Question Text
      ↓
TF-IDF Vectorization
      ↓
ML Model
      ↓
Predicted Topic / Predicted Difficulty
