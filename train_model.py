import os
from datetime import datetime
from dotenv import load_dotenv
import joblib
import pandas as pd
from fastapi import Form
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sqlalchemy import Integer, create_engine, select, text

from generator import question_generator
from prediction import calculate_difficulty, calculate_topic
from similarity import similarity_checker, sync_database_to_vector_db

# Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

with engine.begin() as connection:

    query = text("""
        SELECT question_bank_question_text, question_bank_question_difficulty, question_bank_question_topic 
        FROM lms_demo_db.question_bank_questions
        WHERE question_bank_question_text IS NOT NULL 
          AND question_bank_question_difficulty IS NOT NULL 
          AND question_bank_question_topic IS NOT NULL
    """)
    
    results = connection.execute(query).fetchall()
    
    # Unpack the aligned data
    X = [row[0] for row in results]
    y_diff = [row[1] for row in results]
    y_top = [row[2] for row in results]


    (
        X_train,
        X_test,
        y_diff_train,
        y_diff_test,
        y_top_train,
        y_top_test,
    ) = train_test_split(X, y_diff, y_top, test_size=0.2, random_state=42)

    vectorizer = TfidfVectorizer()
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model_diff = LogisticRegression(max_iter=1000)
    model_diff.fit(X_train_vec, y_diff_train)
    diff_preds = model_diff.predict(X_test_vec)
    diff_accuracy = accuracy_score(y_diff_test, diff_preds)
    print(f"Difficulty Accuracy: {diff_accuracy * 100:.2f}%")

    model_top = LinearSVC(C=1.0, max_iter=1000)
    model_top.fit(X_train_vec, y_top_train)
    top_preds = model_top.predict(X_test_vec)
    top_accuracy = accuracy_score(y_top_test, top_preds)
    print(f"Topic Accuracy: {top_accuracy * 100:.2f}%")

    joblib.dump(vectorizer, "vectorizer.pkl")
    joblib.dump(model_diff, "model_diff.pkl")
    joblib.dump(model_top, "model_top.pkl")

    print("\nModels and vectorizer saved successfully.")