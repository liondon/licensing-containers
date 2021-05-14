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
import secrets
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

hostIP = "0.0.0.0"
serverPort = 9090

# import environment variables
self_ip = os.getenv("CONTAINER_IP", "192.168.33.10")
username = os.getenv("USERNAME", "tester")
password = os.getenv("PASSWORD", "testpwd")    
authsrvr_url = os.getenv("AUTH_SERVER", "http://localhost:5000")
container_id = socket.gethostname()
max_checkin_failure = os.getenv("MAX_CHECKIN_FAILURE", 1)
failed_checkin_count = 0
message_bytes = b''

# create app
app = Flask(__name__)
# app.debug = True

# initialize scheduler for cron jobs
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# config logger
logging.basicConfig(format='%(asctime)s | [%(levelname)s] | %(message)s', datefmt='%m/%d/%Y | %I:%M:%S %p')
# app.logger.setLevel(logging.INFO)
app.logger.setLevel(logging.DEBUG)
# logging.getLogger('apscheduler').setLevel(logging.INFO)


######################################################################
#  U t i l i t y    f u n c t i o n s
######################################################################
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

def periodically_checkin(license_id, license_pub_key):
    global failed_checkin_count, max_checkin_failure, message_bytes

    # generate a random message
    message_bytes = secrets.token_bytes()
    app.logger.debug("message_bytes: {}".format(message_bytes))

    # encrypt the message
    pub_key_obj = serialization.load_pem_public_key(license_pub_key.encode('UTF-8','strict'))
    encrypted_message_bytes = pub_key_obj.encrypt(
        message_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    app.logger.debug("encrypted_message_bytes: {}".format(encrypted_message_bytes))

    data = {
        "used_by": container_id,
        "pub_key": license_pub_key,
        # send the encrypted_message as ascii string
        "encrypted_message": base64.b64encode(encrypted_message_bytes).decode('ascii','strict')
    }
    app.logger.debug("data['encrypted_message']: {}".format(data['encrypted_message']))

    with scheduler.app.app_context():
        while True:
            if failed_checkin_count > max_checkin_failure:
                shutdown_server("Error: failed checkin count exceed max_checkin_failure.")
                return

            try:
                res = requests.post(authsrvr_url + '/licenses/' + str(license_id) + '/checkin', json = data)

                if res.status_code == 200:

                    # convert the decrypted_message from ascii string to bytes
                    decrypted_message = res.text
                    app.logger.debug("decrypted_message: {}".format(decrypted_message))
                    decrypted_message_bytes = base64.b64decode(decrypted_message.encode('ascii', 'strict'))
                    app.logger.debug("decrypted_message_bytes: {}".format(decrypted_message_bytes))

                    if decrypted_message_bytes != message_bytes:
                        app.logger.error("Error: the message does not match!")
                        failed_checkin_count += 1
                        break

                    app.logger.info("successfully finished checkin without issue!")
                    failed_checkin_count = 0
                    break

                elif res.status_code >= 400 and res.status_code < 500:
                    app.logger.error("Error: checkin verification failed.")
                    failed_checkin_count += 1
                    break
                elif res.status_code >= 500:
                    app.logger.error("Error: server side error, try again.")
                    failed_checkin_count += 1
                    time.sleep(30)
            except:
                app.logger.error("Error: failed to POST /checkin")
                failed_checkin_count += 1
                break


######################################################################
#  E X A M P L E    C O N T A I N E R I Z E D    A P P
######################################################################
def fib(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
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
        start_time = time.time_ns()
        app.logger.info("{} | Got a request: {}".format(start_time, request.args.get("number")))
        n = int(request.args.get("number"))
    except:
        abort(400)

    answer = str(fib(n))
    end_time = time.time_ns()
    app.logger.info("{} | Returning Answer: {}".format(end_time, answer))
    app.logger.info("{} | Total time: {} nanoseconds".format(end_time, end_time - start_time))
    return "time consumed: {} | answer: {}\n".format(end_time - start_time, answer), 200

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
            args=[lic["id"], lic["pub_key"]],
            seconds=10, 
            max_instances=1,
            # misfire_grace_time=60,
        )

        # start the application
        app.run(host=hostIP, port=serverPort)

        # shutdown the scheduler after the flask app exits 
        scheduler.remove_all_jobs()
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
