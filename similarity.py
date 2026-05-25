import chromadb
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine , text
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
chroma_client = chromadb.PersistentClient(path="./my_vector_db")
collection = chroma_client.get_or_create_collection(name="my_faq_collection")

def sync_database_to_vector_db():
    
    query = text("""
        SELECT question_bank_question_id, question_bank_question_text
        FROM lms_demo_db.question_bank_questions
        WHERE question_bank_question_is_deleted = 0
    """)
    
    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()
        
    if not rows:
        print("No questions found in database.")
        return
    
    ids = [str(row["question_bank_question_id"]) for row in rows]
    documents = [str(row["question_bank_question_text"]) for row in rows]

    collection.upsert(
        ids=ids,
        documents=documents
    )
    print(f"Sync complete. {len(documents)} questions are now indexed.")


def similarity_checker(user_search_query, n_results=1):
    
    results = collection.query(
        query_texts=[user_search_query],
        n_results=n_results
    )
    
    if not results or not results['documents'][0]:
        print("No matches found.")
        return {
            "closest_match": None,
            "distance_score": None,
            "similarity": None,
            "result": "No matches found."
        }

    closest_match = results['documents'][0][0] 
    distance_score = results['distances'][0][0]

    similarity = round((1 - distance_score) * 100, 2)  

    if similarity < 60.0:
        result = 'Unique question.'
    elif 60.0 <= similarity <= 85.0:
        result = 'Similar question.'
    else:
        result = "Duplicate Question."

    return {
        "closest_match": closest_match,   
        "distance_score": distance_score,
        "similarity": similarity,
        "result": result
    }