import os, gridfs, jwt, datetime
import grpc
from flask import Flask, request, send_file, session, render_template, make_response, url_for, flash
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from register import addUser
from io import BytesIO
from functools import wraps
import grpc
from protos.upload_pb2 import *
from protos.upload_pb2_grpc import *
from protos.download_pb2 import *
from protos.download_pb2_grpc import *

server = Flask(__name__)
server.config['SECRET_KEY'] = 'sarcasm'

mongo_csv = PyMongo(server, uri="mongodb://mongo:27017/csvs")
mongo_arff = PyMongo(server, uri="mongodb://mongo:27017/arffs")

fs_csv = gridfs.GridFS(mongo_csv.db)
fs_arffs = gridfs.GridFS(mongo_arff.db)


@server.context_processor 
def inject_dict_for_all_templates():
    # Build the Navigation Bar
    nav = [
        {"text": "Login", "url": url_for('login')},
        {"text": "Register", "url": url_for('register')},
        {"text": "Converter", "url": url_for('upload_csv')},
        {"text": "Download", "url": url_for('download_arff')},
    ]
    
    return dict(navbar = nav)


@server.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'logged in currently'


def token_required(f):    
    @wraps(f)    
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.cookies:
            token = request.cookies['x-access-token']
        else:
            flash("Token is missing, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp
        try:
            data = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.DecodeError:
            flash("Token is missing, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp

        except jwt.exceptions.ExpiredSignatureError:
            flash("Token has expired, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp

        return f(*args, **kwargs)
    return decorated


@server.route("/login", methods=["POST"])
def login():

    if 'x-access-token' in request.cookies:
        token = request.cookies['x-access-token']
        try:
            data = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])
            flash("You're already logged in!")
            return render_template('upload.html')
        except jwt.DecodeError:
            flash("Token is missing, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp
        except jwt.exceptions.ExpiredSignatureError:
            flash("Token has expired, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp
    else:
        pass

    token, err = access.login(request)
    
    if not err:
        resp = make_response(render_template('upload.html'), 200)
        resp.set_cookie('x-access-token', token, expires=datetime.datetime.utcnow() + datetime.timedelta(minutes=5))
        return resp
    else:
        flash("Invalid credentials, please try again...")
        resp = make_response(render_template('login.html'), 401)
        return resp
    

@server.route("/login", methods=["GET"])
def login_get():
    resp = make_response(render_template('login.html'), 200)
    return resp


@server.route("/logout", methods=["GET"])
def logout():
    resp = make_response(render_template('login.html'), 200)
    resp.delete_cookie('x-access-token')
    return resp


@server.route("/register", methods=["POST"])
def register():
    
    if 'x-access-token' in request.cookies:
        token = request.cookies['x-access-token']
        try:
            data = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])
            flash("You're already logged in!")
            return render_template('upload.html')
        except jwt.DecodeError:
            flash("Token is missing, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp
        except jwt.exceptions.ExpiredSignatureError:
            flash("Token has expired, please log in!")
            resp = make_response(render_template('login.html'), 401)
            return resp
    else:
        pass
    
    res, err = addUser.register(request)

    if not err:
        resp = make_response(render_template('login.html'), 200)
        return resp
    else:
        flash("Inserted fields are invalid, please try again...")
        resp = make_response(render_template('login.html'), 401)
        return resp
    

@server.route("/register", methods=["GET"])
def register_get():
    resp = make_response(render_template('register.html'), 200)
    return resp


@server.route("/upload_csv", methods=["GET"])
@token_required
def upload_get():
    access, username, err = validate.token(request)
    resp = make_response(render_template('upload.html'), 200)
    return resp
   

@server.route("/upload_csv", methods=["POST"])
@token_required
def upload_csv():
    access, username, err = validate.token(request)

    if err:
        flash("Invalid token, please log in again!")
        resp = make_response(render_template('login.html'), 400)
        return resp

    if access=="True":
        # upload just 1 file per time
        if len(request.files) > 1 or len(request.files) < 1:
            flash("You should upload just 1 file per time, please try to upload again!")
            resp = make_response(render_template('upload.html'), 400)
            return resp
            
        if(request.files['file-upload-csv'].filename == ''):
            flash("Please click the right button!")
            resp = make_response(render_template('upload.html'), 400)
            return resp
       
        for _, file in request.files.items():
        
            try:
                with grpc.insecure_channel(os.environ.get('UPLOAD_SVC_ADDRESS')) as channel:
                    stub = UploadStub(channel)
                    response = stub.doUpload(UploadRequest(username=username, data=file.read()))
            except:
                raise Exception
            
        if response.status_code == 200:
            resp = make_response(render_template('download.html'), 200)
            return resp
        else:
            flash("An error occurred during upload, please try to upload again!" + response.text)
            resp = make_response(render_template('upload.html'), 400)
            return resp
    else:
        return "not authorized", 401


@server.route("/download_arff", methods=["GET"])
@token_required
def download_arff():
    access, username, err = validate.token(request)

    if err:
        flash("Invalid token, please log in again!")
        resp = make_response(render_template('login.html'), 400)
        return resp

    if access == "True":
        fid_string = request.args.get("fidARFF")

        if not fid_string:
            flash("Please enter the id, check your email inbox!")
            resp = make_response(render_template('download.html'), 200)
            return resp

        try:
            with grpc.insecure_channel(os.environ.get('DOWNLOAD_SVC_ADDRESS')) as channel:
                stub = DownloadStub(channel)
                response = stub.doDownload(DownloadRequest(fid=fid_string))
        except:
            raise Exception

        if (response.status_code != 200):
            flash("An error occured during download, please try to download again...")
            resp = make_response(render_template('download.html'), 500)
            return resp
        else:
            return send_file(BytesIO(response.data), download_name=f"{fid_string}.arff", as_attachment=True), 200
            
    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)