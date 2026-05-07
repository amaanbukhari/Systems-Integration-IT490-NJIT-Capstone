import json
import pika
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

RMQ_HOST = "100.114.37.13"
RMQ_PORT = 5672
RMQ_USER = "music"
RMQ_PASS = "music123"

SEARCH_DB_REQUEST_QUEUE = "search.request.befe_to_db"
SEARCH_DB_RESPONSE_QUEUE = "search.response.db_to_bedb"


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


def search_itunes(query):
    encoded_query = quote(query)
    url = f"https://itunes.apple.com/search?term={encoded_query}&media=music&limit=50"

    with urlopen(url, timeout=10) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw)

    results = data.get("results", [])

    songs = []
    albums = []
    seen_album_keys = set()

    for item in results:
        wrapper_type = item.get("wrapperType", "")
        kind = item.get("kind", "")

        if wrapper_type == "track" and kind == "song":
            songs.append({
                "trackId": item.get("trackId"),
                "collectionId": item.get("collectionId"),
                "trackName": item.get("trackName", ""),
                "artistName": item.get("artistName", ""),
                "collectionName": item.get("collectionName", ""),
                "artworkUrl100": item.get("artworkUrl100", ""),
                "previewUrl": item.get("previewUrl", ""),
                "trackViewUrl": item.get("trackViewUrl", ""),
                "collectionViewUrl": item.get("collectionViewUrl", "")
            })

        elif wrapper_type == "collection":
            collection_id = item.get("collectionId")
            collection_name = item.get("collectionName", "")
            artist_name = item.get("artistName", "")

            album_key = (collection_id, collection_name, artist_name)
            if album_key in seen_album_keys:
                continue

            seen_album_keys.add(album_key)

            albums.append({
                "collectionId": collection_id,
                "collectionName": collection_name,
                "artistName": artist_name,
                "artworkUrl100": item.get("artworkUrl100", ""),
                "collectionViewUrl": item.get("collectionViewUrl", "")
            })

    return songs, albums


def on_search_db_request(ch, method, props, body):
    print("\n[DB Search] Search DB request received")
    print("[DB Search] Correlation ID:", props.correlation_id)
    print("[DB Search] Reply-To:", props.reply_to)

    try:
        data = json.loads(body.decode("utf-8"))
        print("[DB Search] Body:", data)

        query = str(data.get("query", "")).strip()

        if not query:
            payload = {
                "action": "search",
                "query": "",
                "songs": [],
                "albums": [],
                "message": "Missing search query"
            }
        else:
            songs, albums = search_itunes(query)

            print("[DB Search] Query:", query)
            print("[DB Search] Songs found:", len(songs))
            print("[DB Search] Albums found:", len(albums))

            payload = {
                "action": "search",
                "query": query,
                "songs": songs,
                "albums": albums,
                "message": "Search completed successfully"
            }

        publish_message(
            ch,
            SEARCH_DB_RESPONSE_QUEUE,
            payload,
            props.reply_to,
            props.correlation_id
        )

        print("[DB Search] Sent search response to BE-DB stage")

    except HTTPError as exc:
        payload = {
            "action": "search",
            "query": "",
            "songs": [],
            "albums": [],
            "message": f"iTunes HTTP error: {exc.code}"
        }

        publish_message(
            ch,
            SEARCH_DB_RESPONSE_QUEUE,
            payload,
            props.reply_to,
            props.correlation_id
        )

        print("[DB Search] iTunes HTTP error:", exc)

    except URLError as exc:
        payload = {
            "action": "search",
            "query": "",
            "songs": [],
            "albums": [],
            "message": f"iTunes URL error: {str(exc)}"
        }

        publish_message(
            ch,
            SEARCH_DB_RESPONSE_QUEUE,
            payload,
            props.reply_to,
            props.correlation_id
        )

        print("[DB Search] iTunes URL error:", exc)

    except Exception as exc:
        payload = {
            "action": "search",
            "query": "",
            "songs": [],
            "albums": [],
            "message": f"Search failed: {str(exc)}"
        }

        publish_message(
            ch,
            SEARCH_DB_RESPONSE_QUEUE,
            payload,
            props.reply_to,
            props.correlation_id
        )

        print("[DB Search] General error:", exc)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = get_rmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=SEARCH_DB_REQUEST_QUEUE, durable=True, arguments={"x-queue-type":"quorum"})
    channel.queue_declare(queue=SEARCH_DB_RESPONSE_QUEUE, durable=True, arguments={"x-queue-type":"quorum"})

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=SEARCH_DB_REQUEST_QUEUE,
        on_message_callback=on_search_db_request
    )

    print("[DB Search] Waiting for DB-stage search requests...")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[DB Search] Shutting down...")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
