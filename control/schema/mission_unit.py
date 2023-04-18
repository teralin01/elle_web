from packages.tornado_openapi.model import register_swagger_model
from packages.tornado_openapi.parameter import register_swagger_parameter

@register_swagger_parameter
class MissionActivityTrigger:
    """
    ---
    name: trigger mission activity
    description: set mission state to start/stop/reload/skip/abort
    type: object
    properties:
      command:
        type: integer
        format: int32
        minimum: 0
        maximum: 4
        example: 0  
    required:
    - command    
    """

@register_swagger_parameter
class MissionItem:
    """
    ---
    name: missions
    in: path
    description: add a mission
    type: object
    properties:
      mission:
        type: object
        properties:
          overwrite_current_mission:
            type: boolean
            example: false
          set_as_default_mission:
            type: boolean
            example: false
          first:
            type: integer
            format: int32
            minimum: 0
            example: 0
          repeats:
            type: integer
            format: int32
            example: 1
          name:
            type: string
            minLength: 0
            maxLength: 64
          actions:
            type: array
            items:
              type: object
              minItems: 1
              properties:
                action_state:
                    type: integer
                    format: int32
                    minimum: 0
                    maximum: 5
                    example: 1
                coordinate:
                    required:
                    - x
                    - y
                    - z
                    type: object
                    properties:
                      x:
                        type: number
                        multipleOf: 0.001
                        example: 1.234
                      y:
                        type: number
                        multipleOf: 0.001
                        example: 6.789
                      z:
                        type: number
                        multipleOf: 0.00001
                        example: 1.23456
    required: 
    - mission
    """

@register_swagger_model
class MissionUnit:
    """
    ---
    description: a unit of mission
    type: object
    properties:
      mission:
        type: object
        properties:
          overwrite_current_mission:
            type: boolean
            example: false
          set_as_default_mission:
            type: boolean
            example: false
          first:
            type: integer
            format: int32
            minimum: 0
            example: 0
          repeats:
            type: integer
            format: int32
            example: 1
          name:
            type: string
            minLength: 0
            maxLength: 64
            example: remote1
          actions:
            type: array
            items:
              type: object
              minItems: 1
              properties:
                action_state:
                    type: integer
                    format: int32
                    minimum: 0
                    maximum: 5
                    example: 1
                coordinate:
                    required:
                    - x
                    - y
                    - z
                    type: object
                    properties:
                      x:
                        type: number
                        multipleOf: 0.001
                        example: 1.234
                      y:
                        type: number
                        multipleOf: 0.001
                        example: 6.789
                      z:
                        type: number
                        multipleOf: 0.00001
                        example: 1.23456
        required:
          - overwrite_current_mission
          - set_as_default_mission
          - first
          - repeats
          - actions
    required: 
    - mission
    """
