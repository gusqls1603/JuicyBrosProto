#!/usr/bin/env python

import collections
import smbus
import struct

from max30100.constants import *

_MAX30100___BUFFER_SIZE            = 16
_MAX30100___DEFAULT_MODE           = MAX30100_MODE_HRONLY
_MAX30100___DEFAULT_SR             = MAX30100_SAMPRATE_100HZ
_MAX30100___DEFAULT_PWM            = MAX30100_PWM_1600US_16BITS
_MAX30100___DEFAULT_RED_CURRENT    = MAX30100_LED_CURR_50MA
_MAX30100___DEFAULT_IR_CURRENT     = MAX30100_LED_CURR_50MA

def __u2s__(data):
  return struct.unpack("<b", struct.pack("<B", data))[0]

class SensorData:
  def __init__(self, irData, redData):
    self.irData = irData
    self.redData = redData


class MAX30100:
  def __init__(self, port=0):
    self.buffer = collections.deque(maxlen=___BUFFER_SIZE)
    self.bus = smbus.SMBus(port)
    self.irData=0
    self.redData=0

  def begin(self):
    if self.getPartId() != MAX30100_PART_ID:
      return False

    self.setMode(___DEFAULT_MODE)
    self.setLedPWM(___DEFAULT_PWM)
    self.setSampleRate(___DEFAULT_SR)
    self.setLedsCurrent(___DEFAULT_IR_CURRENT, ___DEFAULT_RED_CURRENT)
    self.setHighResMode(True)

    return True

  def setMode(self, mode):
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION, mode)

  def setLedPWM(self, pwm):
    previous = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_SPO2_CONFIGURATION)
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_SPO2_CONFIGURATION, (previous & 0xFC) | pwm)

  def setSampleRate(self, sampleRate):
    previous = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_SPO2_CONFIGURATION)
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_SPO2_CONFIGURATION, (previous & 0xE3) | sampleRate << 2)

  def setLedsCurrent(self, irCurrent, redCurrent):
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_LED_CONFIGURATION, redCurrent << 4 | irCurrent)

  def setHighResMode(self, enabled=True):
    previous = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_SPO2_CONFIGURATION)
    flag = previous | MAX30100_SPO2_HI_RES_EN if enabled else previous & (~MAX30100_SPO2_HI_RES_EN & 0xFF)
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_SPO2_CONFIGURATION, flag)

  def __burstRead(self, addr, length):
    return self.bus.read_i2c_block_data(MAX30100_I2C_ADDRESS, addr, length)

  def update(self):
    writePointer = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_FIFO_WRITE_POINTER)
    readPointer = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_FIFO_READ_POINTER)
    toRead = (writePointer - readPointer) & (MAX30100_FIFO_DEPTH-1)
    

    if toRead:
      data = self.__burstRead(MAX30100_REG_FIFO_DATA, 4 * toRead)
      for i in range(toRead):
        self.buffer.append(SensorData(
          irData  = ((data[i*4 + 0] << 8) | data[i*4 + 1]),
          redData = ((data[i*4 + 2] << 8) | data[i*4 + 3])
        ))
        self.irData=(data[i*4 + 0] << 8) | data[i*4 + 1]
        self.redData=(data[i*4 + 2] << 8) | data[i*4 + 3]
  def getRawValues(self):
    if len(self.buffer) > 0:
      return self.buffer.pop()
    else:
      return None

  def resetFifo(self):
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_FIFO_WRITE_POINTER, 0)
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_FIFO_READ_POINTER, 0)
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_FIFO_OVERFLOW_COUNTER, 0)

  def startTemperatureSampling(self):
    modeConfig = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION)
    modeConfig = modeConfig | MAX30100_MC_TEMP_EN
    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION, modeConfig)

  def retrieveTemperature(self):
    intPart = __u2s__(self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_TEMPERATURE_DATA_INT))
    fracPart = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_TEMPERATURE_DATA_FRAC) / 16.0

    return intPart + fracPart

  def shutdown(self):
    modeConfig = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION)
    modeConfig = modeConfig | MAX30100_MC_SHDN

    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION, modeConfig)

  def resume(self):
    modeConfig = self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION)
    modeConfig = modeConfig & (~MAX30100_MC_SHDN & 0xFF)

    self.bus.write_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_MODE_CONFIGURATION, modeConfig)

  def getPartId(self):
    return self.bus.read_byte_data(MAX30100_I2C_ADDRESS, MAX30100_REG_PART_ID)