import json
import pika
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

SEARCH_REQUEST_QUEUE = "search.request.fe_to_befe"
SEARCH_DB_REQUEST_QUEUE = "search.request.befe_to_db"

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

def publish_message(channel, queue_name, payload, reply_to, correlation_id):
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

def search_itunes(term):
    encoded_term = quote(term)
    songs_url = (
        f"https://itunes.apple.com/search?"
        f"term={encoded_term}&media=music&entity=song&limit=25"
    )
    albums_url = (
        f"https://itunes.apple.com/search?"
        f"term={encoded_term}&media=music&entity=album&limit=12"
    )
    with urlopen(songs_url, timeout=10) as response:
        songs_raw = response.read().decode("utf-8")
        songs_data = json.loads(songs_raw)
    with urlopen(albums_url, timeout=10) as response:
        albums_raw = response.read().decode("utf-8")
        albums_data = json.loads(albums_raw)
    return {
        "songs": songs_data.get("results", []),
        "albums": albums_data.get("results", [])
    }

def on_search_request(ch, method, props, body):
    print("\n[BE-FE Search] Search request received")
    print("[BE-FE Search] Correlation ID:", props.correlation_id)
    print("[BE-FE Search] Reply-To:", props.reply_to)
    try:
        data = json.loads(body.decode("utf-8"))
        query = data.get("query", "").strip()
        username = data.get("username", "").strip()
        if not query:
            raise ValueError("Missing search query")
        results = search_itunes(query)
        payload = {
            "action": "search",
            "query": query,
            "username": username,
            "songs": results.get("songs", []),
            "albums": results.get("albums", [])
        }
        publish_message(
            ch,
            SEARCH_DB_REQUEST_QUEUE,
            payload,
            props.reply_to,
            props.correlation_id
        )
        print("[BE-FE Search] Forwarded search payload to DB stage")
        print("[BE-FE Search] Songs found:", len(payload["songs"]))
        print("[BE-FE Search] Albums found:", len(payload["albums"]))

    except (URLError, HTTPError, json.JSONDecodeError, Exception) as exc:
        payload = {
            "action": "search",
            "query": "",
            "songs": [],
            "albums": [],
            "message": f"Search failed: {str(exc)}"
        }
        publish_message(
            ch,
            SEARCH_DB_REQUEST_QUEUE,
            payload,
            props.reply_to,
            props.correlation_id
        )
        print("[BE-FE Search] Error:", exc)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = get_rmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=SEARCH_REQUEST_QUEUE, durable=True)
    channel.queue_declare(queue=SEARCH_DB_REQUEST_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=SEARCH_REQUEST_QUEUE,
        on_message_callback=on_search_request
    )
    print("[BE-FE Search] Waiting for search requests...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[BE-FE Search] Shutting down...")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
