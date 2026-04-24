import bcrypt
from utils.helpers import get_db_connection

def create_user(name, email, password, phone, has_bike):
    conn = get_db_connection()
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    query = """
    INSERT INTO users (name, email, password, phone, has_bike)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (name, email, hashed_password, phone, has_bike))
    conn.commit()

    cursor.close()
    conn.close()
    return True


def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


# 🔥 EXTRA (needed later)
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user