import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine

df = pd.read_excel("question_bank_questions.xlsx")
df.columns = df.columns.str.strip().str.lower()

DATABASE_URL = "mysql+pymysql://db_local_user:yD94Q34eI@192.168.1.88:3306/lms_demo_db"

engine = create_engine(DATABASE_URL)

column_mapping = {
    "topic": "question_bank_question_topic",
    "question_type": "question_bank_question_type",
    "question_text": "question_bank_question_text",
    "difficulty": "question_bank_question_difficulty",
    "marks": "question_bank_question_marks",
}

df = df.rename(columns=column_mapping)

df["tenant_id"] = 19
df["question_bank_id"] = 1
df["question_bank_question_paragraph_text"] = None
df["question_bank_question_negative_marks"] = 0
df["question_bank_question_hint_text"] = None
df["question_bank_question_explanation_text"] = df.get("explanation", None)
df["question_bank_question_order"] = None
df["question_bank_question_parent_id"] = None
df["question_bank_question_is_active"] = 1
df["question_bank_question_is_deleted"] = 0
df["question_bank_question_created_at"] = datetime.now()
df["question_bank_question_created_by"] = 16
df["question_bank_question_updated_at"] = datetime.now()
df["question_bank_question_updated_by"] = 16
df["question_bank_question_audio_url"] = None
df["audio_file_url"] = None

mysql_columns = [
    "tenant_id",
    "question_bank_id",
    "question_bank_question_topic",
    "question_bank_question_type",
    "question_bank_question_text",
    "question_bank_question_paragraph_text",
    "question_bank_question_difficulty",
    "question_bank_question_marks",
    "question_bank_question_negative_marks",
    "question_bank_question_hint_text",
    "question_bank_question_explanation_text",
    "question_bank_question_order",
    "question_bank_question_parent_id",
    "question_bank_question_is_active",
    "question_bank_question_is_deleted",
    "question_bank_question_created_at",
    "question_bank_question_created_by",
    "question_bank_question_updated_at",
    "question_bank_question_updated_by",
    "question_bank_question_audio_url",
    "audio_file_url",
]

df = df[mysql_columns]

df = df.drop_duplicates(subset=["question_bank_question_text"])

df.to_sql(
    name="question_bank_questions",
    con=engine,
    if_exists="append",
    index=False,
)

print("Excel data imported into MySQL successfully.")