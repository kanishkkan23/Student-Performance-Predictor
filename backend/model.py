import os
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "student_model.pkl")

model = joblib.load(MODEL_PATH)

def predict_score(study_hours, attendance,
                  previous_score, assignment_score):

    input_data = np.array([[
        study_hours,
        attendance,
        previous_score,
        assignment_score
    ]])

    prediction = model.predict(input_data)[0]

    prediction = float(np.clip(prediction, 0, 100))

    return round(prediction, 2)

