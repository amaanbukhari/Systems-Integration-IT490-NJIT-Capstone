import json
import pika
import time

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

# Final response queues from BE-DB back to FE
REGISTER_RESPONSE_QUEUE = "auth.register.bedb_to_fe"
LOGIN_RESPONSE_QUEUE = "auth.login.bedb_to_fe"


def get_connection():
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    params = pika.ConnectionParameters(
        host=RMQ_HOST,
        port=RMQ_PORT,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30
    )
    return pika.BlockingConnection(params)


def wait_for_response(queue_name, correlation_id, timeout=10):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(
    queue=queue_name,
    durable=True,
    arguments={"x-queue-type": "quorum"}
)

    print(f"[FE Consumer] Waiting on queue: {queue_name}")
    print(f"[FE Consumer] Looking for correlation ID: {correlation_id}")

    start_time = time.time()

    while time.time() - start_time < timeout:
        method_frame, header_frame, body = channel.basic_get(
            queue=queue_name,
            auto_ack=True
        )

        if method_frame:
            print(f"[FE Consumer] Message received from queue: {queue_name}")
            print(f"[FE Consumer] Message correlation ID: {header_frame.correlation_id}")

            if header_frame.correlation_id == correlation_id:
                try:
                    decoded = json.loads(body.decode("utf-8"))
                    print(f"[FE Consumer] Matching response received: {decoded}")
                    connection.close()
                    return decoded
                except Exception:
                    connection.close()
                    return {
                        "status": "fail",
                        "message": "Invalid JSON response from backend"
                    }

        time.sleep(0.1)

    connection.close()

    print("[FE Consumer] Timeout waiting for response")
    return {
        "status": "fail",
        "message": "Backend timeout or no response received"
    }
