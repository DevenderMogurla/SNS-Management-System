
import os

import mysql.connector as SQLC
from dotenv import load_dotenv

load_dotenv()

LAST_ERROR = ""


def getLastError():
    return LAST_ERROR


# =========================================================
# DATABASE CONNECTION
# =========================================================

def DatabaseConnection():

    global LAST_ERROR

    try:

        connection = SQLC.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "mysqlpassword"),
            database=os.getenv("DB_NAME", "sns_management1"),
        )

        return connection

    except Exception as e:

        LAST_ERROR = str(e)

        print(
            f"Something wrong in database/connection.py: {e}"
        )

        return None