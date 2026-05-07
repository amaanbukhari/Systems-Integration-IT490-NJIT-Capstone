import sys
sys.stdout.reconfigure(line_buffering=True)

import json
import pika

RMQ_HOSTS = [
    "100.114.37.13",  # RMQ1 - Daniel
    "100.65.228.57",  # RMQ2 - Amaan
    "100.94.40.126",  # RMQ3 - Meek
]
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

DB_REGISTER_RESPONSE_QUEUE = "auth.register.db.response"
DB_LOGIN_RESPONSE_QUEUE = "auth.login.db.response"
DB_FORGOT_PASSWORD_RESPONSE_QUEUE = "auth.forgot_password.db.response"


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

def publish_final_response(channel, reply_to, payload, correlation_id):
    channel.basic_publish(
        exchange="",
        routing_key=reply_to,
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2,
            correlation_id=correlation_id,
            content_type="application/json"
        )
    )


def on_register_db_response(ch, method, props, body):
    print("\n[BE-DB] Register DB response received")
    print("[BE-DB] Correlation ID:", props.correlation_id)
    print("[BE-DB] Reply-To:", props.reply_to)

    data = json.loads(body.decode())
    response = {
        "stage": "be_db",
        "status": data.get("status"),
        "message": data.get("message"),
        "username": data.get("username")
    }

    publish_final_response(ch, props.reply_to, response, props.correlation_id)
    print("[BE-DB] Final register response sent to FE")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def on_login_db_response(ch, method, props, body):
    print("\n[BE-DB] Login DB response received")
    print("[BE-DB] Correlation ID:", props.correlation_id)
    print("[BE-DB] Reply-To:", props.reply_to)

    data = json.loads(body.decode())
    response = {
        "stage": "be_db",
        "status": data.get("status"),
        "message": data.get("message"),
        "user_id": data.get("user_id"),
        "username": data.get("username"),
        "session_id": data.get("session_id")
    }

    publish_final_response(ch, props.reply_to, response, props.correlation_id)
    print("[BE-DB] Final login response sent to FE")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def on_forgot_password_db_response(ch, method, props, body):
    print("\n[BE-DB] Forgot password DB response received")
    print("[BE-DB] Correlation ID:", props.correlation_id)
    print("[BE-DB] Reply-To:", props.reply_to)

    data = json.loads(body.decode())
    response = {
        "stage": "be_db",
        "status": data.get("status"),
        "message": data.get("message"),
        "username": data.get("username")
    }

    publish_final_response(ch, props.reply_to, response, props.correlation_id)
    print("[BE-DB] Final forgot password response sent to FE")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = None

    try:
        connection = get_rmq_connection()
        channel = connection.channel()

        channel.queue_declare(queue=DB_REGISTER_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_LOGIN_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_declare(queue=DB_FORGOT_PASSWORD_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})

        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(
            queue=DB_REGISTER_RESPONSE_QUEUE,
            on_message_callback=on_register_db_response
        )
        channel.basic_consume(
            queue=DB_LOGIN_RESPONSE_QUEUE,
            on_message_callback=on_login_db_response
        )
        channel.basic_consume(
            queue=DB_FORGOT_PASSWORD_RESPONSE_QUEUE,
            on_message_callback=on_forgot_password_db_response
        )

        print("[BE-DB] Waiting for DB-stage auth responses...")
        channel.start_consuming()

    except KeyboardInterrupt:
        print("\n[BE-DB] Shutting down...")
    except Exception as e:
        print(f"[BE-DB] Fatal error: {e}")
    finally:
        try:
            if connection and connection.is_open:
                connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
