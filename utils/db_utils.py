import psycopg2
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash


def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="Underwritter",
        user="postgres",
        password="United2025",
        port="5432"
    )

def insert_vehicle_inspection(df, user_id):
    conn = get_connection()
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO vehicle_inspection 
            (user_id, client_name, model_year, make_name, sub_make_name, tracker_id, suminsured, clam_amount, grosspremium, netpremium, no_of_claims, vehicle_capacity)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            row['CLIENT_NAME'],
            row['MODEL_YEAR'],
            row['MAKE_NAME'],
            row['SUB_MAKE_NAME'],
            row['TRACKER_ID'],
            row['SUMINSURED'],
            row['CLM_AMOUNT'],
            row['GROSSPREMIUM'],
            row['NETPREMIUM'],
            row['NO_OF_CLAIMS'],
            row['VEHICLE_CAPACITY']
        ))
    conn.commit()
    cur.close()
    conn.close()

# ✅ ADD: Get avg claims + capacity for Risk Profile
def get_vehicle_claims(make_name, sub_make_name, model_year):
    conn = get_connection()
    cur = conn.cursor()

    if model_year == 2025:
        query = """
            SELECT 
                AVG(no_of_claims)::FLOAT, 
                AVG(vehicle_capacity)::FLOAT
            FROM vehicle_inspection
            WHERE upper(make_name) = %s
            AND upper(sub_make_name) = %s
            AND model_year BETWEEN 2020 AND 2024
            AND no_of_claims > 0
        """
        cur.execute(query, (make_name.upper(), sub_make_name.upper()))
    else:
        query = """
            SELECT 
                AVG(no_of_claims)::FLOAT, 
                AVG(vehicle_capacity)::FLOAT
            FROM vehicle_inspection
            WHERE upper(make_name) = %s
            AND upper(sub_make_name) = %s
            AND model_year = %s
            AND no_of_claims > 0
        """
        cur.execute(query, (make_name.upper(), sub_make_name.upper(), model_year))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

# ✅ ADD: Insert calculated Risk Profile
def insert_vehicle_risk(user_id, driver_age, make_name, sub_make_name, model_year, capacity, num_claims, risk_level):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO vehicle_risk
        (user_id, driver_age, make_name, sub_make_name, model_year, capacity, num_claims, risk_level, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        user_id,
        driver_age,
        make_name,
        sub_make_name,
        model_year,
        capacity,
        num_claims,
        risk_level,
        datetime.now()
    ))

    risk_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return risk_id



# --- In db_utils.py ---

def get_latest_suminsured_netpremium(make_name, sub_make_name, model_year):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT suminsured, netpremium
        FROM vehicle_inspection
        WHERE upper(make_name) = %s
        AND upper(sub_make_name) = %s
        AND model_year = %s
        ORDER BY id DESC LIMIT 1
    """
    cur.execute(query, (make_name.upper(), sub_make_name.upper(), model_year))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_tracker_id(make_name, sub_make_name, model_year):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT tracker_id
        FROM vehicle_inspection
        WHERE upper(make_name) = %s
        AND upper(sub_make_name) = %s
        AND model_year = %s
        ORDER BY id DESC LIMIT 1
    """
    cur.execute(query, (make_name.upper(), sub_make_name.upper(), model_year))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_risk_level(risk_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT risk_level FROM vehicle_risk WHERE id = %s", (risk_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def update_vehicle_risk_premium(risk_id, premium_rate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE vehicle_risk
        SET premium_rate = %s
        WHERE id = %s
    """, (premium_rate, risk_id))

    conn.commit()
    cur.close()
    conn.close()


def create_user(username, password, cnic, make_name):
    conn = get_connection()
    cur = conn.cursor()
    hashed_pw = generate_password_hash(password)
    cur.execute(
        sql.SQL("INSERT INTO users (username, password, cnic, make_name) VALUES (%s, %s, %s, %s)"),
        [username, hashed_pw, cnic, make_name]
    )
    conn.commit()
    cur.close()
    conn.close()

def validate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result and check_password_hash(result[1], password):
        return (result[0], username)  # ✅ tuple
    return None




def insert_vehicle_prediction(make_name, sub_make_name, model_year, avg_netpremium, suminsured, final_premium_rate, risk_level):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO vehicle_premium_predictions 
        (make_name, sub_make_name, model_year, avg_netpremium, suminsured, final_premium_rate, risk_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (make_name, sub_make_name, model_year, avg_netpremium, suminsured, final_premium_rate, risk_level))
    conn.commit()
    cur.close()
    conn.close()



# ✅ Add this function below your existing functions
def get_vehicle_premiums(make_name, sub_make_name, year):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(netpremium)::FLOAT
        FROM vehicle_inspection
        WHERE upper(make_name) = %s
        AND upper(sub_make_name) = %s
        AND model_year = %s
    """, (make_name.upper(), sub_make_name.upper(), year))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None
