# Code adapted from John J. Rofrano's [nyu-devops/lab-flask-tdd]:
# https://github.com/nyu-devops/lab-flask-tdd

"""
Authorizing Service

# Paths:
# ------
# GET /pets - Returns a list all of the Pets
# GET /pets/{id} - Returns the Pet with a given id number
# POST /pets - creates a new Pet record in the database
# PUT /pets/{id} - updates a Pet record in the database
# DELETE /pets/{id} - deletes a Pet record in the database
"""

import os
import sys
import logging
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes
from werkzeug.exceptions import NotFound, Forbidden, InternalServerError
import uuid
from datetime import datetime

# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from .models import License, DataValidationError

# Import Flask application
from . import app

######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)

@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=str(error)
        ),
        status.HTTP_400_BAD_REQUEST,
    )

@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_404_NOT_FOUND, error="Not Found", message=str(error)
        ),
        status.HTTP_404_NOT_FOUND,
    )

@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            error="Method not Allowed",
            message=str(error),
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )

@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=str(error),
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    )

@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    app.logger.error(str(error))
    return (
        jsonify(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=str(error),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="Authorizing Service",
            version="1.0",
            paths=url_for("list_licenses", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# LIST ALL License
######################################################################
@app.route("/licenses", methods=["GET"])
def list_licenses():
    """ Returns all of the Licenses """
    args = request.args.to_dict()
    app.logger.info("Request to list Licenses based on query string %s ...", args)
    licenses = License.find_by_query_string(args)
    results = [lic.serialize() for lic in licenses]
    app.logger.info("Returning %d licenses", len(results))
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A License
######################################################################
@app.route("/licenses/<int:license_id>", methods=["GET"])
def get_licenses(license_id):
    """
    Retrieve a single License

    This endpoint will return a License based on it's id
    """
    app.logger.info("Request for license with id: %s", license_id)
    lic = License.find(license_id)
    if not lic:
        raise NotFound("License with id '{}' was not found.".format(license_id))

    app.logger.info("Returning lic: %s", lic.key)
    return make_response(jsonify(lic.serialize()), status.HTTP_200_OK)


######################################################################
# UPDATE AN EXISTING License with req.body containing ALL the fields
######################################################################
@app.route("/licenses/<int:license_id>", methods=["PUT"])
def update_licenses(license_id):
    """
    Update a License

    This endpoint will update a License based the body that is posted
    """
    app.logger.info("Request to update license with id: %s", license_id)
    check_content_type("application/json")
    lic = License.find(license_id)
    if not lic:
        raise NotFound("License with id '{}' was not found.".format(license_id))
    lic.deserialize(request.get_json())
    lic.id = license_id
    lic.update()

    app.logger.info("License with ID [%s] updated.", lic.id)
    return make_response(jsonify(lic.serialize()), status.HTTP_200_OK)


######################################################################
# UPDATE AN EXISTING License with req.body containing ANY fields
######################################################################
@app.route("/licenses/<int:license_id>", methods=["PATCH"])
def patch_licenses(license_id):
    """
    Update a License

    This endpoint will update a License based the body that is posted
    """
    app.logger.info("Request to update license with id: %s", license_id)
    check_content_type("application/json")
    lic = License.find(license_id)
    if not lic:
        raise NotFound("License with id '{}' was not found.".format(license_id))

    # use existing values for the fields
    update_data = request.get_json()
    for field in update_data:
        setattr(lic, field, update_data[field])
    lic.id = license_id
    lic.update()

    app.logger.info("License with ID [%s] updated.", lic.id)
    return make_response(jsonify(lic.serialize()), status.HTTP_200_OK)


######################################################################
# ADD A NEW License
######################################################################
@app.route("/licenses", methods=["POST"])
def create_licenses():
    """
    Creates a License
    This endpoint will create a License based the data in the body that is posted
    """
    app.logger.info("Request to create a license")
    check_content_type("application/json")

    data = request.get_json()

    # authenticate user
    if not authenticate(data["username"], data["password"]):
        return make_response(jsonify({}), status.HTTP_401_UNAUTHORIZED)

    # check if the user has available license
    # TODO: max_license_available should be stored at the users table, we hardcoded it for now.
    max_license_available = 2
    if not check_license_available(data["username"], max_license_available):
        return make_response(jsonify({}), status.HTTP_403_FORBIDDEN)

    data["is_active"] = True
    data["key"] = uuid.uuid4()
    data["created_at"] = datetime.now()
    data["revoked_at"] = None
    data["last_checkin"] = datetime.now()

    lic = License()
    lic.deserialize(data)
    lic.create()

    message = lic.serialize()
    location_url = url_for("get_licenses", license_id=lic.id, _external=True)

    app.logger.info("License with ID [%s] created.", lic.id)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


# # ###################################################################
# # # DELETE A License
# # ###################################################################
# @app.route("/licenses/<int:license_id>", methods=["DELETE"])
# def delete_licenses(license_id):
#     """
#     Delete a license

#     This endpoint will delete a License based on the license_id in the path

#     """
#     app.logger.info("Request to delete license with id: %s", license_id)
#     lic = License.find(license_id)
#     if lic:
#         try:
#             lic.delete()
#             app.logger.info("License with ID [%s] delete complete.", license_id)
#             return make_response("", status.HTTP_200_OK)
#         except:
#             app.logger.info("License with ID [%s] delete failed.", license_id)
#             return make_response("", status.HTTP_500_INTERNAL_SERVER_ERROR)


######################################################################
# Endpoint for periodical checkin
######################################################################
@app.route("/licenses/<int:license_id>/checkin", methods=["POST"])
def periodically_checkin(license_id):
    """
    When the application container ping this endpoint,
    Then AS checks the `container_id` and `key` in request body,
    If they do not match the record in DB, 
        return 403 Forbidden
    If they matches the record in DB, 
        Then AS updated a field `last_checkedin` to current time,
        return 200 if succeeded
        return 500 if failed
    """
    app.logger.info("Checkin request for license with id: %s", license_id)
    check_content_type("application/json")

    lic = License.find(license_id)
    if not lic:
        raise NotFound("License with id '{}' was not found.".format(license_id))

    # check if request matches the record in DB
    else:
        request_body = request.get_json()
        req_cid = request_body['used_by']
        req_key = request_body['key']
        lic_cid = lic.used_by
        lic_key = lic.key
        app.logger.debug("req_cid: {}".format(req_cid))
        app.logger.debug("req_key: {}".format(req_key))
        app.logger.debug("lic_cid: {}".format(lic_cid))
        app.logger.debug("lic_key: {}".format(lic_key))

        if lic_cid == req_cid and lic_key == req_key:
            # update 'last_checkin' to current time
            try:
                lic.last_checkin = datetime.now()
                lic.update()    # actually write to the database
                app.logger.info("Successfully updated last_checkin field of current license with id '{}'.".format(license_id))
                return make_response(jsonify(lic.serialize()), status.HTTP_200_OK)
            except:
                raise InternalServerError("Failed to update last_checkin field of current license with id '{}'.".format(license_id))
        else:
            raise Forbidden("The info of '{}' does not match the record in DB.".format(license_id))


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def init_db():
    """ Initializes the SQLAlchemy app """
    global app
    License.init_db(app)

def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(415, "Content-Type must be {}".format(content_type))

# TODO:
def authenticate(username, password):
    return True

def check_license_available(username, max_license_available):
    licenses = License.find_by_query_string({
        "username": username,
        "is_active": True
    })
    results = [lic.serialize() for lic in licenses]
    app.logger.info("Returning %d licenses", len(results))

    return True if len(results) < max_license_available else False
