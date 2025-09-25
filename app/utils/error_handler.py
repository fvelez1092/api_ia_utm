from flask import current_app as app
from app.utils.response import create_response
from werkzeug.exceptions import HTTPException, BadRequestKeyError
from marshmallow.exceptions import ValidationError
from app.extensions import logger_app, db

def handle_error(error):  
    status_error = 'error'
    db.session.rollback()
    with app.app_context():
      logger_app.exception("")
    if isinstance(error, BadRequestKeyError):
        status_code = 400
        message = error.__class__.__name__
        data = {}
        for arg in error.args:
            data.update({arg: 'Query param not found.'})
    elif isinstance(error, ValidationError):
        status_code = 200
        message = "Marshmallow Validation Error"
        data = error.messages
        status_error = 'fail'
    elif isinstance(error, HTTPException):#: Base HTTP's Exceptions
        status_code = error.code
        message = "{}: {}".format(error.name, str(error))
        data = None
    elif isinstance(error, Exception):#: Base Exceptions
        status_code = 200
        message = error.__class__.__name__
        data = error.__str__()
    else:
        status_code = 500
        message = 'Internal Server Error: An unexpected error occurred'
        data = None

    response = create_response(status_error, data=data, message=message, status_code=status_code)
    return response
