
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from fastapi import BackgroundTasks
from email_service import send_prediction_email

from jose import jwt, JWTError

from model import predict_score
from database import (
    init_db,
    save_user,
    get_user_by_id,
    save_prediction,
    get_predictions
)


# Load environment variables from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(
    os.getenv("JWT_EXPIRATION_MINUTES", "60")
)

if not GOOGLE_CLIENT_ID or not JWT_SECRET_KEY:
    raise RuntimeError("Missing GOOGLE_CLIENT_ID or JWT_SECRET_KEY in .env")


app = FastAPI(title="Student Performance Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Initialize database
init_db()

security = HTTPBearer()


class GoogleLoginRequest(BaseModel):
    credential: str


class StudentInput(BaseModel):
    study_hours: float = Field(ge=0, le=24)
    attendance: float = Field(ge=0, le=100)
    previous_score: float = Field(ge=0, le=100)
    assignment_score: float = Field(ge=0, le=100)


def create_access_token(user_id: int):

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRATION_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration,
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = int(payload["sub"])

    except (JWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login token"
        )

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account not found"
        )

    return user


@app.get("/")
def home():
    return {
        "message": "Student Performance Prediction API is running"
    }


# GOOGLE AUTHENTICATION

@app.post("/auth/google")
def google_login(data: GoogleLoginRequest):

    try:
        google_user = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google ID token"
        )

    if not google_user.get("email_verified"):
        raise HTTPException(
            status_code=401,
            detail="Google email is not verified"
        )

    google_id = google_user.get("sub")
    name = google_user.get("name")
    email = google_user.get("email")
    picture = google_user.get("picture")

    if not google_id or not name or not email:
        raise HTTPException(
            status_code=400,
            detail="Required Google account information is missing"
        )

    user = save_user(
        google_id,
        name,
        email,
        picture
    )

    access_token = create_access_token(user["id"])

    return {
        "message": "Google login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# GET LOGGED-IN USER

@app.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    return user


# STUDENT PERFORMANCE PREDICTION


@app.post("/predict")
def predict(
    data: StudentInput,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):

    predicted_score = predict_score(
        data.study_hours,
        data.attendance,
        data.previous_score,
        data.assignment_score
    )

    if predicted_score >= 85:
        performance = "Excellent"
    elif predicted_score >= 70:
        performance = "Good"
    elif predicted_score >= 50:
        performance = "Average"
    else:
        performance = "Needs Improvement"

    # Save prediction in SQLite
    prediction_id = save_prediction(
        user["id"],
        data.study_hours,
        data.attendance,
        data.previous_score,
        data.assignment_score,
        predicted_score,
        performance
    )

    # Schedule email notification
    background_tasks.add_task(
        send_prediction_email,
        user["email"],
        user["name"],
        data.study_hours,
        data.attendance,
        data.previous_score,
        data.assignment_score,
        predicted_score,
        performance
    )

    return {
        "id": prediction_id,
        "predicted_score": predicted_score,
        "performance": performance,
        "message": "Prediction completed. Email notification scheduled."
    }



# PERSONAL PREDICTION HISTORY

@app.get("/history")
def history(user: dict = Depends(get_current_user)):
    return get_predictions(user["id"])
