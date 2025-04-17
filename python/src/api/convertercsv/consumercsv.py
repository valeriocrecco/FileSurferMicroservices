import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_arff


def main():
    # client give us access to the db
    client = MongoClient("mongo", 27017)
    db_csvs = client.csvs
    db_arffs = client.arffs
    # gridfs
    fs_csvs = gridfs.GridFS(db_csvs)
    fs_arffs = gridfs.GridFS(db_arffs)

    # rabbitmq connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    # function to be executed when a message is taken from the video queue
    def callback(ch, method, properties, body):
        err = to_arff.start(body, fs_csvs, fs_arffs, ch)
        if err:
            # if err -> message must remain into the queue
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # function to consume message from the video queue
    channel.basic_consume(
        queue=os.environ.get("CSV_QUEUE"), on_message_callback=callback
    )

    print("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # pressed CTRL+C
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)