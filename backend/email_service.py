
import os
import smtplib
import logging

from email.message import EmailMessage
from html import escape

from dotenv import load_dotenv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")


def send_prediction_email(
    recipient_email,
    student_name,
    study_hours,
    attendance,
    previous_score,
    assignment_score,
    predicted_score,
    performance
):

    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        logging.error("SMTP credentials are missing.")
        return False

    safe_name = escape(student_name)

    message = EmailMessage()

    message["Subject"] = "Your Student Performance Prediction Result"
    message["From"] = SMTP_EMAIL
    message["To"] = recipient_email

    message.set_content(f"""
Hello {student_name},

Your student performance prediction has been completed.

Prediction Details:

Study Hours: {study_hours}
Attendance: {attendance}%
Previous Score: {previous_score}
Assignment Score: {assignment_score}

Predicted Score: {predicted_score}
Performance: {performance}

Keep working towards your academic goals!

Regards,
Student Performance Prediction System
""")

    message.add_alternative(f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">

    <h2 style="color: #2563eb;">
        Student Performance Prediction
    </h2>

    <p>Hello <b>{safe_name}</b>,</p>

    <p>Your performance prediction has been completed successfully.</p>

    <table border="1" cellpadding="10" cellspacing="0"
           style="border-collapse: collapse;">

        <tr><td>Study Hours</td><td>{study_hours}</td></tr>
        <tr><td>Attendance</td><td>{attendance}%</td></tr>
        <tr><td>Previous Score</td><td>{previous_score}</td></tr>
        <tr><td>Assignment Score</td><td>{assignment_score}</td></tr>

        <tr>
            <td><b>Predicted Score</b></td>
            <td><b>{predicted_score}</b></td>
        </tr>

        <tr>
            <td><b>Performance</b></td>
            <td><b>{performance}</b></td>
        </tr>

    </table>

    <p>Keep working towards your academic goals!</p>

    <p>Regards,<br>
    Student Performance Prediction System</p>

</body>
</html>
""", subtype="html")

    try:

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)

            server.send_message(message)

        logging.info("Prediction email sent successfully.")
        return True

    except Exception:

        logging.exception("Failed to send prediction email.")
        return False
