import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score



df = pd.read_excel("question_bank_questions.xlsx")

# remove extra spaces from column names
df.columns = df.columns.str.strip()

# features
X = df["question_text"].astype(str)

# targets
y_diff = df["difficulty"]
y_top = df["topic"]


(
    X_train,
    X_test,
    y_diff_train,
    y_diff_test,
    y_top_train,
    y_top_test
) = train_test_split(
    X,
    y_diff,
    y_top,
    test_size=0.2,
    random_state=42
)



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