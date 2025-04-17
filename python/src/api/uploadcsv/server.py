import gridfs, pika, json, tempfile
from pymongo import MongoClient
from concurrent import futures
import grpc
from protos.upload_pb2 import *
from protos.upload_pb2_grpc import *

def upload_csv(username, file):

    client = MongoClient('mongodb://mongo:27017/')
    mongo_csv = client.csvs

    fs_csv = gridfs.GridFS(mongo_csv)
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()

    # create empty temp file
    tf = tempfile.NamedTemporaryFile()
    tf.write(file)
    
    # write arff to the file
    f = open(tf.name, "rb")
    data = f.read()

    auth = username
    if not auth:
        return "missing credentials", 401

    try:
        fid = fs_csv.put(data)
        f.close()
    except Exception as err:
        print(err)
        return "internal server error csv", 502
    
    message = {
        "csv_fid": str(fid),
        "arff_fid": None,
        "username": username,
    }

    try:
        channel.basic_publish(
            exchange="",              # default exchange node
            routing_key="csv",
            body=json.dumps(message), # convert a python object to a JSON string
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE # allow to store messages in the queue in order to handle pods crash or restart
            ),
        )
    except Exception as err:
        # remove the uploaded file on MongoDB because there isn't a message in the regarding this file
        print(err)
        fs_csv.delete(fid)
        return "internal server error BB"+ username + str(fid), 503
    
    return "upload success", 200

class Upload(UploadServicer):
    def doUpload(self, request, context):
        response = upload_csv(request.username, request.data)
        return UploadReply(text=response[0], status_code=response[1])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_UploadServicer_to_server(Upload(), server)
    server.add_insecure_port('[::]:5002')
    server.start()
    server.wait_for_termination()    

if __name__ == "__main__":
    #server.run(host="0.0.0.0", port=5002)
    serve()