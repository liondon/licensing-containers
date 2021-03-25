import os
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
    url = os.getenv("AUTH_SERVER", "http://172.17.0.1:5000")
    container_id = socket.gethostname()
    print(container_id)
    data = {
        "username": "tester",
        "used_by": container_id,
        "is_active": True, 
        "key": "",
    }

    res = requests.post(url + '/licenses', json = data)
    res = json.loads(res.text)
    print("res", res)
    return res["key"]

if __name__ == "__main__":
    # activate a license
    lic = get_license()
    print("license", lic)

    app.run(host=hostIP, port=serverPort)

    # graceful exit
