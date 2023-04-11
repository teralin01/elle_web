import logging
import copy
from jsonref import replace_refs
from jsonref import JsonRefError
from jsonschema import validate
from jsonschema import SchemaError
from jsonschema import ValidationError
class JsonValidator():
    """A class to validate JSON schema"""

    validator_schema = None
    def __init__(self, openapi_schema):
        """Init JSON schema validator with openAPI object

        Args:
            openapi_schema (dict): an dict whth openAPI 3.0 JSON format content
            
        Raises:
            ValueError: if JSON format is invalid
            JsonRefError: if dereference JSON schema error
        """

        if openapi_schema is None:
            raise ValueError("No openapi_schema data found")

        try:
            deref = replace_refs(openapi_schema)
            JsonValidator.validator_schema = deref
        except ValueError as exception:
            logging.error("init JSON fail %s",exception)
            raise

        except JsonRefError as exception:
            logging.error("JSON Ref Error %s",exception)
            raise
        except Exception as exp:
            logging.error("Exception %s ",str(exp))

    def validate_paramater_schema(self,validate_content, request_url, request_http_method):
        """The core function to validate JSON schema

        Args:
            validate_content (dict): incoming request body
            request_url (string): request URL
            request_http_method (string): HTTP request method

        Returns:
            boolen: Either pass or fail
            
        Raises:
            ValidationError: if JSON format is invalid
            SchemaError: if JSON schema is invalid
            
        """
        return_value = False
        reason = "None"
        logging.debug("Validating para: %s , %s, %s",validate_content, request_url, request_http_method )
        if None is JsonValidator.validator_schema:
            logging.error("!!!!!! No validator schema found !!!!!!!!")
            raise ImportError("No Validator schema found")
        try:
            target_schema = JsonValidator.validator_schema['paths'][request_url][request_http_method]['parameters'][0]['schema']
            target_schema["$schema"] = "http://json-schema.org/draft-04/schema#"
            validate(instance=validate_content, schema=target_schema)#Throw SchemaError or VaildationError exception if error
            return_value = True
        except SchemaError as exception:
            reason = str(exception.message)
        except ValidationError as exception:
            reason = str(exception.message)
        finally:
            return return_value,reason

    def validate_response_schema(self,validate_content, request_url, request_http_method, response_code):
        """The core function to validate JSON schema

        Args:
            validate_content (dict): incoming request 
            request_url (string): request URL
            request_http_method (string): HTTP request method

        Returns:
            boolen: Either pass or fail
            
        Raises:
            ValidationError: if JSON format is invalid
            SchemaError: if JSON schema is invalid. For example, the require field must be described as array.
        """
        if None is self.validator_schema:
            return False
        return_value = False
        try:
            target_schema = self.validator_schema['paths'][request_url][request_http_method]['responses'][response_code]['schema']
            target_schema["$schema"] = "http://json-schema.org/draft-04/schema#"
            validate(instance=validate_content, schema=target_schema)#Throw SchemaError or VaildationError exception if error
            return_value = True
        except  ValidationError  as exception:
            logging.error("validating JSON fail %s",exception)
            raise
        
        except SchemaError as exception:
            logging.error("JSON schema error%s",exception)
            raise
        finally:
            return return_value
