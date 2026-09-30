import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row


load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

def get_db():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn