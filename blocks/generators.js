Blockly.Python['mpu6050_Setup'] = function(block) {
  Blockly.Python.definitions_['from_mpu6050_import_mpu6050'] = 'from MPU6050 import MPU6050';

  var dropdown_addr = block.getFieldValue('addr');
  var code = `mpu = MPU6050('X')\nmpu.setUp()\n`;
  return code;
};

Blockly.Python['mpu6050_Update'] = function(block) {
  var code = `mpu.update()`;
  return code;
};

Blockly.Python['mpu6050_get_Acc'] = function(block) {
  var dropdown_axis = block.getFieldValue('axis');
  var code = `mpu.accel.${dropdown_axis}()`;
  return [code, Blockly.Python.ORDER_NONE];
};

Blockly.Python['mpu6050_get_Gyro'] = function(block) {
  var dropdown_axis = block.getFieldValue('axis');
  var code = `mpu.gyro.${dropdown_axis}()`;
  return [code, Blockly.Python.ORDER_NONE];
};
Blockly.Python['mpu6050_get_Angle'] = function(block) {
  var dropdown_axis = block.getFieldValue('angle');
  var code = `mpu.getAngle${dropdown_axis}()`;
  return [code, Blockly.Python.ORDER_NONE];
};


