import pika
import time

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "musicapp"
RMQ_PASS = "strongpassword"
QUEUE_NAME = "it490_test"


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RMQ_HOST,
            port=RMQ_PORT,
            credentials=pika.PlainCredentials(RMQ_USER, RMQ_PASS)
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    msg = f"Hello from RabbitMQ test {time.time()}"

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=msg,
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    print("Message sent:", msg)

    connection.close()


if __name__ == "__main__":
    main()
