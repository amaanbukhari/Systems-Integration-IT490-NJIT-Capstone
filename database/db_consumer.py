import pika

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

DB_REGISTER_REQUEST_QUEUE = "auth.register.db.request"
DB_LOGIN_REQUEST_QUEUE = "auth.login.db.request"
DB_REGISTER_RESPONSE_QUEUE = "auth.register.db.response"
DB_LOGIN_RESPONSE_QUEUE = "auth.login.db.response"


def get_rmq_connection():
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    params = pika.ConnectionParameters(
        host=RMQ_HOST,
        port=RMQ_PORT,
        credentials=credentials,
        heartbeat=300,
        blocked_connection_timeout=150
    )
    return pika.BlockingConnection(params)


def start_db_consumer(register_callback, login_callback):
    connection = get_rmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=DB_REGISTER_REQUEST_QUEUE, durable=True, arguments={"x-queue-type":"quorum"})
    channel.queue_declare(queue=DB_LOGIN_REQUEST_QUEUE, durable=True, arguments={"x-queue-type":"quorum"})
    channel.queue_declare(queue=DB_REGISTER_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type":"quorum"})
    channel.queue_declare(queue=DB_LOGIN_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type":"quorum"})

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=DB_REGISTER_REQUEST_QUEUE,
        on_message_callback=register_callback
    )

    channel.basic_consume(
        queue=DB_LOGIN_REQUEST_QUEUE,
        on_message_callback=login_callback
    )

    print("[DB Consumer] Waiting for DB-stage auth requests...")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[DB Consumer] Shutting down...")
        try:
            channel.stop_consuming()
        except Exception:
            pass
    finally:
        try:
            if connection and connection.is_open:
                connection.close()
        except Exception:
            pass
