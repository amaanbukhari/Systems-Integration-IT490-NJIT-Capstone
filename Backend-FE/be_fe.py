import json
import sys
import time
sys.stdout.reconfigure(line_buffering=True)
import pika

RMQ_HOSTS = [
    "100.114.37.13",  # RMQ1 - Daniel
    "100.65.228.57",  # RMQ2 - Amaan
    "100.94.40.126",  # RMQ3 - Meek
]
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

# FE -> BE-FE queues
REGISTER_REQUEST_QUEUE = "auth.register.fe_to_befe"
LOGIN_REQUEST_QUEUE = "auth.login.fe_to_befe"
FORGOT_PASSWORD_REQUEST_QUEUE = "auth.forgot_password.fe_to_befe"

# BE-FE -> BE-DB queues
DB_REGISTER_REQUEST_QUEUE = "auth.register.db.request"
DB_LOGIN_REQUEST_QUEUE = "auth.login.db.request"
DB_FORGOT_PASSWORD_REQUEST_QUEUE = "auth.forgot_password.db.request"

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

def forward_message(channel, queue_name, payload, reply_to, correlation_id):
    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2,
            reply_to=reply_to,
            correlation_id=correlation_id
        )
    )

def on_register_request(ch, method, props, body):
    print("\n[BE-FE] Register request received")
    print("[BE-FE] Correlation ID:", props.correlation_id)
    print("[BE-FE] Reply-To:", props.reply_to)
    print("[BE-FE] Body:", body.decode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
        if not data.get("username") or not data.get("password"):
            raise ValueError("Missing username or password")
        forward_message(ch, DB_REGISTER_REQUEST_QUEUE, data, props.reply_to, props.correlation_id)
        print("[BE-FE] Forwarded register request to DB stage")
    except Exception as e:
        print("[BE-FE] Error:", str(e))
    ch.basic_ack(delivery_tag=method.delivery_tag)

def on_login_request(ch, method, props, body):
    print("\n[BE-FE] Login request received")
    print("[BE-FE] Correlation ID:", props.correlation_id)
    print("[BE-FE] Reply-To:", props.reply_to)
    print("[BE-FE] Body:", body.decode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
        if not data.get("username") or not data.get("password"):
            raise ValueError("Missing username or password")
        forward_message(ch, DB_LOGIN_REQUEST_QUEUE, data, props.reply_to, props.correlation_id)
        print("[BE-FE] Forwarded login request to DB stage")
    except Exception as e:
        print("[BE-FE] Error:", str(e))
    ch.basic_ack(delivery_tag=method.delivery_tag)

def on_forgot_password_request(ch, method, props, body):
    print("\n[BE-FE] Forgot password request received")
    print("[BE-FE] Correlation ID:", props.correlation_id)
    print("[BE-FE] Reply-To:", props.reply_to)
    print("[BE-FE] Body:", body.decode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
        if not data.get("username") or not data.get("new_password"):
            raise ValueError("Missing username or new_password")
        forward_message(ch, DB_FORGOT_PASSWORD_REQUEST_QUEUE, data, props.reply_to, props.correlation_id)
        print("[BE-FE] Forwarded forgot password request to DB stage")
    except Exception as e:
        print("[BE-FE] Error:", str(e))
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    while True:
        connection = None
        try:
            connection = get_rmq_connection()
            channel = connection.channel()
            channel.queue_declare(queue=REGISTER_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
            channel.queue_declare(queue=LOGIN_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
            channel.queue_declare(queue=FORGOT_PASSWORD_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
            channel.queue_declare(queue=DB_REGISTER_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
            channel.queue_declare(queue=DB_LOGIN_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
            channel.queue_declare(queue=DB_FORGOT_PASSWORD_REQUEST_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=REGISTER_REQUEST_QUEUE, on_message_callback=on_register_request)
            channel.basic_consume(queue=LOGIN_REQUEST_QUEUE, on_message_callback=on_login_request)
            channel.basic_consume(queue=FORGOT_PASSWORD_REQUEST_QUEUE, on_message_callback=on_forgot_password_request)
            print("[BE-FE] Waiting for FE auth requests...")
            channel.start_consuming()
        except KeyboardInterrupt:
            print("\n[BE-FE] Shutting down...")
            break
        except Exception as e:
            print(f"[BE-FE] Connection lost or startup failed: {e}")
            print("[BE-FE] Retrying in 5 seconds...")
            time.sleep(5)
        finally:
            try:
                if connection and connection.is_open:
                    connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
