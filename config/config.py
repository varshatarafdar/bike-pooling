import mysql.connector

# 🔐 SECRET KEY
SECRET_KEY = "27cabedd3523a9e2f1c329f6733b2a9119356aebac75c40fc8691c1298eababe"

# 🗄️ DATABASE CONFIG
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "", 
    "database": "bike_pooling_2"
}
# ✅ ADD THIS (IMPORTANT)

# 🔗 DB CONNECTION FUNCTION
def get_db_connection():
    return mysql.connector.connect()