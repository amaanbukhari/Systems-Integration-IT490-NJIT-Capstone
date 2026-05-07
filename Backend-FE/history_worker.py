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

# FE -> Be-Fe to connect to the queues
HISTORY_ADD_FE_QUEUE = "history.add.fe_to_befe"
HISTORY_GET_FE_QUEUE = "history.get.fe_to_befe"
HISTORY_CLEAR_FE_QUEUE = "history.clear.fe_to_befe"

# Be-Fe -> Be-DB to connect to the queues
HISTORY_ADD_DB_QUEUE = "history.add.befe_to_bedb"
HISTORY_GET_DB_QUEUE = "history.get.befe_to_bedb"
HISTORY_CLEAR_DB_QUEUE = "history.clear.befe_to_bedb"

def get_connection():
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

def declare_queue(channel, queue_name):
    channel.queue_declare(
        queue=queue_name,
        durable=True,
        arguments={"x-queue-type": "quorum"}
    )

