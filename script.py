import pandas as pd
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Form
from prediction import calculate_difficulty, calculate_topic
from generator import question_generator


class Question(BaseModel):
    question_id: int
    question_text: str
    subject: str
    topic: str
    question_type: str
    difficulty: str
    marks: int
    options: str
    correct_answer: str
    explanation: str

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def load_data():
    df = pd.read_excel("data.xlsx")
    df.columns = df.columns.str.strip()
    return df


def analyze_questions():
    df = load_data()
    duplicate_count = int(df.duplicated(subset=["question_text"]).sum())
    
    if duplicate_count > 0:
        df = df.drop_duplicates(subset=["question_text"], keep='first')
        df.to_excel("data.xlsx", index=False)

    return {
        "total_questions": len(df),
        "questions_by_subject": df["subject"].value_counts().to_dict(),
        "questions_by_topic": df["topic"].value_counts().to_dict(),
        "questions_by_difficulty": df["difficulty"].value_counts().to_dict(),
        "questions_by_type": df["question_type"].value_counts().to_dict(),
        "total_marks": int(df["marks"].sum()),
        "missing_values": df.isnull().sum().to_dict(),

        "duplicate_questions": int(df.duplicated(subset=["question_text"]).sum())
    }


@app.get("/",include_in_schema=True)
async def get_summary(request: Request):
    summary = analyze_questions()
    return templates.TemplateResponse(request, 'summary.html', {"data": summary})


@app.get("/questions", include_in_schema=True)
async def get_questions(request: Request):

    df = load_data()
    selected_df = df[['question_id', 'question_text']]
    questions = selected_df.to_dict(orient="records")
    
    return templates.TemplateResponse(request, 'questions.html', {"data": questions})


@app.get("/add_question")
async def show_add_question_form(request: Request):
    return templates.TemplateResponse(request,
        "add_question.html"
    )


@app.post("/add_question")
async def add_question(
    request: Request,
    question_id: int = Form(...),
    question_text: str = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    question_type: str = Form(...),
    difficulty: str = Form(...),
    marks: int = Form(...),
    options: str = Form(""),
    correct_answer: str = Form(...),
    explanation: str = Form("")
):
    df = load_data()

    if question_id in df["question_id"].values:
        return {"error": "Question ID already exists."}

    if question_text in df["question_text"].values:
        return {"error": "Question text already exists."}

    new_question = {
        "question_id": question_id,
        "question_text": question_text,
        "subject": subject,
        "topic": topic,
        "question_type": question_type,
        "difficulty": difficulty,
        "marks": marks,
        "options": options,
        "correct_answer": correct_answer,
        "explanation": explanation
    }

    df = pd.concat([df, pd.DataFrame([new_question])], ignore_index=True)
    df.to_excel("data.xlsx", index=False)

    return {"message": "Question added successfully"}


@app.get("/update_question")
async def show_update_question_form(request: Request):
    return templates.TemplateResponse(request,
        "update_question.html"
    )


@app.post("/update_question")
async def update_question(
    request: Request,
    question_id: int = Form(...),
    question_text: str = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    question_type: str = Form(...),
    difficulty: str = Form(...),
    marks: int = Form(...),
    options: str = Form(""),
    correct_answer: str = Form(...),
    explanation: str = Form("")
):

    df = load_data()

    if question_id not in df["question_id"].values:
        return {"error": "Question ID not found."}

    idx = df.index[df["question_id"] == question_id][0]

    df.at[idx, "question_text"] = question_text
    df.at[idx, "subject"] = subject
    df.at[idx, "topic"] = topic
    df.at[idx, "question_type"] = question_type
    df.at[idx, "difficulty"] = difficulty
    df.at[idx, "marks"] = marks
    df.at[idx, "options"] = options
    df.at[idx, "correct_answer"] = correct_answer
    df.at[idx, "explanation"] = explanation

    df.to_excel("data.xlsx", index=False)

    return {"message": "Question updated successfully"}

@app.get("/delete_question")
async def show_delete_question_form(request: Request):
    return templates.TemplateResponse(request,
        "delete_question.html"
    )


@app.post("/delete_question")
async def delete_question(
    request: Request,
    question_id: int = Form(...)
):
    df = load_data()

    if question_id not in df["question_id"].values:
        return {"error": "Question ID not found."}

    df = df[df["question_id"] != question_id]
    df.to_excel("data.xlsx", index=False)

    return {"message": "Question deleted successfully"}


@app.get("/prediction")
async def show_prediction_form(request: Request):
    return templates.TemplateResponse(request, "prediction.html")


@app.post("/prediction")
async def prediction(
    request: Request,
    question_text: str = Form(...)
):
    df = load_data()

    difficulty = calculate_difficulty(question_text)
    topic = calculate_topic(question_text)

    return templates.TemplateResponse(request, "prediction.html", {
        "difficulty": difficulty, 
        "topic": topic,
        "question_text": question_text
    })


@app.get("/classification", include_in_schema=True)
async def classification(request: Request):
    df = load_data()
    total = len(df)
    df.columns = df.columns.str.strip().str.lower()
    
    diff_count = 0
    top_count = 0
    results = []

    questions = df[["question_id", "question_text", "difficulty", "topic"]].to_dict(orient="records")

    for q in questions:
        question_text = str(q["question_text"])
        pred_diff = calculate_difficulty(question_text)
        pred_top = calculate_topic(question_text)

        results.append({
            **q, 
            "predicted_topic": pred_top, 
            "predicted_difficulty": pred_diff
        })

        if str(pred_diff).strip().lower() == str(q["difficulty"]).strip().lower():
            diff_count += 1
        if str(pred_top).strip().lower() == str(q["topic"]).strip().lower():
            top_count += 1

    difficulty_accuracy = round((diff_count / total) * 100, 2) if total > 0 else 0
    topic_accuracy = round((top_count / total) * 100, 2) if total > 0 else 0

    return templates.TemplateResponse(request, "classification.html", {
        "data": results,
        "total_questions": total,
        "difficulty_accuracy": difficulty_accuracy,
        "topic_accuracy": topic_accuracy
    })


@app.get('/generator')
async def show_generator_form(request: Request, subject: str = None):
    df = load_data()
    subjects = df["subject"].unique().tolist()

    return templates.TemplateResponse(request, "generator.html", {
        "subjects": subjects,
        "selected_subject": subject,
        "questions": None,
    })


@app.post('/generator')
async def generator(
    request: Request,
    marks: int = Form(...),
    subject: str = Form(...)
):
    df = load_data()
    subjects = df["subject"].unique().tolist()                            
    topics = df[df["subject"] == subject]["topic"].unique().tolist()   

    questions = question_generator(marks, subject)         
    total_q = len(questions)
    easy = sum(1 for q in questions if q["difficulty"] == "Easy")
    medium = sum(1 for q in questions if q["difficulty"] == "Medium")
    hard = sum(1 for q in questions if q["difficulty"] == "Hard")

    easy_pct = round(easy / total_q * 100) if total_q > 0 else 0
    medium_pct = round(medium / total_q * 100) if total_q > 0 else 0
    hard_pct = round(hard / total_q * 100) if total_q > 0 else 0   

    return templates.TemplateResponse(request, "generator.html", {
        "marks": marks,
        "subject": subject,
        "subjects": subjects,
        "selected_subject": subject,
        "questions": questions,
        "topics": topics,
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "easy_pct": easy_pct,
        "medium_pct": medium_pct,
        "hard_pct": hard_pct
    })

@app.get("/get_topics")
async def get_topics(subject: str):
    df = load_data()
    topics = df[df["subject"] == subject]["topic"].unique().tolist()
    return {"topics": topics}
