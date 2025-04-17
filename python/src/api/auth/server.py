import jwt, datetime, os
from concurrent import futures
import grpc, logging
import mysql.connector
from protos.login_pb2 import *
from protos.login_pb2_grpc import *

def connect_mysql():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("MYSQL_HOST"),
            user=os.environ.get("MYSQL_USER"),
            password=os.environ.get("MYSQL_PASSWORD"),
            database=os.environ.get("MYSQL_DB"),
            port=os.environ.get("MYSQL_PORT")
        )
        return connection
    except:
        return False

def login(username, password):
    if not (username and password):
        return "missing credentials aa", 401

    connection=connect_mysql()

    if (connection == False):
        return "error in getting mysql connection", 500
    
    cur = connection.cursor()
    if not cur:
        return "error in getting cur connection", 500
    
    logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.WARNING)
    logging.warning("INFOS: " + username + password)
    
    cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (username,)
    )

    res = cur.fetchall()

    if cur.rowcount > 0:
        email = res[0][0]
        pswd = res[0][1]
        
        if username != email or password != pswd:
            logging.warning("INFOS (2): " + username + password)
            return "invalid credentials auth/server.py/login()", 401
        else:
            logging.warning("INFOS (3): " + username + password)
            return createJWT(username, os.environ.get("JWT_SECRET"), True), 200
    else:
        return "invalid credentials auth/server.py/login() 2", 401
    
    
def register(username, password):
    if not (username and password):
        return "missing credentials auth/register", 401
    
    connection=connect_mysql()
    if not connection:
        return "error in getting mysql connection", 500
    
    cur = connection.cursor()
    if not cur:
        return "error in getting cur connection", 500
    
    logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.WARNING)
    logging.warning("INFOS: " + username + password)
    
    try:
        cur.execute(
            "INSERT INTO user (email, password) VALUES (%s, %s)", (username, password,)
        )
        connection.commit()
    except:
        return "user already exists!", 500
    
    if(cur.rowcount == 1):
        cur.close()
        return "user added successfully", 200
    else:
        cur.close()
        return "[server.py/register] invalid credentials: " + username, 401


def validate(token):
    
    encoded_jwt = token
    
    if not encoded_jwt:
        return "missing credentials", 401
    try:
        decoded = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"]
        )
    except:
        return "not authorized", 403
    
    #access = json.loads(decoded)
    if decoded['admin']:
        return "True", decoded['username'], 200
    else:
        return "False", 401



def createJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )

class Login(LoginServicer):

    def doLogin(self, request, context):
        print("INFO: " + request.username + request.password)
        response = login(request.username, request.password)
        return LoginReply(token=response[0], status_code=response[1])

    def doRegistration(self, request, context):
        response = register(request.username, request.password)
        return RegistrationReply(text=response[0], status_code=response[1])
    
    def doValidate(self, request, context):
        response = validate(request.token)
        return ValidateReply(text=response[0], username=response[1], status_code=response[2])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    add_LoginServicer_to_server(Login(), server)
    server.add_insecure_port('[::]:5000')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    #server.run(host="0.0.0.0", port=5000)
    logging.basicConfig()
    serve()
