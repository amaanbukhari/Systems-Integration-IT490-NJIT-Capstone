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

#Discussion creation QUEUE for RMQ for discussion feature
DISCUSSION_CREATE_POST_FE_TO_BEFE = "discussion.create_post.fe_to_befe"
DISCUSSION_CREATE_POST_BEFE_TO_BEDB = "discussion.create_post.befe_to_bedb"

#Discussion GET QUEUE for RMQ for discussion feature
DISCUSSION_GET_POSTS_FE_TO_BEFE = "discussion.get_posts.fe_to_befe"
DISCUSSION_GET_POSTS_BEFE_TO_BEDB = "discussion.get_posts.befe_to_bedb"

#Discussion REPLY QUEUE for RMQ for discussion feature
DISCUSSION_CREATE_REPLY_FE_TO_BEFE = "discussion.create_reply.fe_to_befe"
DISCUSSION_CREATE_REPLY_BEFE_TO_BEDB = "discussion.create_reply.befe_to_bedb"

# general connection setup for RMQ nodes
def get_connection():
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    for host in RMQ_HOSTS:
        try:
            params = pika.ConnectionParameters(
                host=host,
                port=RMQ_PORT,
                credentials=credentials,
                connection_attempts=1,
                retry_delay=0
            )
            return pika.BlockingConnection(params)
        except Exception:
            continue
    raise Exception("Could not connect to any RabbitMQ node")

def main():
    connection = get_connection()
    channel = connection.channel()

    queues = [
        DISCUSSION_CREATE_POST_FE_TO_BEFE,
        DISCUSSION_CREATE_POST_BEFE_TO_BEDB,
        DISCUSSION_GET_POSTS_FE_TO_BEFE,
        DISCUSSION_GET_POSTS_BEFE_TO_BEDB,
        DISCUSSION_CREATE_REPLY_FE_TO_BEFE,
        DISCUSSION_CREATE_REPLY_BEFE_TO_BEDB
    ]

    for q in queues:
        channel.queue_declare(
            queue=q,
            durable=True,
            arguments={"x-queue-type": "quorum"}
        )
