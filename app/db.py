
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

def get_conn():
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    return conn

def create_table_if_not_exists():
    sql = """
    CREATE TABLE IF NOT EXISTS contacts (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT UNIQUE,
      phone TEXT,
      notes TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()

def create_contact(name, email=None, phone=None, notes=None):
    sql = """
    INSERT INTO contacts (name, email, phone, notes)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, email, phone, notes))
                new_id = cur.fetchone()[0]
                return new_id
    finally:
        conn.close()

def get_all_contacts():
    sql = "SELECT id, name, email, phone, notes, created_at FROM contacts ORDER BY id;"
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                return rows
    finally:
        conn.close()

def get_contact_by_id(contact_id):
    sql = "SELECT id, name, email, phone, notes, created_at FROM contacts WHERE id = %s;"
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (contact_id,))
                return cur.fetchone()
    finally:
        conn.close()

def update_contact(contact_id, name, email, phone, notes):
    sql = """
    UPDATE contacts
    SET name=%s, email=%s, phone=%s, notes=%s
    WHERE id=%s;
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, email, phone, notes, contact_id))
                return cur.rowcount  # number of rows updated
    finally:
        conn.close()

def delete_contact(contact_id):
    sql = "DELETE FROM contacts WHERE id = %s;"
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (contact_id,))
                return cur.rowcount
    finally:
        conn.close()
