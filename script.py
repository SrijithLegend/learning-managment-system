import pandas as pd
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Form
from prediction import calculate_difficulty, calculate_topic
from generator import question_generator
from datetime import datetime
from sqlalchemy import create_engine, text, select, Integer
from dotenv import load_dotenv
import os
from similarity import similarity_checker , sync_database_to_vector_db

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

engine = create_engine(DATABASE_URL)

def analyze_questions():
    with engine.connect() as connection:
        duplicate_count = connection.execute(text("SELECT COUNT(*) FROM (SELECT question_bank_question_text FROM question_bank_questions GROUP BY question_bank_question_text HAVING COUNT(*) > 1) AS t")).scalar() or 0

        if duplicate_count > 0:
            delete_query = text("""
                SET SQL_SAFE_UPDATES = 0;
                UPDATE lms_demo_db.exam_submission_questions esq
                JOIN lms_demo_db.question_bank_questions q 
                    ON esq.question_id = q.question_bank_question_id
                JOIN (
                    SELECT MIN(question_bank_question_id) AS keep_id, question_bank_question_text
                    FROM lms_demo_db.question_bank_questions
                    GROUP BY question_bank_question_text
                ) AS keeper 
                    ON q.question_bank_question_text = keeper.question_bank_question_text
                SET esq.question_id = keeper.keep_id
                WHERE esq.question_id != keeper.keep_id;
                
                DELETE FROM lms_demo_db.question_bank_questions
                WHERE question_bank_question_id NOT IN (
                    SELECT id FROM (
                        SELECT MIN(question_bank_question_id) AS id
                        FROM lms_demo_db.question_bank_questions
                        GROUP BY question_bank_question_text
                    ) AS temp
                );
                SET SQL_SAFE_UPDATES = 1;
            """)
            connection.execute(delete_query)
            connection.commit()

        total_questions = connection.execute(text("SELECT COUNT(*) FROM question_bank_questions")).scalar() or 0
        topic_res = connection.execute(text("SELECT question_bank_question_topic, COUNT(*) AS question_count FROM question_bank_questions GROUP BY question_bank_question_topic")).mappings().all()
        difficulty_res = connection.execute(text("SELECT question_bank_question_difficulty, COUNT(*) AS question_count FROM question_bank_questions GROUP BY question_bank_question_difficulty")).mappings().all()
        type_res = connection.execute(text("SELECT question_bank_question_type, COUNT(*) AS question_count FROM question_bank_questions GROUP BY question_bank_question_type")).mappings().all()
        total_marks = connection.execute(text("SELECT SUM(question_bank_question_marks) FROM question_bank_questions")).scalar() or 0
        missing_values = connection.execute(text("SELECT COUNT(*) FROM question_bank_questions WHERE question_bank_question_text IS NULL")).scalar() or 0
        
        return {
            "total_questions": total_questions,
            "questions_by_topic": [dict(row) for row in topic_res],
            "questions_by_difficulty": [dict(row) for row in difficulty_res],
            "questions_by_type": [dict(row) for row in type_res],
            "total_marks": total_marks,
            "missing_values": missing_values,
            "duplicate_questions": duplicate_count,
        }
    
@app.get("/", include_in_schema=True)
async def get_summary(request: Request):
    summary = analyze_questions()
    return templates.TemplateResponse(request, 'summary.html', {"data": summary})

@app.get("/questions", include_in_schema=True)
async def get_questions(request: Request):
    with engine.connect() as connection:
        questions = connection.execute(text("SELECT question_bank_question_id, question_bank_question_text FROM lms_demo_db.question_bank_questions")).mappings().all()
    return templates.TemplateResponse(request, 'questions.html', {"data": questions})

@app.get("/add_question")
async def show_add_question_form(request: Request):
    return templates.TemplateResponse(request, "add_question.html")

@app.post("/add_question")
async def add_question(
    request: Request,
    question_bank_id: int = Form(...),
    question_bank_question_id: int = Form(...),
    tenant_id: int = Form(...), 
    question_bank_question_topic: str = Form(...), 
    question_bank_question_type: str = Form(...),
    question_bank_question_text: str = Form(...), 
    question_bank_question_paragraph_text: str | None = Form(None), 
    question_bank_question_difficulty: str = Form(...),
    question_bank_question_marks: float = Form(...), 
    question_bank_question_negative_marks: float = Form(...), 
    question_bank_question_hint_text: str | None = Form(None), 
    question_bank_question_explanation_text: str | None = Form(None), 
    question_bank_question_order: str | None = Form(None), 
    question_bank_question_parent_id: str | None = Form(None), 
    question_bank_question_is_active: int = Form(...), 
    question_bank_question_is_deleted: int = Form(...), 
    question_bank_question_created_at: datetime = Form(...), 
    question_bank_question_created_by: int = Form(...),
    question_bank_question_updated_at: datetime = Form(...),
    question_bank_question_updated_by: int = Form(...),
    question_bank_question_audio_url: str | None = Form(None),
    audio_file_url: str | None = Form(None)
):
    similarity_result = similarity_checker(question_bank_question_text)
    
    with engine.begin() as connection:
        question_text_validity = connection.execute(
            text("""
                SELECT question_bank_question_text
                FROM lms_demo_db.question_bank_questions
                WHERE question_bank_question_text = :question_text
                AND question_bank_question_is_deleted = 0;
            """),
            {"question_text": question_bank_question_text}
        ).fetchone()

        if question_text_validity:
            return {"error": "Question text already exists."}
        

        try:
            order_val = int(question_bank_question_order) if question_bank_question_order and question_bank_question_order != "null" else None
        except ValueError:
            order_val = None

        try:
            parent_val = int(question_bank_question_parent_id) if question_bank_question_parent_id and question_bank_question_parent_id != "null" else None
        except ValueError:
            parent_val = None

        new_question = {
            'question_bank_id': question_bank_id,
            'question_bank_question_id': question_bank_question_id,
            'tenant_id': tenant_id,
            'question_bank_question_topic': question_bank_question_topic,
            'question_bank_question_type': question_bank_question_type,
            'question_bank_question_text': question_bank_question_text,
            'question_bank_question_paragraph_text': question_bank_question_paragraph_text if question_bank_question_paragraph_text and question_bank_question_paragraph_text != "null" else None,
            'question_bank_question_difficulty': question_bank_question_difficulty,
            'question_bank_question_marks': question_bank_question_marks,
            'question_bank_question_negative_marks': question_bank_question_negative_marks,
            'question_bank_question_hint_text': question_bank_question_hint_text if question_bank_question_hint_text and question_bank_question_hint_text != "null" else None,
            'question_bank_question_explanation_text': question_bank_question_explanation_text if question_bank_question_explanation_text and question_bank_question_explanation_text != "null" else None,
            'question_bank_question_order': order_val,
            'question_bank_question_parent_id': parent_val,
            'question_bank_question_is_active': question_bank_question_is_active,
            'question_bank_question_is_deleted': question_bank_question_is_deleted,
            'question_bank_question_created_at': question_bank_question_created_at,
            'question_bank_question_created_by': question_bank_question_created_by,
            'question_bank_question_updated_at': question_bank_question_updated_at,
            'question_bank_question_updated_by': question_bank_question_updated_by,
            'question_bank_question_audio_url': question_bank_question_audio_url if question_bank_question_audio_url and question_bank_question_audio_url != "null" else None,
            'audio_file_url': audio_file_url if audio_file_url and audio_file_url != "null" else None
        }
        
        connection.execute(
            text("""
                INSERT INTO lms_demo_db.question_bank_questions (
                    question_bank_id,
                    tenant_id,
                    question_bank_question_id,
                    question_bank_question_topic,
                    question_bank_question_type,
                    question_bank_question_text,
                    question_bank_question_paragraph_text,
                    question_bank_question_difficulty,
                    question_bank_question_marks,
                    question_bank_question_negative_marks,
                    question_bank_question_hint_text,
                    question_bank_question_explanation_text,
                    question_bank_question_order,
                    question_bank_question_parent_id,
                    question_bank_question_is_active,
                    question_bank_question_is_deleted,
                    question_bank_question_created_at,
                    question_bank_question_created_by,
                    question_bank_question_updated_at,
                    question_bank_question_updated_by,
                    question_bank_question_audio_url,
                    audio_file_url
                )
                VALUES (
                    :question_bank_id,
                    :tenant_id,
                    :question_bank_question_id,
                    :question_bank_question_topic,
                    :question_bank_question_type,
                    :question_bank_question_text,
                    :question_bank_question_paragraph_text,
                    :question_bank_question_difficulty,
                    :question_bank_question_marks,
                    :question_bank_question_negative_marks,
                    :question_bank_question_hint_text,
                    :question_bank_question_explanation_text,
                    :question_bank_question_order,
                    :question_bank_question_parent_id,
                    :question_bank_question_is_active,
                    :question_bank_question_is_deleted,
                    :question_bank_question_created_at,
                    :question_bank_question_created_by,
                    :question_bank_question_updated_at,
                    :question_bank_question_updated_by,
                    :question_bank_question_audio_url,
                    :audio_file_url
                )
            """),
            new_question
        )

        message = f"Question with ID {question_bank_question_id} added successfully"

    sync_database_to_vector_db()

    return templates.TemplateResponse(request, "add_question.html", {
        "message": message,
        "closest_match": 'No Questions Matched' if similarity_result["similarity"] <= 0 else similarity_result["closest_match"],
        "distance_score": '0' if similarity_result["similarity"] <= 0 else similarity_result["similarity"],
        "result": similarity_result["result"]
    })

@app.get("/update_question")
async def show_update_question_form(request: Request):
    return templates.TemplateResponse(request,
        "update_question.html"
    )


@app.post("/update_question")
async def update_question(
    request: Request,
    question_bank_id: int = Form(...),
    question_bank_question_id: int = Form(...),
    tenant_id: int = Form(...), 
    question_bank_question_topic: str = Form(...), 
    question_bank_question_type: str = Form(...),
    question_bank_question_text: str = Form(...), 
    question_bank_question_paragraph_text: str | None = Form(None), 
    question_bank_question_difficulty: str = Form(...),
    question_bank_question_marks: float = Form(...), 
    question_bank_question_negative_marks: float = Form(...), 
    question_bank_question_hint_text: str | None = Form(None), 
    question_bank_question_explanation_text: str | None = Form(None), 
    question_bank_question_order: str | None = Form(None), 
    question_bank_question_parent_id: str | None = Form(None), 
    question_bank_question_is_active: int = Form(...), 
    question_bank_question_is_deleted: int = Form(...), 
    question_bank_question_created_at: datetime = Form(...), 
    question_bank_question_created_by: int = Form(...),
    question_bank_question_updated_at: datetime = Form(...),
    question_bank_question_updated_by: int = Form(...),
    question_bank_question_audio_url: str | None = Form(None),
    audio_file_url: str | None = Form(None)
):
    similarity_result = similarity_checker(question_bank_question_text)
    
    with engine.begin() as connection:
        question_id_validity = connection.execute(
            text("""
                SELECT question_bank_question_id
                FROM lms_demo_db.question_bank_questions
                WHERE question_bank_question_id = :question_id
                AND question_bank_question_is_deleted = 0
            """),
            {"question_id": question_bank_question_id}
        ).fetchone()

        if not question_id_validity:
            return {"error": "Question id doesn't exist."}

        try:
            order_val = int(question_bank_question_order) if question_bank_question_order and question_bank_question_order != "null" else None
        except ValueError:
            order_val = None

        try:
            parent_val = int(question_bank_question_parent_id) if question_bank_question_parent_id and question_bank_question_parent_id != "null" else None
        except ValueError:
            parent_val = None

        update_question = {
            'question_bank_id': question_bank_id,
            'question_bank_question_id': question_bank_question_id,
            'tenant_id': tenant_id,
            'question_bank_question_topic': question_bank_question_topic,
            'question_bank_question_type': question_bank_question_type,
            'question_bank_question_text': question_bank_question_text,
            'question_bank_question_paragraph_text': question_bank_question_paragraph_text if question_bank_question_paragraph_text and question_bank_question_paragraph_text != "null" else None,
            'question_bank_question_difficulty': question_bank_question_difficulty,
            'question_bank_question_marks': question_bank_question_marks,
            'question_bank_question_negative_marks': question_bank_question_negative_marks,
            'question_bank_question_hint_text': question_bank_question_hint_text if question_bank_question_hint_text and question_bank_question_hint_text != "null" else None,
            'question_bank_question_explanation_text': question_bank_question_explanation_text if question_bank_question_explanation_text and question_bank_question_explanation_text != "null" else None,
            'question_bank_question_order': order_val,
            'question_bank_question_parent_id': parent_val,
            'question_bank_question_is_active': question_bank_question_is_active,
            'question_bank_question_is_deleted': question_bank_question_is_deleted,
            'question_bank_question_created_at': question_bank_question_created_at,
            'question_bank_question_created_by': question_bank_question_created_by,
            'question_bank_question_updated_at': question_bank_question_updated_at,
            'question_bank_question_updated_by': question_bank_question_updated_by,
            'question_bank_question_audio_url': question_bank_question_audio_url if question_bank_question_audio_url and question_bank_question_audio_url != "null" else None,
            'audio_file_url': audio_file_url if audio_file_url and audio_file_url != "null" else None
        }
        
        connection.execute(
    text("""
        UPDATE lms_demo_db.question_bank_questions
        SET
            question_bank_id = :question_bank_id,
            tenant_id = :tenant_id,
            question_bank_question_topic = :question_bank_question_topic,
            question_bank_question_type = :question_bank_question_type,
            question_bank_question_text = :question_bank_question_text,
            question_bank_question_paragraph_text = :question_bank_question_paragraph_text,
            question_bank_question_difficulty = :question_bank_question_difficulty,
            question_bank_question_marks = :question_bank_question_marks,
            question_bank_question_negative_marks = :question_bank_question_negative_marks,
            question_bank_question_hint_text = :question_bank_question_hint_text,
            question_bank_question_explanation_text = :question_bank_question_explanation_text,
            question_bank_question_order = :question_bank_question_order,
            question_bank_question_parent_id = :question_bank_question_parent_id,
            question_bank_question_is_active = :question_bank_question_is_active,
            question_bank_question_is_deleted = :question_bank_question_is_deleted,
            question_bank_question_created_at = :question_bank_question_created_at,
            question_bank_question_created_by = :question_bank_question_created_by,
            question_bank_question_updated_at = :question_bank_question_updated_at,
            question_bank_question_updated_by = :question_bank_question_updated_by,
            question_bank_question_audio_url = :question_bank_question_audio_url,
            audio_file_url = :audio_file_url
        WHERE question_bank_question_id = :question_bank_question_id
    """),
    update_question
)

        message = f"Question updated successfully"

    sync_database_to_vector_db()
    return templates.TemplateResponse(request, "update_question.html", {
        "closest_match": 'No Questions Matched' if similarity_result["similarity"] <= 0 else similarity_result["closest_match"],
        "distance_score": '0' if similarity_result["similarity"] <= 0 else similarity_result["similarity"],
        "result": similarity_result["result"]
    })


@app.get("/delete_question")
async def show_delete_question_form(request: Request):
    return templates.TemplateResponse(request,
        "delete_question.html"
    )


@app.post("/delete_question")
async def delete_question(request: Request,
    question_bank_question_id: int = Form(...)
):
    with engine.begin() as connection:
        if not question_bank_question_id:
            return {"error": "Question ID not found."}
        
        delete_question = {
            'question_bank_question_id': question_bank_question_id
        }
        
        connection.execute(
        text("""
            DELETE FROM lms_demo_db.question_bank_questions WHERE question_bank_question_id = :question_bank_question_id;
        """),
        delete_question
    )
        message = f"Question with ID {question_bank_question_id} deleted successfully"

        return templates.TemplateResponse(request, "delete_question.html", {
        "message": message
    })


@app.get("/prediction")
async def show_prediction_form(request: Request):
    return templates.TemplateResponse(request, "prediction.html")


@app.post("/prediction")
async def prediction(
    request: Request,
    question_bank_question_text: str = Form(...)
):
    similarity_result = similarity_checker(question_bank_question_text)
    difficulty = calculate_difficulty(question_bank_question_text)
    topic = calculate_topic(question_bank_question_text)

    return templates.TemplateResponse(request, "prediction.html", {
        "difficulty": difficulty, 
        "topic": topic,
        "question_text": question_bank_question_text,
        "closest_match": 'No Questions Matched' if similarity_result["similarity"] <= 0 else similarity_result["closest_match"],
        "distance_score": '0' if similarity_result["similarity"] <= 0 else similarity_result["similarity"],
        "result": similarity_result["result"]
    })

@app.get("/classification", include_in_schema=True)
async def classification(request: Request):

    with engine.begin() as connection:
        total = connection.execute(text("""
            SELECT COUNT(*)
            FROM lms_demo_db.question_bank_questions
            WHERE question_bank_question_is_deleted = 0
        """)).scalar() or 0

        diff_count = 0
        top_count = 0
        results = []

        questions = connection.execute(text("""
            SELECT 
                question_bank_question_id,
                question_bank_question_text,
                question_bank_question_difficulty,
                question_bank_question_topic
            FROM lms_demo_db.question_bank_questions
            WHERE question_bank_question_is_deleted = 0
        """)).mappings().all()

        for q in questions:
            question_text = q["question_bank_question_text"]
            pred_diff = calculate_difficulty(question_text)
            pred_top = calculate_topic(question_text)

            results.append({
                **q,
                "predicted_topic": pred_top,
                "predicted_difficulty": pred_diff
            })

            if str(pred_diff).strip().lower() == str(q["question_bank_question_difficulty"]).strip().lower():
                diff_count += 1

            if str(pred_top).strip().lower() == str(q["question_bank_question_topic"]).strip().lower():
                top_count += 1

    difficulty_accuracy = round((diff_count / total) * 100, 2) if total > 0 else 0
    topic_accuracy = round((top_count / total) * 100, 2) if total > 0 else 0

    return templates.TemplateResponse(request, "classification.html", 
        {"data": results, 
         "total_questions": total, 
         "difficulty_accuracy": difficulty_accuracy, 
         "topic_accuracy": topic_accuracy
        })


@app.get("/generator")
async def show_generator_form(request: Request):
    with engine.begin() as connection:
        topic_rows = connection.execute(text("""
            SELECT DISTINCT question_bank_question_topic
            FROM lms_demo_db.question_bank_questions
            WHERE question_bank_question_is_deleted = 0
        """)).mappings().all()

        topics = [
            row["question_bank_question_topic"]
            for row in topic_rows
        ]

    return templates.TemplateResponse(request ,"generator.html", {
        "topics": topics,
        "selected_topic": None,
        "questions": None,
    })


@app.post("/generator")
async def generator(
    request: Request,
    subject: str = Form(...),
    question_bank_question_marks: int = Form(...),
    easy_pct: int = Form(...),
    medium_pct: int = Form(...),
    hard_pct: int = Form(...)
):
    with engine.begin() as connection:
        topic_rows = connection.execute(text("""
            SELECT DISTINCT question_bank_question_topic
            FROM lms_demo_db.question_bank_questions
            WHERE question_bank_question_is_deleted = 0
        """)).mappings().all()

        topics = [
            row["question_bank_question_topic"]
            for row in topic_rows
        ]

    if easy_pct + medium_pct + hard_pct != 100:
        return templates.TemplateResponse("generator.html", {
            "request": request,
            "topics": topics,
            "selected_topic": subject,
            "questions": None,
            "error": "Percentages must sum to 100.",
            "easy_pct": easy_pct,
            "medium_pct": medium_pct,
            "hard_pct": hard_pct,
            "question_bank_question_marks": question_bank_question_marks,
        })

    easy = round(question_bank_question_marks * easy_pct / 100)
    medium = round(question_bank_question_marks * medium_pct / 100)
    hard = question_bank_question_marks - easy - medium

    questions = question_generator(
        subject,                   
        question_bank_question_marks,
        easy,
        medium,
        hard
    )

    total_marks = sum(q["question_bank_question_marks"] for q in questions) if questions else 0

    return templates.TemplateResponse(request, "generator.html", { 
        "topics": topics,
        "selected_topic": subject,
        "questions": questions,
        "total_marks": total_marks,                     
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "easy_pct": easy_pct,
        "medium_pct": medium_pct,
        "hard_pct": hard_pct,
        "question_bank_question_marks": question_bank_question_marks,
    })

@app.get("/get_topics")
async def get_topics():
    with engine.begin() as connection:
        topic_rows = connection.execute(text("""
            SELECT DISTINCT question_bank_question_topic
            FROM lms_demo_db.question_bank_questions
            WHERE question_bank_question_is_deleted = 0
        """)).mappings().all()

        topics = [
            row["question_bank_question_topic"]
            for row in topic_rows
        ]

    return {"topics": topics}


