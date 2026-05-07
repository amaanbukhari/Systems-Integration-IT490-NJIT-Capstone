import json
import pika
import time
import sys

sys.stdout.reconfigure(line_buffering=True)

RMQ_HOSTS = [
    "100.65.228.57",  # RMQ2 - Amaan
    "100.94.40.126",  # RMQ3 - Meek
    "100.114.37.13",  # RMQ1 - Daniel
]

RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

#Queue for RabbitMQ for Getting Users
DM_GET_USERS_FE_TO_BEFE = "dm.get_users.fe_to_befe"
DM_GET_USERS_BEFE_TO_BEDB = "dm.get_users.befe_to_bedb"

#Queue for RabbitMQ for Getting Conversations
DM_GET_CONVERSATION_FE_TO_BEFE = "dm.get_conversation.fe_to_befe"
DM_GET_CONVERSATION_BEFE_TO_BEDB = "dm.get_conversation.befe_to_bedb"

#Queue for RabbitMQ for Sending Messages
DM_SEND_FE_TO_BEFE = "dm.send.fe_to_befe"
DM_SEND_BEFE_TO_BEDB = "dm.send.befe_to_bedb"

#Setting up the RMQ connection
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

            conn = pika.BlockingConnection(params)
            print(f"[BE-FE] Connected to {host}")
            return conn

        except Exception as e:
            print(f"[BE-FE] Failed {host}: {e}")
            continue

    raise Exception("Could not connect to any RabbitMQ node")
