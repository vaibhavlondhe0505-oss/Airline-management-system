# db.py
import mysql.connector
from config import Config

def get_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )
