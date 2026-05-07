import pika

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "musicapp"
RMQ_PASS = "strongpassword"
QUEUE_NAME = "it490_test"


def callback(ch, method, properties, body):
    print("Received:", body.decode())


def main():
    credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RMQ_HOST,
            port=RMQ_PORT,
            credentials=credentials
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    print("Waiting for messages...")

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=True
    )

    channel.start_consuming()


if __name__ == "__main__":
    main()
