import os
import requests
import json
from flask import Flask, request, abort
import socket
import time
from datetime import datetime


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


@app.route('/shutdown')
def shutdown():
    #do things
    sys.exit()

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


def revoke_license(license_id):
    username = os.getenv("USERNAME", "tester")
    password = os.getenv("PASSWORD", "testpwd")    
    authsrvr_url = os.getenv("AUTH_SERVER", "http://localhost:5000")
    container_id = socket.gethostname()

    data = {
        "is_active": False,
        "revoked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    res = requests.patch(authsrvr_url + '/licenses/' + str(license_id), json = data)
    return res


def periodically_checkin(license_id):
    username = os.getenv("USERNAME", "tester")
    password = os.getenv("PASSWORD", "testpwd")    
    authsrvr_url = os.getenv("AUTH_SERVER", "http://localhost:5000")
    container_id = socket.gethostname()

    data = {
        "username":"tester",
        "used_by": container_id,
        "is_active": True,
        "key": license_id
    }

    res = requests.get(authsrvr_url + '/licenses/' + str(license_id), json = data)
    return res


if __name__ == "__main__":
    # activate a license
    lic = get_license()
    print("license", lic)

    app.run(host=hostIP, port=serverPort)

    check_period = 5
    start_time  = time.time()


    # deal with non-graceful exit in addition of graceful exit
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time

        if elapsed_time > check_period:
            need_check = True
            while need_check:
                res = periodically_checkin(lic["id"])
                if res.status_code == 200:
                    need_check = False
                    print("Finished checkin without issue!")

            start_time = time.time()

        
        res = revoke_license(lic["id"])
        if res.status_code == 200:
            sys.exit("Info: successfully revoked the license.")
        
