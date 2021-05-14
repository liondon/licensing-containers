# Licensing System for Containerized Application

We implemented all the defense mechanisms described in our final report, except for the obfuscation and compilation. 

## Getting Started

### Prerequisites

```
virtualbox + vagrant
```
OR
```
docker
```

### Installing

1. (optional) Spin up and access the VM. (NOTE: when you spin up the VM for the first time, it might not finish all the provisioning process, just provision it again.)

    ```sh
    $ vagrant up
    $ vagrant ssh
    
    # provision the VM again if needed.
    $ vagrant up --provision
    ```

    **NOTE: the project root directory is synced with `/vagrant` in the VM**

2. Test docker installation.

    ```sh
    docker run hello-world
    ```

3. Spin up the Authorizing Server with docker-compose. **(NOTE: remove the volume if the data schema has been modified, otherwise the table will not be updated.)**

    ```sh
    # remove the volume for database if data schema is updated
    docker volume remove authsrvr_psql_data

    cd /vagrant/AuthSrvr
    docker-compose up
    ```

4. Test the endpoints with POSTMAN or curl from your host machine (NOTE: replace `localhost` with `192.168.33.10` if you're using the vagrant VM.)

    ```sh
    # create a new license (license returned in `key`)
    curl -H "Content-Type: application/json" \
    -X POST \
    -d '{"username": "tester","password": "testpwd","used_by": "12d8c6885151"}' \
    http://localhost:5000/licenses
    # Response:
    # {
    #   "created_at": "2021-03-26 03:53:09",
    #   "id": 1,
    #   "is_active": true,
    #   "key": "9e28ed47-b788-4a25-91e6-c36f7e1d3c72",
    #   "revoked_at": null,
    #   "used_by": "12d8c6885151",
    #   "username": "tester"
    # }

    # update a license
    curl -H "Content-Type: application/json" \
    -X PATCH \
    -d '{"is_active": false,"revoked_at": "2021-03-26 12:34:56"}' \
    http://localhost:5000/licenses/1
    # Response:
    # {
    #   "created_at": "2021-03-26 03:53:09",
    #   "id": 1,
    #   "is_active": false,
    #   "key": "9e28ed47-b788-4a25-91e6-c36f7e1d3c72",
    #   "revoked_at": "2021-03-26 12:34:56",
    #   "used_by": "12d8c6885151",
    #   "username": "tester"
    # }

    # list/query all licenses
    curl -X GET "http://localhost:5000/licenses?username=tester&is_active=false"        
    ```

5. In another termial, build image and spin up the example containerized app (also a Flask server)

    ```sh
    vagrant ssh

    cd /vagrant/App
    docker build -t app:1.0 . 
    docker run -p 9090:9090 --name app --rm app:1.0
    ```

   **NOTE: you can also change the `USERNAME` environment variable in `App/Dockerfile`, as every user can only have 2 licenses in active now.**

6. When the container is spun up, you should see the license printed out:
    ```sh
    # Successfully get license, then the app started:
    license <class 'dict'> {'created_at': '2021-05-14 00:06:51', 'id': 2, 'is_active': True, 'last_checkin': '2021-05-14 00:06:51', 'private_key': 'shh!', 'pub_key': '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtijttWS89VDFL1Qe4/c3\nKV9PFf6CSUDTXACzhjGAajWzPfu41IVp1wjmuGGjFg3IBaFY6T0zwoVx4lhg9jfx\nDE4f2vSiofO8pxyadx/hhhpWr7uXjcHRYwWbCXuBixM9gK0opUDjX3eCe0sngheg\nzp4ncbIAaTCB1nAAGMGvOsxrWGyPn0hFM0cO6dKI5v9Nadjf9CICcA2x5/7fhQUO\nJxXLZPucErS5PDwQmuBR2Gu2RgRws9Mf3PqibDL1q98XfNRGHbCDw7xoWv/8+XJc\nnnjYY/1oEKkd9rc5AABrMSdq0pDChRl/ut8sc+9c8E9ZdtUutVD34YE9qnEg+sqN\nYwIDAQAB\n-----END PUBLIC KEY-----\n', 'revoked_at': None, 'used_by': 'b907cbc83d1a', 'username': 'tester'}
    * Serving Flask app "app" (lazy loading)
    * Environment: production
      WARNING: This is a development server. Do not use it in a production deployment.
      Use a production WSGI server instead.
    * Debug mode: off
    * Running on http://0.0.0.0:9090/ (Press CTRL+C to quit)

    # Failed to get license, then the app exits:
    license <class 'dict'> {}
    Error: you don't have available license.
    ```

7.  Test the endpoints with POSTMAN or curl from your host machine (NOTE: replace `localhost` with `192.168.33.10` if you're using vagrant VM.)

    ```sh
    # get the welcome page
    curl -X GET http://localhost:9090/

    # get a fibonacci number
    curl -X GET http://localhost:9090/fibonacci?number=10 
    ```

8. You will see detailed logs for periodical check-in when the app container is running.

9.  Exit the app with `ctrl+c` and you should see the following log:
    ```
    Info: revoking license... res.status_code = 200
    Info: successfully revoked the license.
    ```

10. Remove the containers and/or images

    ```sh
    # list all containers
    docker container ls -a #list all containers, including stopped ones

    # remove containers
    docker rm <container name or container id> #<another container name> ...etc.

    #remove images
    docker rmi <image name>
    ```

11. Exit and stop the VM

    ```sh
    exit
    vagrant halt
    
    # destroy the vagrant machine
    vagrant destroy
    ```

<!-- ## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system -->

## Acknowledgments
- The `Vagrantfile`, `Dockerfile`, `docker-compose.yml`, `config.py` and the `service` directory are based on John J. Rofrano's [nyu-devops/lab-kubernetes](https://github.com/nyu-devops/lab-kubernetes) and [nyu-devops/lab-flask-tdd](https://github.com/nyu-devops/lab-flask-tdd)
