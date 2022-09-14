missionSchema = {
    "definitions":
    {
        "missionEntry":
        {
            "properties":
            {
                "action_state":{
                    "type":"integer",
                    "minimum": 0,
                    "maximum": 5,
                },  
                "coordinate":{
                    "type":"object",
                    "properties": {
                            "x":{"type":"number", "multipleOf": 0.001},
                            "y":{"type":"number", "multipleOf": 0.001},
                            "z":{"type":"number", "multipleOf": 0.00001}
                    },
                    "required":["x","y","z"]
                },
                "station":{
                    "type":"string"
                },
                "docking_info":{
                    "type":"array",
                    "items":{
                          "type": "string"
                    }
                },
                "pose_cmd":{
                    "type":"object"
                }
            }
        }
    },
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "addMission",
    "description": "validate new mission command",
    "type": "object",
    "properties": {
        "mission": {
            "description": "New mission",
            "type": "object",
            "properties": {
                "overwrite_current_mission":{
                    "type":"boolean"
                    
                 },
                "set_as_default_mission":{
                    "type":"boolean"
                    
                 },
                "first":{
                    "type":"integer",
                     "minimum": 0,
                 },
                "repeats":{
                    "type":"integer", "not":{"enum":[0]}
                 },
                "name":{
                    "type":"string",
                    "minLength": 0,
                    "maxLength": 64
                 },
                "actions":{
                    "type":"array",
                    "minItems": 1,
                    "items": { "$ref": "#/definitions/missionEntry" }      
                 },                                                                
             },
            "required":["overwrite_current_mission","set_as_default_mission","first","repeats","actions"]
        }
    },
    "required": ["mission"]
}