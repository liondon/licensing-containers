# Code adapted from John J. Rofrano's [nyu-devops/lab-flask-tdd]:
# https://github.com/nyu-devops/lab-flask-tdd

"""
Models for the Authorizing Service

All of the models are stored in this module

Models
------
License - A license in the pool
    Attributes:
    -----------
    username (string) 
        - the username of the owner
    used_by (string) 
        - the container_id (or other non-forgeable identifier for containers)
    key (string) 
        - the license (uuid)
    is_active (boolean) 
        - True for license is not revoked
    created_at (datetime.datetime() object) 
        - datetime when a license was created/assigned to a container 
    revoked_at (datetime.datetime() object) 
        - datetime when a license was revoked by a container 
    last_checkin
        - the time when the license is last checked in

"""

import logging
from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """

    pass


class License(db.Model):
    """
    Class that represents a License

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    logger = logging.getLogger(__name__)
    app = None

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    used_by = db.Column(db.String(64))
    key = db.Column(db.String(64))
    is_active = db.Column(db.Boolean())
    created_at = db.Column(db.DateTime())
    revoked_at = db.Column(db.DateTime())
    last_checkin = db.Column(db.DateTime())

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<License %r>" % (self.key)

    def create(self):
        """
        Creates a License to the data store
        """
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a License to the data store
        """
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """ Removes a License from the data store """
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes a License into a dictionary """
        return {
            "id": self.id,
            "username": self.username,
            "used_by": self.used_by,
            "key": self.key,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at is not None else None,
            "revoked_at": self.revoked_at.strftime("%Y-%m-%d %H:%M:%S") if self.revoked_at is not None else None,
            "last_checkin": self.last_checkin.strftime("%Y-%m-%d %H:%M:%S") if self.last_checkin is not None else None,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a License from a dictionary

        :param data: a dictionary of attributes
        :type data: dict

        :return: a reference to self
        :rtype: License

        """
        try:
            self.username = data["username"]
            self.used_by = data["used_by"]
            self.key = data["key"]
            self.is_active = data["is_active"]
            self.created_at = data["created_at"] 
            self.revoked_at = data["revoked_at"] 
            self.last_checkin = data["last_checkin"] 
        except KeyError as error:
            raise DataValidationError("Invalid License: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid License: body of request contained bad or no data"
            )
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app):
        """Initializes the database session

        :param app: the Flask app
        :type data: Flask

        """
        cls.logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the Licenses in the database """
        cls.logger.info("Processing all Licenses")
        return cls.query.all()

    @classmethod
    def find(cls, license_id: int):
        """Finds a License by it's ID

        :param license_id: the id of the License to find
        :type license_id: int

        :return: an instance with the license_id, or None if not found
        :rtype: License

        """
        cls.logger.info("Processing lookup for id %s ...", license_id)
        return cls.query.get(license_id)

    @classmethod
    def find_or_404(cls, license_id: int):
        """Find a License by it's id

        :param license_id: the id of the License to find
        :type license_id: int

        :return: an instance with the license_id, or 404_NOT_FOUND if not found
        :rtype: License

        """
        cls.logger.info("Processing lookup or 404 for id %s ...", license_id)
        return cls.query.get_or_404(license_id)

    @classmethod
    def find_by_query_string(cls, args):
        """ Find Licenses by query string """
        cls.logger.info(" Processing lookup based on query string %s ...", args)
        return cls.query.filter_by(**args).order_by(License.created_at).all()
