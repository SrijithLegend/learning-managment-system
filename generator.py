import pandas as pd
import random

def question_generator(marks, subject, easy , medium, hard):

    df = pd.read_excel("question_bank_questions.xlsx")
    df.columns = df.columns.str.strip()
    df["marks"] = pd.to_numeric(df["marks"], errors="coerce").fillna(0).astype(int)

    if marks <= 0:
        return []

    if subject not in df["subject"].unique():
        return []

    filtered_df = df[df["subject"] == subject]
    questions_list = list(filtered_df.itertuples())
    random.shuffle(questions_list)

    total_available = sum(q.marks for q in questions_list)            
    if marks > total_available:                                        
        return [{"question_id": q.question_id, "question_text": q.question_text, "marks": q.marks, "difficulty": q.difficulty, "options": q.options, "correct_answer": q.correct_answer, "explanation": q.explanation} for q in questions_list]  # Added

    def find_exact(questions, target, index=0):

        if target == 0:
            return []                                                
        if target < 0 or index >= len(questions):
            return None                                                 

        q = questions[index]

        with_q = find_exact(questions, target - q.marks, index + 1)
        if with_q is not None:
            return [q] + with_q
        
        without_q = find_exact(questions, target, index + 1)
        return without_q

    result = find_exact(questions_list, marks)

    if result is None:
        return []                                                            

    return [
        {
            "question_id": q.question_id,
            "question_text": q.question_text,
            "marks": q.marks,
            "difficulty": q.difficulty,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation
        }
        for q in result
    ]