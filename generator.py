import random
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)


def question_generator(subject, marks, easy, medium, hard):

    marks = int(marks)

    if marks <= 0:
        return []

    if not subject:
        return []

    with engine.begin() as connection:
        rows = connection.execute(text("""
            SELECT
                question_bank_question_id,
                question_bank_question_text,
                question_bank_question_marks,
                question_bank_question_difficulty,
                question_bank_question_type,
                question_bank_question_topic
            FROM lms_demo_db.question_bank_questions
            WHERE question_bank_question_topic = :subject
            AND question_bank_question_is_deleted = 0
        """), {"subject": subject}).mappings().all()

    questions_list = [dict(q) for q in rows]

    if not questions_list:
        return []

    random.shuffle(questions_list)

    total_available = sum(q["question_bank_question_marks"] for q in questions_list)


    if marks > total_available:
        return questions_list

    def find_exact(questions, target, index=0):
        if target == 0:
            return []
        if target < 0 or index >= len(questions):
            return None

        q = questions[index]

        with_q = find_exact(questions, target - q["question_bank_question_marks"], index + 1)
        if with_q is not None:
            return [q] + with_q

        return find_exact(questions, target, index + 1)

    result = find_exact(questions_list, marks)

    if result is None:
        return []

    return result