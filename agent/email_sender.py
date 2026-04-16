import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def send_digest(digest: str, subject: str = "Job Scout — Your Daily Matches") -> bool:
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    EMAIL_TO = os.getenv("EMAIL_TO")

    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not EMAIL_TO:
        logging.warning(
            "Missing email configuration: GMAIL_USER, GMAIL_APP_PASSWORD, or EMAIL_TO"
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject

        msg.attach(MIMEText(digest, _subtype="plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        logging.info(f"Digest email sent to {EMAIL_TO}")
        return True

    except Exception as e:
        logging.error(f"Failed to send digest email: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = send_digest("This is a test email from your Job Scout Agent.")
    print(f"Sent: {result}")
