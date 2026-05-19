import pandas as pd
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Form
from prediction import calculate_difficulty, calculate_topic
from generator import question_generator
from datetime import datetime
from sqlalchemy import create_engine, text, select, Integer

app = FastAPI()
templates = Jinja2Templates(directory="templates")

df = pd.read_excel("question_bank_questions.xlsx")
df.columns = df.columns.str.strip().str.lower()

DATABASE_URL = "mysql+pymysql://db_local_user:yD94Q34eI@192.168.1.88:3306/lms_demo_db"
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

    return {"message": "Question added successfully"}