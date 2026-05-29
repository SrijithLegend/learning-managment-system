import joblib

vectorizer = joblib.load("vectorizer.pkl")

model_diff = joblib.load("model_diff.pkl")

model_top = joblib.load("model_top.pkl")


def calculate_difficulty(question_text):

    if not question_text.strip():
        return "Unknown"

    transformed = vectorizer.transform([question_text])

    prediction = model_diff.predict(transformed)[0]

    return prediction


def calculate_topic(question_text):

    if not question_text.strip():
        return "Unknown"

    transformed = vectorizer.transform([question_text])

    prediction = model_top.predict(transformed)[0]

    return prediction



question = ""

difficulty = calculate_difficulty(question)

topic = calculate_topic(question)

print(f"Question: {question}")

print(f"Predicted Difficulty: {difficulty}")

print(f"Predicted Topic: {topic}")