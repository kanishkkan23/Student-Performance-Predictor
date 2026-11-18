
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "student_predictions.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_hours REAL NOT NULL,
            attendance REAL NOT NULL,
            previous_score REAL NOT NULL,
            assignment_score REAL NOT NULL,
            predicted_score REAL NOT NULL,
            performance TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    columns = connection.execute(
        "PRAGMA table_info(predictions)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "user_id" not in column_names:
        connection.execute("""
            ALTER TABLE predictions
            ADD COLUMN user_id INTEGER REFERENCES users(id)
        """)

    connection.commit()
    connection.close()


def save_user(google_id, name, email, picture):
    connection = get_connection()

    connection.execute("""
        INSERT INTO users (google_id, name, email, picture)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(google_id) DO UPDATE SET
            name = excluded.name,
            email = excluded.email,
            picture = excluded.picture
    """, (google_id, name, email, picture))

    user = connection.execute("""
        SELECT * FROM users WHERE google_id = ?
    """, (google_id,)).fetchone()

    connection.commit()
    connection.close()

    return dict(user)


def get_user_by_id(user_id):
    connection = get_connection()

    user = connection.execute("""
        SELECT id, google_id, name, email, picture, created_at
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    connection.close()

    return dict(user) if user else None


def save_prediction(user_id, study_hours, attendance,
                    previous_score, assignment_score,
                    predicted_score, performance):

    connection = get_connection()

    cursor = connection.execute("""
        INSERT INTO predictions (
            user_id,
            study_hours,
            attendance,
            previous_score,
            assignment_score,
            predicted_score,
            performance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        study_hours,
        attendance,
        previous_score,
        assignment_score,
        predicted_score,
        performance
    ))

    connection.commit()
    prediction_id = cursor.lastrowid
    connection.close()

    return prediction_id


def get_predictions(user_id):
    connection = get_connection()

    rows = connection.execute("""
        SELECT * FROM predictions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 50
    """, (user_id,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]
