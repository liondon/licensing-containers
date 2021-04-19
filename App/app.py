import os
import sys
import requests
import json
from flask import Flask, request, abort
import socket
import time
from datetime import datetime

hostIP = "0.0.0.0"
serverPort = 9090

# import environment variables
username = os.getenv("USERNAME", "tester")
password = os.getenv("PASSWORD", "testpwd")    
authsrvr_url = os.getenv("AUTH_SERVER", "http://localhost:5000")
container_id = socket.gethostname()

# create app
app = Flask(__name__)
# app.debug = True



######################################################################
#  L I C E N S I N G    r e l a t e d    f u n c t i o n s
######################################################################
def get_license():
    data = {
        "username": username,
        "password": password,
        "used_by": container_id
    }

    res = requests.post(authsrvr_url + '/licenses', json = data)
    lic = json.loads(res.text)
    return lic

def revoke_license(license_id):
    data = {
        "is_active": False,
        "revoked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    res = requests.patch(authsrvr_url + '/licenses/' + str(license_id), json = data)
    return res

def periodically_checkin(license_id):

    data = {
        "username":"tester",
        "used_by": container_id,
        "is_active": True,
        "key": license_id
    }

    res = requests.get(authsrvr_url + '/licenses/' + str(license_id), json = data)
    return res


######################################################################
#  E X A M P L E    C O N T A I N E R I Z E D    A P P
######################################################################
def fib(n):
    minusTwo = 0
    minusOne = 1
    for i in range(2, n + 1):
        answer = minusOne + minusTwo
        minusTwo = minusOne
        minusOne = answer
    return answer

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

# @app.route('/shutdown')
# def shutdown():
#     #do things
#     sys.exit()


######################################################################
#  R U N N I N G    T H E    F L A S K    A P P
######################################################################
if __name__ == "__main__":

    # activate a license
    lic = get_license()
    print("license", type(lic), lic)
    if not lic:
        sys.exit("Error: failed to get license.")

    # start the application
    app.run(host=hostIP, port=serverPort)

    # graceful exit

    # check_period = 5
    # start_time  = time.time()
    # # deal with non-graceful exit in addition of graceful exit
    while True:
        # current_time = time.time()
        # elapsed_time = current_time - start_time

        # if elapsed_time > check_period:
        #     need_check = True
        #     while need_check:
        #         res = periodically_checkin(lic["id"])
        #         if res.status_code == 200:
        #             need_check = False
        #             print("Finished checkin without issue!")

        #     start_time = time.time()

        res = revoke_license(lic["id"])
        if res.status_code == 200:
            sys.exit("Info: successfully revoked the license.")
        elif res.status_code >= 400 and res.status_code < 500:
            sys.exit("Error: failed to revoke the license due to client side error.")
        elif res.status_code >= 500:
            print("Error: server side error, try again.")
