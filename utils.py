
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import random
import bcrypt

# Load environment variables
load_dotenv()


# =========================================================
# EMAIL CONFIGURATION
# =========================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.getenv("email")
SENDER_PASSKEY = os.getenv("passkey")


# =========================================================
# SEND EMAIL
# =========================================================

def SendEmail(to_email: str, subject: str, body: str):

    msg = MIMEMultipart()

    msg["To"] = to_email
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL

    msg.attach(MIMEText(body, "plain"))

    try:

        # Establish server connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

        # Start TLS
        server.starttls()

        # Login to Gmail
        server.login(SENDER_EMAIL, SENDER_PASSKEY)

        # Send email
        server.sendmail(
            SENDER_EMAIL,
            to_email,
            msg.as_string()
        )

        # Close server
        server.quit()

        return True, "Mail sent successfully"

    except Exception as e:

        return False, f"Something wrong while sending an email: {e}"


# =========================================================
# GENERATE OTP
# =========================================================

def generate_otp():

    otp = random.randint(1000, 9999)

    return otp


# =========================================================
# EMAIL TEMPLATES
# =========================================================

class EmailTemapltes:

    # -----------------------------------------------------
    # OTP EMAIL TEMPLATE
    # -----------------------------------------------------

    @staticmethod
    def OTPEmailTempalte(
        otp: int,
        username: str = "user"
    ):

        template = f"""
Dear {username},

Thank you for choosing SNS App to manage your notes and files.

Your Registration OTP is:

{otp}

If you did not register for this app, simply ignore this email.

Please do not share your OTP with anyone.

Regards,
SNS App
"""

        return template


    # -----------------------------------------------------
    # RESET PASSWORD EMAIL TEMPLATE
    # -----------------------------------------------------

    @staticmethod
    def resetpasswordEmaliTemplate(
        username: str,
        url: str
    ):

        template = f"""
Dear {username},

You requested to reset your password for the SNS App.

Please click the link below to reset your password:

{url}

This password reset link will expire after 10 minutes.

If you did not request a password reset, simply ignore this email.

Regards,
SNS App
"""

        return template


# =========================================================
# PASSWORD HASHING
# =========================================================

def generateHashPassword(password: str):

    # Convert password from string to bytes
    password_bytes = password.encode("utf-8")

    # Generate salt
    salt = bcrypt.gensalt()

    # Generate hashed password
    hash_password = bcrypt.hashpw(
        password_bytes,
        salt
    )

    # Convert bytes to string before storing in MySQL
    return hash_password.decode("utf-8")


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verifyHashPassword(
    password: str,
    hash_password: str
):

    # Convert entered password to bytes
    password_bytes = password.encode("utf-8")

    # Convert stored hash from string to bytes
    hash_password_bytes = hash_password.encode("utf-8")

    # Compare password with stored hash
    status = bcrypt.checkpw(
        password_bytes,
        hash_password_bytes
    )

    return status