import json
import pika

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"


def get_rmq_connection():
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    params = pika.ConnectionParameters(
        host=RMQ_HOST,
        port=RMQ_PORT,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30
    )
    return pika.BlockingConnection(params)


def send_db_response(queue_name, payload, correlation_id=None, reply_to=None):
    connection = get_rmq_connection()
    channel = connection.channel()

    target_queue = reply_to if reply_to else queue_name
    channel.queue_declare(queue=target_queue, durable=True, arguments={"x-queue-type":"quorum"})

    print("\n[DB Producer] Sending response")
    print("[DB Producer] Queue:", target_queue)
    print("[DB Producer] Correlation ID:", correlation_id)
    print("[DB Producer] Reply-To:", reply_to)
    print("[DB Producer] Payload:", payload)

    channel.basic_publish(
        exchange="",
        routing_key=target_queue,
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2,
            correlation_id=correlation_id,
            content_type="application/json"
        )
    )

    try:
        if connection and connection.is_open:
            connection.close()
    except Exception:
        pass
