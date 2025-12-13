import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import time
import logging
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DB", "mydatabase"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
}

def get_conn(max_retries: int = 10, retry_delay: int = 3):
    """Get PostgreSQL connection with automatic retry"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                dbname=DB_CONFIG["dbname"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                connect_timeout=5
            )
            logger.info(f"✅ PostgreSQL connection established (attempt {attempt + 1})")
            return conn
        except psycopg2.OperationalError as e:
            logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Failed to connect to PostgreSQL after all retries")
                raise ConnectionError(f"Could not connect to database: {e}")
    return None

def create_table_if_not_exists():
    """Create contacts table if it doesn't exist"""
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
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            logger.info("✅ Contacts table ready")
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_contact(name: str, email: Optional[str] = None, 
                   phone: Optional[str] = None, notes: Optional[str] = None) -> int:
    """Create a new contact and return its ID"""
    sql = """
    INSERT INTO contacts (name, email, phone, notes)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (name, email, phone, notes))
            new_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"✅ Contact created with ID: {new_id}")
            return new_id
    except Exception as e:
        logger.error(f"❌ Error creating contact: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_all_contacts() -> List[Dict[str, Any]]:
    """Get all contacts"""
    sql = """
    SELECT id, name, email, phone, notes, 
           TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at
    FROM contacts 
    ORDER BY created_at DESC;
    """
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return rows
    except Exception as e:
        logger.error(f"❌ Error fetching contacts: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_contact_by_id(contact_id: int) -> Optional[Dict[str, Any]]:
    """Get a contact by ID"""
    sql = """
    SELECT id, name, email, phone, notes, 
           TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at
    FROM contacts 
    WHERE id = %s;
    """
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (contact_id,))
            return cur.fetchone()
    except Exception as e:
        logger.error(f"❌ Error fetching contact {contact_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_contact(contact_id: int, name: str, email: str, 
                   phone: str, notes: str) -> bool:
    """Update a contact"""
    sql = """
    UPDATE contacts
    SET name = %s, email = %s, phone = %s, notes = %s
    WHERE id = %s;
    """
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (name, email, phone, notes, contact_id))
            conn.commit()
            updated = cur.rowcount > 0
            if updated:
                logger.info(f"✅ Contact {contact_id} updated")
            return updated
    except Exception as e:
        logger.error(f"❌ Error updating contact {contact_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_contact(contact_id: int) -> bool:
    """Delete a contact"""
    sql = "DELETE FROM contacts WHERE id = %s;"
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (contact_id,))
            conn.commit()
            deleted = cur.rowcount > 0
            if deleted:
                logger.info(f"✅ Contact {contact_id} deleted")
            return deleted
    except Exception as e:
        logger.error(f"❌ Error deleting contact {contact_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def search_contacts(search_term: str) -> List[Dict[str, Any]]:
    """Search contacts by name, email, or phone"""
    sql = """
    SELECT id, name, email, phone, notes,
           TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at
    FROM contacts 
    WHERE name ILIKE %s OR email ILIKE %s OR phone ILIKE %s
    ORDER BY created_at DESC;
    """
    
    search_pattern = f"%{search_term}%"
    conn = None
    try:
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (search_pattern, search_pattern, search_pattern))
            return cur.fetchall()
    except Exception as e:
        logger.error(f"❌ Error searching contacts: {e}")
        return []
    finally:
        if conn:
            conn.close()
