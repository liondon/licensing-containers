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
    http://192.168.33.10:5000/licenses
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
    http://192.168.33.10:5000/licenses/1
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
    curl -X GET http://192.168.33.10:5000/licenses?username=tester&is_active=false        
    ```

6. Use `docker inspect` to get the url of the Auth server within the VM, then change the environment variable `AUTH_SERVER` in `App/Dockerfile` and/or the default value of it in the `App/app.py`.

7. Build image and spin up the example containerized app (also a Flask server)

    ```sh
    cd /vagrant/App
    docker build -t app:1.0 . 
    docker run -p 9090:9090 --name app app:1.0
    ```

8. Test the endpoints with POSTMAN or curl from your host machine

    ```sh
    # get the welcome page
    curl -X GET http://192.168.33.10:9090/

    # get a fibonacci number
    curl -X GET http://192.168.33.10:9090/fibonacci?number=10 
    ```

9. Remove the containers and/or images

    ```sh
    # list all containers
    docker container ls -a #list all containers, including stopped ones

    # remove containers
    docker rm <container name or container id> #<another container name> ...etc.

    #remove images
    docker rmi <image name>
    ```
   
10. Exit and stop the VM

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
