import os, requests
import grpc
from protos.login_pb2 import *
from protos.login_pb2_grpc import *

def token(request):

    token = str(request.cookies['x-access-token'])
    if not token:
        return None, ("missing credentials cookie", 401)
    
    try:
        with grpc.insecure_channel(os.environ.get('AUTH_SVC_ADDRESS')) as channel:
            stub = LoginStub(channel)
            response = stub.doValidate(ValidateRequest(token=token))
    except:
        raise Exception

    if response.status_code == 200:
        # response.text contains the body of the token regarding the request (claim)
        return response.text, response.username, None
    else:
        return None, None, (response.text, response.status_code)
    