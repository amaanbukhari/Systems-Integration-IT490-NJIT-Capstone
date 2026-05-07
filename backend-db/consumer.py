import os, pika

HOST  = os.getenv("RMQ_HOST")
PORT  = int(os.getenv("RMQ_PORT", "5672"))
USER  = os.getenv("RMQ_USER")
PASS  = os.getenv("RMQ_PASS")
VHOST = os.getenv("RMQ_VHOST", "it490_test")
QUEUE = os.getenv("RMQ_REQUEST_QUEUE", "db_requests")

creds = pika.PlainCredentials(USER, PASS)
params = pika.ConnectionParameters(host=HOST, port=PORT, virtual_host=VHOST, credentials=creds)

conn = pika.BlockingConnection(params)
ch = conn.channel()
ch.queue_declare(queue=QUEUE, durable=True)

method, props, body = ch.basic_get(queue=QUEUE, auto_ack=True)

if body:
    print("Consumed:", body.decode())
else:
    print("No messages in queue. Run publisher.py on Backend-Frontend first.")

conn.close()
