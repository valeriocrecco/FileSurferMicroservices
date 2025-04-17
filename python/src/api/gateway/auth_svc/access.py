# module to contain login function
import os, requests
import grpc
from protos.login_pb2 import *
from protos.login_pb2_grpc import *
from flask import session

def login(request):
    
    if not (request.form['username'] and request.form['password']):
        return None, ("missing credentials in access.py", 401)
    
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        with grpc.insecure_channel(os.environ.get('AUTH_SVC_ADDRESS')) as channel:
            stub = LoginStub(channel)
            response = stub.doLogin(LoginRequest(username=username, password=password))
    except:
        raise Exception
    
    if response.status_code == 200:
        return response.token, None
    else:
        return None, (response.token, response.status_code)
    
