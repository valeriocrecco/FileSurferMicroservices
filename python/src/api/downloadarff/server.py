import gridfs
from bson.objectid import ObjectId
from pymongo import MongoClient
from functools import wraps
import grpc
from protos.download_pb2 import *
from protos.download_pb2_grpc import *
from concurrent import futures

def download_arff(fid_string):

    #fid_string = str(request.files['fid'].read(), 'utf-8')
    client = MongoClient('mongodb://mongo:27017/')
    mongo_arff = client.arffs
    fs_arffs = gridfs.GridFS(mongo_arff)

    try:
        out = fs_arffs.get(ObjectId(fid_string))
    except Exception as err:
        return bytes('Error occurered while downloading', 'utf-8'), 401

    #return send_file(out, download_name=f"{fid_string}.arff"), 200
    return out.read(), 200

class Download(DownloadServicer):
    def doDownload(self, request, context):
        response = download_arff(request.fid)
        return DownloadReply(data=response[0], status_code=response[1])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_DownloadServicer_to_server(Download(), server)
    server.add_insecure_port('[::]:5001')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    #server.run(host="0.0.0.0", port=5001)
    serve()