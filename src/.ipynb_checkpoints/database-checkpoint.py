import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

try:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    print("Database connection successful!")
    conn.close()
except Exception as e:
    print("Failed to connect to database")
    print(e)

