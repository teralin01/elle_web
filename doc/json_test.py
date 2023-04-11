import json
from jsonref import replace_refs
from openapi_schema_to_json_schema import to_json_schema

json_file = open('docs.json','r')

openapi_schema = json.load(json_file)

options = {"supportPatternProperties": True}
converted = to_json_schema(openapi_schema, options)
try:
    converted2 = replace_refs(converted)
except Exception as exp:
    print(exp)

print(json.dumps(converted2, indent=2))
