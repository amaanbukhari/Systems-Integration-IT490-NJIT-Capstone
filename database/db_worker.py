import sys
sys.stdout.reconfigure(line_buffering=True)
import json
import mysql.connector
from mysql.connector import Error

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

import pika

# =========================
# RabbitMQ Configuration
# =========================
RMQ_HOSTS = [
    "100.114.37.13",  # RMQ1 - Daniel
    "100.65.228.57",  # RMQ2 - Amaan
    "100.94.40.126",  # RMQ3 - Meek
]
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

DB_REGISTER_REQUEST_QUEUE = "auth.register.db.request"
DB_LOGIN_REQUEST_QUEUE = "auth.login.db.request"
DB_FORGOT_PASSWORD_REQUEST_QUEUE = "auth.forgot_password.db.request"

DB_REGISTER_RESPONSE_QUEUE = "auth.register.db.response"
DB_LOGIN_RESPONSE_QUEUE = "auth.login.db.response"
DB_FORGOT_PASSWORD_RESPONSE_QUEUE = "auth.forgot_password.db.response"

# =========================
# MySQL Configuration
# =========================
DB_ROUTER_HOSTS = [
    ("100.78.226.13", 6446),  # Router on Dariel's VM
    ("100.64.56.116", 6446),  # Router on Amaan's VM
    ("100.124.122.18", 6446), # Router on Meek's VM
]
DB_USER = "music"
DB_PASS = "changeme"
DB_NAME = "this_is_music"

ph = PasswordHasher()


def get_rmq_connection():
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    for host in RMQ_HOSTS:
        try:
            params = pika.ConnectionParameters(
                host=host,
                port=RMQ_PORT,
                credentials=credentials,
                heartbeat=300,
                blocked_connection_timeout=150,
                connection_attempts=3,
                retry_delay=2
            )
            return pika.BlockingConnection(params)
        except Exception:
            continue
    raise Exception("Could not connect to any RabbitMQ node")


def get_db_connection():
    for host, port in DB_ROUTER_HOSTS:
        try:
            return mysql.connector.connect(
                host=host,
                port=port,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME
            )
        except Exception:
            continue
    raise Exception("Could not connect to any MySQL Router")


def publish_response(ch, target_queue, payload, correlation_id=None, reply_to=None):
    ch.basic_publish(
        exchange="",
        routing_key=target_queue,
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2,
            correlation_id=correlation_id,
            reply_to=reply_to,
            content_type="application/json"
        )
    )


def close_db(cursor=None, conn=None):
    try:
        if cursor is not None:
            cursor.close()
    except Exception:
        pass
    try:
        if conn is not None and conn.is_connected():
            conn.close()
    except Exception:
        pass


def hash_password(password):
    return ph.hash(password)


def verify_password(password, hashed):
    try:
        ph.verify(hashed, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

# =========================
# DB Logic
# =========================

def handle_register(data):
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()

    if not username or not password or not email:
        return {"status": "fail", "message": "Missing username, email, or password"}

    password_hash = hash_password(password)
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        existing = cursor.fetchone()
        if existing:
            return {"status": "fail", "message": "Username or email already exists"}
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        conn.commit()
        return {
            "status": "success",
            "message": f"User '{username}' registered successfully",
            "username": username
        }
    except Error as e:
        return {"status": "fail", "message": f"Database error during registration: {str(e)}"}
    finally:
        close_db(cursor, conn)


def handle_login(data):
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    ip_address = data.get("ip_address", "unknown").strip()
    user_agent = data.get("user_agent", "unknown").strip()

    if not username or not password:
        return {"status": "fail", "message": "Missing username or password"}

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return {"status": "fail", "message": "Invalid username or password"}

        user_id, db_username, stored_hash = row
        if not verify_password(password, stored_hash):
            return {"status": "fail", "message": "Invalid username or password"}

        cursor.execute(
            "INSERT INTO login_history (user_id, ip_address) VALUES (%s, %s)",
            (user_id, ip_address)
        )
        cursor.execute(
            "INSERT INTO login_sessions (user_id, ip_address, user_agent) VALUES (%s, %s, %s)",
            (user_id, ip_address, user_agent)
        )
        session_id = cursor.lastrowid
        conn.commit()

        return {
            "status": "success",
            "message": "Login successful",
            "user_id": user_id,
            "username": db_username,
            "session_id": session_id
        }
    except Error as e:
        return {"status": "fail", "message": f"Database error during login: {str(e)}"}
    finally:
        close_db(cursor, conn)


def handle_forgot_password(data):
    username = data.get("username", "").strip()
    new_password = data.get("new_password", "").strip()

    if not username or not new_password:
        return {"status": "fail", "message": "Missing username or new_password"}

    new_hash = hash_password(new_password)
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return {"status": "fail", "message": "Username not found"}
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE username = %s",
            (new_hash, username)
        )
        conn.commit()
        return {"status": "success", "message": "Password updated successfully", "username": username}
    except Error as e:
        return {"status": "fail", "message": f"Database error during password reset: {str(e)}"}
    finally:
        close_db(cursor, conn)

# =========================
# RMQ Consumers
# =========================

def on_register_request(ch, method, props, body):
    print("\n[DB Worker] Register DB request received")
    print("[DB Worker] Correlation ID:", props.correlation_id)
    print("[DB Worker] Reply-To:", props.reply_to)
    print("[DB Worker] Body:", body.decode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
        response = handle_register(data)
    except Exception as e:
        response = {"status": "fail", "message": f"DB register error: {str(e)}"}
    print("[DB Worker] Sending register DB response:", response)
    publish_response(ch, DB_REGISTER_RESPONSE_QUEUE, response, correlation_id=props.correlation_id, reply_to=props.reply_to)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def on_login_request(ch, method, props, body):
    print("\n[DB Worker] Login DB request received")
    print("[DB Worker] Correlation ID:", props.correlation_id)
    print("[DB Worker] Reply-To:", props.reply_to)
    print("[DB Worker] Body:", body.decode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
        response = handle_login(data)
    except Exception as e:
        response = {"status": "fail", "message": f"DB login error: {str(e)}"}
    print("[DB Worker] Sending login DB response:", response)
    publish_response(ch, DB_LOGIN_RESPONSE_QUEUE, response, correlation_id=props.correlation_id, reply_to=props.reply_to)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def on_forgot_password_request(ch, method, props, body):
    print("\n[DB Worker] Forgot password DB request received")
    print("[DB Worker] Correlation ID:", props.correlation_id)
    print("[DB Worker] Reply-To:", props.reply_to)
    print("[DB Worker] Body:", body.decode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
        response = handle_forgot_password(data)
    except Exception as e:
        response = {"status": "fail", "message": f"DB forgot_password error: {str(e)}"}
    print("[DB Worker] Sending forgot password DB response:", response)
    publish_response(ch, DB_FORGOT_PASSWORD_RESPONSE_QUEUE, response, correlation_id=props.correlation_id, reply_to=props.reply_to)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = None
    try:
        connection = get_rmq_connection()
        channel = connection.channel()

        channel.queue_declare(queue=DB_REGISTER_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_LOGIN_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_FORGOT_PASSWORD_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_REGISTER_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_LOGIN_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_FORGOT_PASSWORD_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=DB_REGISTER_REQUEST_QUEUE, on_message_callback=on_register_request)
        channel.basic_consume(queue=DB_LOGIN_REQUEST_QUEUE, on_message_callback=on_login_request)
        channel.basic_consume(queue=DB_FORGOT_PASSWORD_REQUEST_QUEUE, on_message_callback=on_forgot_password_request)

        print("[DB Worker] Waiting for DB-stage auth requests...")
        channel.start_consuming()

    except KeyboardInterrupt:
        print("\n[DB Worker] Shutting down...")
    except Exception as e:
        print(f"[DB Worker] Fatal error: {e}")
    finally:
        try:
            if connection and connection.is_open:
                connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

