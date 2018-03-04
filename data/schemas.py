schemas = {}

schemas['add'] = {
  "type": "array",
  "minItems": 1,
  "uniqueItems": True,
  "items": {
    "type": "object",
    "properties": {
      "compound": {
        "type": "string",
        "title": "Schema for the compound name",
        "description": "Proper chemical formula of the material",
        "default": ""
      },
      "properties": {
        "type": "array",
        "minItems": 1,
        "uniqueItems": True,
        "items": {
          "type": "object",
          "minProperties": 1,
          "properties": {
            "propertyName": {
              "type": "string",
              "title": "Schema for the property name ",
              "description": "Name of the physical/chemical property of the compound",
              "default": ""
            },
            "propertyValue": {
              "type": [
                "string",
                "number",
                "integer"
              ],
              "title": "Schema for the property value",
              "description": "Value of the property of the compound",
              "default": ""
            }
          },
          "additionalProperties": False,
          "required": [
            "propertyName",
            "propertyValue"
          ]
        }
      }
    },
    "additionalProperties": False,
    "required": [
      "compound",
      "properties"
    ]
  }
}

schemas['search'] = {
  "type": "object",
  "properties": {
    "compound": {
      "type": "object",
      "properties": {
        "logic": {
          "type": "string",
          "title": "Schema for compound name logic",
          "default": "matches"
        },
        "value": {
          "type": "string",
          "title": "Schema for compound name",
          "default": "",
          "minLength": 1
        }
      },
      "additionalProperties": False,
      "required": [
        "logic",
        "value"
      ]
    },
    "properties": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": True,
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "title": "Schema for the compound property name",
            "default": "",
            "minLength": 1
          },
          "value": {
            "type": [
              "string",
              "number",
              "integer"
            ],
            "title": "Schema for the compound property value",
            "default": "",
            "minLength": 1
          },
          "logic": {
            "type": "string",
            "title": "Schema for the compound property logic",
            "default": "eq"
          }
        },
        "additionalProperties": False,
        "required": [
          "name",
          "value",
          "logic"
        ]
      }
    }
  },
  "additionalProperties": False
}
