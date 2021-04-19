import os
import sys
import requests
import json
from flask import Flask, request, abort
from flask_apscheduler import APScheduler
import logging
import socket
import time
from datetime import datetime

hostIP = "0.0.0.0"
serverPort = 9090

# import environment variables
self_ip = os.getenv("CONTAINER_IP", "192.168.33.10")
username = os.getenv("USERNAME", "tester")
password = os.getenv("PASSWORD", "testpwd")    
authsrvr_url = os.getenv("AUTH_SERVER", "http://localhost:5000")
container_id = socket.gethostname()

# create app
app = Flask(__name__)
# app.debug = True

# initialize scheduler for cron jobs
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# config logger
logging.basicConfig()
app.logger.setLevel(logging.INFO)
# logging.getLogger('apscheduler').setLevel(logging.INFO)

def shutdown_server(msg=None):
    app.logger.info(msg)
    scheduler.remove_job('checkin')
    res = requests.get("http://{}:{}/shutdown".format(self_ip, serverPort))

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

def periodically_checkin(license_id, license_key):
    data = {
        "used_by": container_id,
        "key": license_key
    }

    with scheduler.app.app_context():
        while True:
            try:
                res = requests.post(authsrvr_url + '/licenses/' + str(license_id) + '/checkin', json = data)

                if res.status_code == 200:
                    app.logger.info("successfully finished checkin without issue!")
                    break
                elif res.status_code >= 400 and res.status_code < 500:
                    shutdown_server("Error: checkin verification failed.")
                    break
                elif res.status_code >= 500:
                    app.logger.error("server side error, try again.")
                    time.sleep(30)
            except:
                shutdown_server("Error: failed to POST /checkin")
                break


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
    return "<h1>Hello, This is a Fibonacci Server</h1>", 200

@app.route("/fibonacci", methods = ['GET'])
def fibonacci():
    try:
        app.logger.info("Got a request: ", request.args.get("number"))
        n = int(request.args.get("number"))
    except:
        abort(400)
    return str(fib(n)), 200

@app.route('/shutdown', methods = ['GET'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    app.logger.info("Info: shutting down the server...")
    func()
    return "successful shutdown", 200


######################################################################
#  R U N N I N G    T H E    F L A S K    A P P
######################################################################
if __name__ == "__main__":
    try:
        # activate a license
        lic = get_license()
        print("license", type(lic), lic)
        if not lic:
            sys.exit("Error: failed to get license.")

        # schedule periodical checkin cron job
        scheduler.add_job(
            func=periodically_checkin,
            id='checkin',
            trigger='interval', 
            args=[lic["id"], lic["key"]],
            seconds=10, 
            max_instances=1,
            # misfire_grace_time=60,
        )

        # start the application
        app.run(host=hostIP, port=serverPort)

        # shutdown the scheduler after the flask app exits 
        scheduler.remove_job('checkin')
        scheduler.shutdown()

        # graceful exit
        while True:
            res = revoke_license(lic["id"])
            print("Info: revoking license... res.status_code = {}".format(res.status_code))
            if res.status_code == 200:
                print("Info: successfully revoked the license.")
                break
            elif res.status_code >= 400 and res.status_code < 500:
                sys.exit("Error: failed to revoke the license due to client side error.")
            elif res.status_code >= 500:
                print("Error: server side error, try again.")
                time.sleep(30)

    except requests.exceptions.ConnectionError:
        sys.exit("Error: cannot connect to Authorizing Server")

    except SystemExit:
        raise

    except:
        print("Error: unexpected error occurred.", sys.exc_info()[0])
