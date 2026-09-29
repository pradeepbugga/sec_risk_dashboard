import os

import psycopg2


def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "sec_filings"),
        user=os.getenv("DB_USER", "myuser"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )
    return conn