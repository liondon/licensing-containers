# Project Title

One Paragraph of project description goes here

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 
See deployment for notes on how to deploy the project on a live system.

### Prerequisites

```
virtualbox + vagrant
```
OR
```
docker
```

### Installing

1. (optional) Spin up and access the VM

    ```sh
    $ vagrant up
    $ vagrant ssh
    ```

2. Test docker installation

    ```sh
    docker run hello-world
    ```

3. Go to the project root directory (it's synced with `/vagrant` in the VM)

    ```sh
    cd /vagrant
    ```

4. Spin up example Flask app and Postgres database instance with docker-compose

    ```sh
    cd /vagrant/AuthSrvr
    docker-compose up
    ```

5. Test the endpoints with POSTMAN or curl from your host machine

    ```sh
    # create a new license (license returned in `key`)
    curl -H "Content-Type: application/json" \
    -X POST \
    -d '{"username": "tester2","password": "testpwd","used_by": "12d8c6885151"}' \
    http://localhost:5000/licenses
    # Response:
    # {
    #   "created_at": "2021-03-26 03:53:09",
    #   "id": 1,
    #   "is_active": true,
    #   "key": "9e28ed47-b788-4a25-91e6-c36f7e1d3c72",
    #   "revoked_at": null,
    #   "used_by": "12d8c6885151",
    #   "username": "tester2"
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
    #   "username": "tester2"
    # }

    # list/query all licenses
    curl -X GET http://localhost:5000/licenses?username=tester&is_active=false        
    ```

6. Get the url of the Auth server within the VM: 
   ```sh
   docker inspect authserver | jq '.[0].NetworkSettings.Networks.authsrvr_web.Gateway'
   ``` 
   Then use it to update the ip address part in the value of environment variable `AUTH_SERVER` in `App/Dockerfile` 
   
   (Simply use `localhost` or `127.0.0.1` might work if you're running both the containers directly on your laptop... need to test)

   **NOTE: you can also change the `USERNAME` environment variable in the dockerfile, as every user can only have 2 licenses in active now.**

7. Build image and spin up the example containerized app (also a Flask server)

    ```sh
    cd /vagrant/App
    docker build -t app:1.0 . 
    docker run -p 9090:9090 --name app app:1.0
    ```

8. When the container is spun up, you should see the license printed out:
    ```sh
    # Successfully get license, then the app started:
    license <class 'dict'> {'created_at': '2021-03-26 04:51:37', 'id': 6, 'is_active': True, 'key': '83646ee4-2750-4156-a0d8-a4cb88471465', 'revoked_at': None, 'used_by': '542f3c4c19c7', 'username': 'tester12'}
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

9.  Test the endpoints with POSTMAN or curl from your host machine

    ```sh
    # get the welcome page
    curl -X GET http://localhost:9090/

    # get a fibonacci number
    curl -X GET http://localhost:9090/fibonacci?number=10 
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
