import bcrypt
from utils.helpers import get_db_connection


# ==============================
# ➕ CREATE USER
# ==============================
def create_user(name, email, password, phone, has_bike):

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ✅ Check if user exists
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return {"status": False, "message": "Email already exists"}

        # ✅ Hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # ✅ Insert user
        cursor.execute("""
            INSERT INTO users (name, email, password, phone, has_bike)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, hashed_password, phone, has_bike))

        conn.commit()

        return {
            "status": True,
            "message": "User created successfully"
        }

    except Exception as e:
        print("CREATE USER ERROR:", e)
        return {
            "status": False,
            "message": "Database error"
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🔍 GET USER BY EMAIL
# ==============================
def get_user_by_email(email):

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        return cursor.fetchone()

    except Exception as e:
        print("GET USER ERROR:", e)
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🔍 GET USER BY ID
# ==============================
def get_user_by_id(user_id):

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        return cursor.fetchone()

    except Exception as e:
        print("GET USER BY ID ERROR:", e)
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# ✏️ UPDATE USER (PROFILE)
# ==============================
def update_user(user_id, name, phone, has_bike):

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET name=%s, phone=%s, has_bike=%s
            WHERE id=%s
        """, (name, phone, has_bike, user_id))

        conn.commit()

        return {
            "status": True,
            "message": "User updated successfully"
        }

    except Exception as e:
        print("UPDATE USER ERROR:", e)
        return {
            "status": False,
            "message": "Update failed"
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()