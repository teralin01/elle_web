from http import HTTPStatus   #Refer to https://docs.python.org/3/library/http.html
from datetime import datetime
import logging
import tornado.web
import tornado.ioloop
from tornado.escape import json_decode
from json.decoder import JSONDecodeError
from control.system.json_validator import JsonValidator
from jsonschema import SchemaError
from jsonschema import ValidationError

class TornadoBaseHandler(tornado.web.RequestHandler):
    def __init__(self,*args, **kwargs):
        super(TornadoBaseHandler,self).__init__(*args, **kwargs)
        self.set_default_headers()
        self._status_code = HTTPStatus.OK.value
        self.timeout_string = {"result":False,"reason":"Request Timeout"}
        self.rest_timeout_period = 10
        self.cache_hit = False
        self.uri = self.request.path
        self.cache_rest_data = dict()
        self.request_data = None
        self.validating_success = False

    def prepare(self):
        if not self.get_secure_cookie("elle_web"):
            self.set_secure_cookie("elle_web",datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), max_age=30)

        if self.request.method == 'GET':
            pass # Skip input content validation
        elif self.request.method == 'POST' or self.request.method == "PUT":
            self._status_code = HTTPStatus.CREATED.value
            if self.request.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    self.request_data = json_decode(self.request.body)
                    logging.debug(self.request_data)
                    self.validating_success,reason = JsonValidator.validate_paramater_schema(JsonValidator, self.request_data, self.request.uri, self.request.method.lower())
                    if not self.validating_success:
                        self.error_response(reason)
                except (JSONDecodeError, TypeError, ValueError,) as exception: #the exceptions for decode
                    self.error_response(str(exception))
                except (SchemaError,ValidationError,ImportError) as exception: #the exceptions for JSON validation
                    self.error_response(str(exception.message))
            else:
                self.error_response("Not supported Content type")

    def error_response(self,reason):
        logging.error("Validation error %s: ",reason)
        self._status_code = HTTPStatus.BAD_REQUEST.value
        default_return = {"result": False,"reason":reason}
        self.rest_response(default_return)

    def set_default_headers(self):
        if self.application.settings.get('debug'): # debug mode is True then support CORS
            self.set_dev_cors_headers()

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def set_dev_cors_headers(self):
        # For development only
        # Not safe for production
        origin = self.request.headers.get('Origin', '*') # use current requesting origin
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, x-requested-with, x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
        self.set_header('Access-Control-Expose-Headers', 'content-type, location, *, set-cookie')
        self.set_header('Access-Control-Request-Headers', '*')
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def rest_response(self,data):
        # Todo add log if necessary
        if self._status_code == HTTPStatus.OK.value:
            if data is not None and not self.cache_hit:
                self.cache_rest_data.update({self.uri:{'cacheData':data,'lastUpdateTime':datetime.now()}})
        try:
            self.write(data)
            self.finish()
        except Exception as exception:
            logging.info("REST Response Error %s",str(exception))

    #TODO Add default user authenication method