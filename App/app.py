import os
import sys
import requests
import json
from flask import Flask, request, abort
import socket
import time

hostIP = "0.0.0.0"
serverPort = 9090

app = Flask(__name__)
#app.debug = True

@app.route("/")
def hello():
    return "<h1>Hello, This is a Fibonacci Server</h1>"

@app.route("/fibonacci", methods = ['GET'])
def fibonacci():
    try:
        print("Got a request: ", request.args.get("number"))
        n = int(request.args.get("number"))
    except:
        abort(400)
    return str(fib(n)), 200

def fib(n):
    minusTwo = 0
    minusOne = 1
    for i in range(2, n + 1):
        answer = minusOne + minusTwo
        minusTwo = minusOne
        minusOne = answer
    return answer

def get_license():
    username = os.getenv("USERNAME", "tester")
    password = os.getenv("PASSWORD", "testpwd")    
    authsrvr_url = os.getenv("AUTH_SERVER", "http://localhost:5000")
    container_id = socket.gethostname()

    data = {
        "username": username,
        "password": password,
        "used_by": container_id
    }

    res = requests.post(authsrvr_url + '/licenses', json = data)
    lic = json.loads(res.text)
    return lic

if __name__ == "__main__":
    # activate a license
    lic = get_license()
    print("license", type(lic), lic)
    if not lic:
        sys.exit("Error: you don't have available license.")

    app.run(host=hostIP, port=serverPort)

    # graceful exit
