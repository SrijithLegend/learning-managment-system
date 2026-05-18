import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score


df = pd.read_excel("question_bank_questions.xlsx")
df.columns = df.columns.str.strip()

X = df["question_text"].astype(str) 
y_diff = df["difficulty"]
y_top = df["topic"]

X_train, X_test, y_train_diff, y_test_diff = train_test_split(X, y_diff, test_size=0.2, random_state=42)
_, _, y_train_top, y_test_top = train_test_split(X, y_top, test_size=0.2, random_state=42)

vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test) 

model_diff = LogisticRegression(max_iter=1000)
model_diff.fit(X_train_vec, y_train_diff)

model_top = LinearSVC(C=1.0, max_iter=1000)
model_top.fit(X_train_vec, y_train_top)

diff_preds = model_diff.predict(X_test_vec)
print(f"Difficulty Prediction Accuracy: {accuracy_score(y_test_diff, diff_preds) * 100:.2f}%")

def calculate_difficulty(question_text):
    if not question_text.strip(): return "Unknown"
    transformed = vectorizer.transform([question_text])
    return model_diff.predict(transformed)[0]

def calculate_topic(question_text):
    if not question_text.strip(): return "Unknown"
    transformed = vectorizer.transform([question_text])
    return model_top.predict(transformed)[0]