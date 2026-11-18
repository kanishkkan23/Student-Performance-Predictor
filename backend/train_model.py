import os
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

DATASET_PATH = os.path.join(
    PROJECT_DIR, "dataset", "student_performance.csv"
)

MODEL_PATH = os.path.join(BASE_DIR, "student_model.pkl")

os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)

# Generate dataset if it does not exist
if not os.path.exists(DATASET_PATH):

    np.random.seed(42)

    data = pd.DataFrame({
        "study_hours": np.random.uniform(1, 10, 500),
        "attendance": np.random.uniform(50, 100, 500),
        "previous_score": np.random.uniform(30, 100, 500),
        "assignment_score": np.random.uniform(30, 100, 500)
    })

    noise = np.random.normal(0, 5, 500)

    data["final_score"] = (
        2.5 * data["study_hours"]
        + 0.15 * data["attendance"]
        + 0.35 * data["previous_score"]
        + 0.25 * data["assignment_score"]
        + noise
    )

    data["final_score"] = data["final_score"].clip(0, 100)

    data.to_csv(DATASET_PATH, index=False)

    print("Dataset created successfully!")

# Load dataset
df = pd.read_csv(DATASET_PATH)

X = df[
    [
        "study_hours",
        "attendance",
        "previous_score",
        "assignment_score"
    ]
]

y = df["final_score"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Evaluate model
predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("Model Training Completed!")
print("Training Records:", len(X_train))
print("Testing Records:", len(X_test))
print("MAE:", round(mae, 2))
print("R2 Score:", round(r2, 4))

# Save model
joblib.dump(model, MODEL_PATH)

print("Model saved successfully!")
