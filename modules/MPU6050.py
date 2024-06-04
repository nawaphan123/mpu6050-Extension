# imu.py MicroPython driver for the InvenSense inertial measurement units
# This is the base class
# Adapted from Sebastian Plamauer's MPU9150 driver:
# https://github.com/micropython-IMU/micropython-mpu9150.git
# Authors Peter Hinch, Sebastian Plamauer
# V0.2 17th May 2017 Platform independent: utime and machine replace pyb

# vector3d.py 3D vector class for use in inertial measurement unit drivers
# Authors Peter Hinch, Sebastian Plamauer

# V0.7 17th May 2017 pyb replaced with utime
# V0.6 18th June 2015

"""
mpu9250 is a micropython module for the InvenSense MPU9250 sensor.
It measures acceleration, turn rate and the magnetic field in three axis.
mpu9150 driver modified for the MPU9250 by Peter Hinch

The MIT License (MIT)
Copyright (c) 2014 Sebastian Plamauer, oeplse@gmail.com, Peter Hinch
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# User access is now by properties e.g.
# myimu = MPU9250('X')
# magx = myimu.mag.x
# accelxyz = myimu.accel.xyz
# Error handling: on code used for initialisation, abort with message
# At runtime try to continue returning last good data value. We don't want aircraft
# crashing. However if the I2C has crashed we're probably stuffed.

from utime import sleep_ms
from machine import I2C,Pin
import time
from math import sqrt, degrees, acos, atan2

class MPUException(OSError):
    """
    Exception for MPU devices
    """

    pass


def bytes_toint(msb, lsb):
    """
    Convert two bytes to signed integer (big endian)
    for little endian reverse msb, lsb arguments
    Can be used in an interrupt handler
    """
    if not msb & 0x80:
        return msb << 8 | lsb  # +ve
    return -(((msb ^ 255) << 8) | (lsb ^ 255) + 1)


class MPU6050(object):
    """
    Module for InvenSense IMUs. Base class implements MPU6050 6DOF sensor, with
    features common to MPU9150 and MPU9250 9DOF sensors.
    """

    _I2Cerror = "I2C failure when communicating with IMU"
    _mpu_addr = (104, 105)  # addresses of MPU9150/MPU6050. There can be two devices
    _chip_id = 104

    def __init__(self, side_str, scl = 22,sca = 21, device_addr = None,transposition=(0, 1, 2), scaling=(1, 1, 1)):
        

        self._accel = Vector3d(transposition, scaling, self._accel_callback)
        self._gyro = Vector3d(transposition, scaling, self._gyro_callback)
        self.buf1 = bytearray(1)  # Pre-allocated buffers for reads: allows reads to
        self.buf2 = bytearray(2)  # be done in interrupt handlers
        self.buf3 = bytearray(3)
        self.buf6 = bytearray(6)

        sleep_ms(200)  # Ensure PSU and device have settled
        if isinstance(side_str, str):  # Non-pyb targets may use other than X or Y
            self._mpu_i2c = I2C(-1, scl=Pin(scl), sda=Pin(sca))
        elif hasattr(side_str, "readfrom"):  # Soft or hard I2C instance. See issue #3097
            self._mpu_i2c = side_str
        else:
            raise ValueError("Invalid I2C instance")

        if device_addr is None:
            devices = set(self._mpu_i2c.scan())
            mpus = devices.intersection(set(self._mpu_addr))
            number_of_mpus = len(mpus)
            if number_of_mpus == 0:
                raise MPUException("No MPU's detected")
            elif number_of_mpus == 1:
                self.mpu_addr = mpus.pop()
            else:
                raise ValueError("Two MPU's detected: must specify a device address")
        else:
            if device_addr not in (0, 1):
                raise ValueError("Device address must be 0 or 1")
            self.mpu_addr = self._mpu_addr[device_addr]

        self.chip_id  # Test communication by reading chip_id: throws exception on error
        # Can communicate with chip. Set it up.
        self.wake()  # wake it up
        self.passthrough = True  # Enable mag access from main I2C bus
        self.accel_range = 0  # default to highest sensitivity
        self.gyro_range = 0  # Likewise for gyro
        
        #angleZ
        self.gyroZoffset = 0
        self.gyroXoffset = 0
        self.gyroYoffset = 0
        self.gyroZ = 0
        self.angleGyroZ = 0
        self.angleZ = 0
        self.preInterval = 0
        self.DoffsetZ = 0
        self.DoffsetY = 0
        self.DoffsetX = 0
        self.angleGyroX = 0
        self.angleGyroY = 0
        self.angleX = 0
        self.angleY = 0
        
    def begin(self):
        self.update()
        self.angleX = self.getAngleX()
        self.angleY = self.getAngleY()
        self.preInterval = (time.ticks_ms())
        
    def setGyroOffsets(self, x,y,z):
        self.gyroZoffset = z
        self.gyroXoffset = x
        self.gyroYoffset = y
        
    
    def calcGyroOffsets(self):
        print("Please don't move")
        z = 0
        x = 0
        y = 0
        
        for i in range(100):
            z += self.gyro.z
            x += self.gyro.x
            y += self.gyro.y
            time.sleep(0.001)
        self.gyroZoffset = z / 100
        self.gyroXoffset = x / 100
        self.gyroYoffset = y /100
        print("Calibration finished")
        time.sleep(0.1)
        
    def update(self):
        accY = self.accel.y
        accX = self.accel.x
        accZ = self.accel.z
        
        angleAccX = atan2(accY, accZ + abs(accX)) * 360 / 2.0 / 3.141
        angleAccY = atan2(accX, accZ + abs(accY)) * 360 / -2.0 / 3.141
        
        self.gyroZ = self.gyro.z
        self.gyroX = self.gyro.x
        self.gyroY = self.gyro.y
        
        self.gyroZ -= self.gyroZoffset
        self.gyroX -= self.gyroXoffset
        self.gyroY -= self.gyroYoffset
        
        now = time.ticks_ms()
        interval = ((now) - self.preInterval) * 0.001
        self.angleGyroZ += self.gyroZ * interval
        self.angleGyroX += self.gyroX * interval
        self.angleGyroY += self.gyroY * interval
        
        self.angleZ = int((self.angleGyroZ))-self.DoffsetZ
        self.angleX = (0.98 * (self.angleX + self.gyroX * interval)) + (0.02 * angleAccX)
        self.angleY = (0.98 * (self.angleY + self.gyroY * interval)) + (0.02 * angleAccY)
        self.preInterval = (time.ticks_ms())
        
    def getAngleZ(self):
        self.update()
        return int(self.angleZ+180)
    def getAngleX(self):
        self.update()
        return int(self.angleX+180)
    def getAngleY(self):
        self.update()
        return int(self.angleY+180)
    
    def setUp(self):
        self.begin()
        self.calcGyroOffsets()
        self.update()
        self.getAngleZ()
        self.DoffsetZ = self.angleZ
        self.DoffsetY = self.angleY
        self.DoffsetX = self.angleX
    
        
    # read from device
    def _read(self, buf, memaddr, addr):  # addr = I2C device address, memaddr = memory location within the I2C device
        """
        Read bytes to pre-allocated buffer Caller traps OSError.
        """
        self._mpu_i2c.readfrom_mem_into(addr, memaddr, buf)

    # write to device
    def _write(self, data, memaddr, addr):
        """
        Perform a memory write. Caller should trap OSError.
        """
        self.buf1[0] = data
        self._mpu_i2c.writeto_mem(addr, memaddr, self.buf1)

    # wake
    def wake(self):
        """
        Wakes the device.
        """
        try:
            self._write(0x01, 0x6B, self.mpu_addr)  # Use best clock source
        except OSError:
            raise MPUException(self._I2Cerror)
        return "awake"

    # mode
    def sleep(self):
        """
        Sets the device to sleep mode.
        """
        try:
            self._write(0x40, 0x6B, self.mpu_addr)
        except OSError:
            raise MPUException(self._I2Cerror)
        return "asleep"

    # chip_id
    @property
    def chip_id(self):
        """
        Returns Chip ID
        """
        try:
            self._read(self.buf1, 0x75, self.mpu_addr)
        except OSError:
            raise MPUException(self._I2Cerror)
        chip_id = int(self.buf1[0])
        if chip_id != self._chip_id:
            print("Possible clone chip?")
        return chip_id

    @property
    def sensors(self):
        """
        returns sensor objects accel, gyro
        """
        return self._accel, self._gyro

    # passthrough
    @property
    def passthrough(self):
        """
        Returns passthrough mode True or False
        """
        try:
            self._read(self.buf1, 0x37, self.mpu_addr)
            return self.buf1[0] & 0x02 > 0
        except OSError:
            raise MPUException(self._I2Cerror)

    @passthrough.setter
    def passthrough(self, mode):
        """
        Sets passthrough mode True or False
        """
        if type(mode) is bool:
            val = 2 if mode else 0
            try:
                self._write(val, 0x37, self.mpu_addr)  # I think this is right.
                self._write(0x00, 0x6A, self.mpu_addr)
            except OSError:
                raise MPUException(self._I2Cerror)
        else:
            raise ValueError("pass either True or False")

    # sample rate. Not sure why you'd ever want to reduce this from the default.
    @property
    def sample_rate(self):
        """
        Get sample rate as per Register Map document section 4.4
        SAMPLE_RATE= Internal_Sample_Rate / (1 + rate)
        default rate is zero i.e. sample at internal rate.
        """
        try:
            self._read(self.buf1, 0x19, self.mpu_addr)
            return self.buf1[0]
        except OSError:
            raise MPUException(self._I2Cerror)

    @sample_rate.setter
    def sample_rate(self, rate):
        """
        Set sample rate as per Register Map document section 4.4
        """
        if rate < 0 or rate > 255:
            raise ValueError("Rate must be in range 0-255")
        try:
            self._write(rate, 0x19, self.mpu_addr)
        except OSError:
            raise MPUException(self._I2Cerror)

    # accelerometer range
    @property
    def accel_range(self):
        """
        Accelerometer range
        Value:              0   1   2   3
        for range +/-:      2   4   8   16  g
        """
        try:
            self._read(self.buf1, 0x1C, self.mpu_addr)
            ari = self.buf1[0] // 8
        except OSError:
            raise MPUException(self._I2Cerror)
        return ari

    @accel_range.setter
    def accel_range(self, accel_range):
        """
        Set accelerometer range
        Pass:               0   1   2   3
        for range +/-:      2   4   8   16  g
        """
        ar_bytes = (0x00, 0x08, 0x10, 0x18)
        if accel_range in range(len(ar_bytes)):
            try:
                self._write(ar_bytes[accel_range], 0x1C, self.mpu_addr)
            except OSError:
                raise MPUException(self._I2Cerror)
        else:
            raise ValueError("accel_range can only be 0, 1, 2 or 3")

    # gyroscope range
    @property
    def gyro_range(self):
        """
        Gyroscope range
        Value:              0   1   2    3
        for range +/-:      250 500 1000 2000  degrees/second
        """
        # set range
        try:
            self._read(self.buf1, 0x1B, self.mpu_addr)
            gri = self.buf1[0] // 8
        except OSError:
            raise MPUException(self._I2Cerror)
        return gri

    @gyro_range.setter
    def gyro_range(self, gyro_range):
        """
        Set gyroscope range
        Pass:               0   1   2    3
        for range +/-:      250 500 1000 2000  degrees/second
        """
        gr_bytes = (0x00, 0x08, 0x10, 0x18)
        if gyro_range in range(len(gr_bytes)):
            try:
                self._write(
                    gr_bytes[gyro_range], 0x1B, self.mpu_addr
                )  # Sets fchoice = b11 which enables filter
            except OSError:
                raise MPUException(self._I2Cerror)
        else:
            raise ValueError("gyro_range can only be 0, 1, 2 or 3")

    # Accelerometer
    @property
    def accel(self):
        """
        Acceleremoter object
        """
        return self._accel

    def _accel_callback(self):
        """
        Update accelerometer Vector3d object
        """
        try:
            self._read(self.buf6, 0x3B, self.mpu_addr)
        except OSError:
            raise MPUException(self._I2Cerror)
        self._accel._ivector[0] = bytes_toint(self.buf6[0], self.buf6[1])
        self._accel._ivector[1] = bytes_toint(self.buf6[2], self.buf6[3])
        self._accel._ivector[2] = bytes_toint(self.buf6[4], self.buf6[5])
        scale = (16384, 8192, 4096, 2048)
        self._accel._vector[0] = self._accel._ivector[0] / scale[self.accel_range]
        self._accel._vector[1] = self._accel._ivector[1] / scale[self.accel_range]
        self._accel._vector[2] = self._accel._ivector[2] / scale[self.accel_range]

    # Gyro
    @property
    def gyro(self):
        """
        Gyroscope object
        """
        return self._gyro

    def _gyro_callback(self):
        """
        Update gyroscope Vector3d object
        """
        try:
            self._read(self.buf6, 0x43, self.mpu_addr)
        except OSError:
            raise MPUException(self._I2Cerror)
        self._gyro._ivector[0] = bytes_toint(self.buf6[0], self.buf6[1])
        self._gyro._ivector[1] = bytes_toint(self.buf6[2], self.buf6[3])
        self._gyro._ivector[2] = bytes_toint(self.buf6[4], self.buf6[5])
        scale = (131, 65.5, 32.8, 16.4)
        self._gyro._vector[0] = self._gyro._ivector[0] / scale[self.gyro_range]
        self._gyro._vector[1] = self._gyro._ivector[1] / scale[self.gyro_range]
        self._gyro._vector[2] = self._gyro._ivector[2] / scale[self.gyro_range]

        





def default_wait():
    '''
    delay of 50 ms
    '''
    sleep_ms(50)


class Vector3d(object):
    '''
    Represents a vector in a 3D space using Cartesian coordinates.
    Internally uses sensor relative coordinates.
    Returns vehicle-relative x, y and z values.
    '''
    def __init__(self, transposition, scaling, update_function):
        self._vector = [0, 0, 0]
        self._ivector = [0, 0, 0]
        self.cal = (0, 0, 0)
        self.argcheck(transposition, "Transposition")
        self.argcheck(scaling, "Scaling")
        if set(transposition) != {0, 1, 2}:
            raise ValueError('Transpose indices must be unique and in range 0-2')
        self._scale = scaling
        self._transpose = transposition
        self.update = update_function

    def argcheck(self, arg, name):
        '''
        checks if arguments are of correct length
        '''
        if len(arg) != 3 or not (type(arg) is list or type(arg) is tuple):
            raise ValueError(name + ' must be a 3 element list or tuple')

    def calibrate(self, stopfunc, waitfunc=default_wait):
        '''
        calibration routine, sets cal
        '''
        self.update()
        maxvec = self._vector[:]                # Initialise max and min lists with current values
        minvec = self._vector[:]
        while not stopfunc():
            waitfunc()
            self.update()
            maxvec = list(map(max, maxvec, self._vector))
            minvec = list(map(min, minvec, self._vector))
        self.cal = tuple(map(lambda a, b: (a + b)/2, maxvec, minvec))

    @property
    def _calvector(self):
        '''
        Vector adjusted for calibration offsets
        '''
        return list(map(lambda val, offset: val - offset, self._vector, self.cal))

    @property
    def x(self):                                # Corrected, vehicle relative floating point values
        self.update()
        return self._calvector[self._transpose[0]] * self._scale[0]

    @property
    def y(self):
        self.update()
        return self._calvector[self._transpose[1]] * self._scale[1]

    @property
    def z(self):
        self.update()
        return self._calvector[self._transpose[2]] * self._scale[2]

    @property
    def xyz(self):
        self.update()
        return (self._calvector[self._transpose[0]] * self._scale[0],
                self._calvector[self._transpose[1]] * self._scale[1],
                self._calvector[self._transpose[2]] * self._scale[2])

    @property
    def magnitude(self):
        x, y, z = self.xyz  # All measurements must correspond to the same instant
        return sqrt(x**2 + y**2 + z**2)

    @property
    def inclination(self):
        x, y, z = self.xyz
        return degrees(acos(z / sqrt(x**2 + y**2 + z**2)))

    @property
    def elevation(self):
        return 90 - self.inclination

    @property
    def azimuth(self):
        x, y, z = self.xyz
        return degrees(atan2(y, x))

    # Raw uncorrected integer values from sensor
    @property
    def ix(self):
        return self._ivector[0]

    @property
    def iy(self):
        return self._ivector[1]

    @property
    def iz(self):
        return self._ivector[2]

    @property
    def ixyz(self):
        return self._ivector

    @property
    def transpose(self):
        return tuple(self._transpose)

    @property
    def scale(self):
        return tuple(self._scale)



