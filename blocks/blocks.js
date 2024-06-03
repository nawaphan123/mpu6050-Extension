Blockly.defineBlocksWithJsonArray(
[{
  "type": "mpu6050_Setup",
  "message0": "MPU6050 setup with address %1",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "addr",
      "options": [
        [
          "0x68",
          "0x68"
        ],
        [
          "0x69",
          "0x69"
        ]
      ]
    }
  ],
  "previousStatement": null,
  "nextStatement": null,
  "colour": "#E74C3C",
  "tooltip": "",
  "helpUrl": ""
},
{
  "type": "mpu6050_Update",
  "message0": "MPU6050 update data",
  "previousStatement": null,
  "nextStatement": null,
  "colour": "#E74C3C",
  "tooltip": "",
  "helpUrl": ""
},
{
  "type": "mpu6050_get_Acc",
  "message0": "MPU6050 get acceleration %1",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "axis",
      "options": [
        [
          "x",
          "x"
        ],
        [
          "y",
          "y"
        ],
        [
          "z",
          "z"
        ]
      ]
    }
  ],
  "output": null,
  "colour": "#E74C3C",
  "tooltip": "",
  "helpUrl": ""
},
{
  "type": "mpu6050_get_Gyro",
  "message0": "MPU6050 get gyro %1",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "axis",
      "options": [
        [
          "x",
          "x"
        ],
        [
          "y",
          "y"
        ],
        [
          "z",
          "z"
        ]
      ]
    }
  ],
  "output": null,
  "colour": "#E74C3C",
  "tooltip": "",
  "helpUrl": ""
},
{
  "type": "mpu6050_get_Angle",
  "message0": "MPU6050 get Angle %1",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "angle",
      "options": [
        [
          "X",
          "X"
        ],
        [
          "Y",
          "Y"
        ],
        [
          "Z",
          "Z"
        ]
      ]
    }
  ],
  "output": null,
  "colour": "#E74C3C",
  "tooltip": "",
  "helpUrl": ""
},
]
);
