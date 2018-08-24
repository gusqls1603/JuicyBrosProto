import time

from max30100.constants import *

import max30100.max30100
import max30100.beatdetector
import max30100.spo2calculator

_Oxymeter___STATE_INIT = 0
_Oxymeter___STATE_IDLE = 1
_Oxymeter___STATE_DETECTING = 2

_Oxymeter___SAMPLING_FREQUENCY = 100
_Oxymeter___CURRENT_ADJUST_PERIOD = 500
_Oxymeter___DEFAULT_IR_LED_CURRENT = MAX30100_LED_CURR_50MA
_Oxymeter___RED_LED_CURRENT_START = MAX30100_LED_CURR_27_1MA

_Oxymeter___DC_REMOVER_ALPHA = 0.95


DEBUG_MODE_NONE = 0
DEBUG_MODE_RAW = 1
DEBUG_MODE_AC = 2
DEBUG_MODE_PULSE = 3

class LowPass:
  '''
  Fs = 100Hz, Fc = 6Hz, Order = 1, Alpha = 0.1 Butterworth
  '''
  def __init__(self):
    self.v = [0.0, 0.0]

  def step(self, x):
    self.v[0] = self.v[1]
    self.v[1] = (2.452372752527856026e-1 * x) + (0.50952544949442879485 * self.v[0]);

    return self.v[0] + self.v[1]


class DCRemover:
  def __init__(self, alpha=0):
    self.alpha = alpha
    self.dcw = 0

  def step(self, x):
    olddcw = self.dcw
    self.dcw = x + self.alpha * self.dcw
    return self.dcw - olddcw

  def getDCW(self):
    return self.dcw

class Oxymeter:
  def __init__(self, port=0):
    self.state = ___STATE_INIT
    self.tsFirstBeatDetected = 0
    self.tsLastBeatDetected = 0
    self.tsLastBiasCheck = 0
    self.tsLastCurrentAdjustment = 0
    self.redLedCurrent = ___RED_LED_CURRENT_START
    self.irLedCurrent = ___DEFAULT_IR_LED_CURRENT
    self.onBeatDetected = None
    self.sensor = max30100.MAX30100(port)
    self.spo2calculator = max30100.spo2calculator.SpO2Calculator()
    self.beatdetector = max30100.beatdetector.BeatDetector()
    self.lpf = LowPass()

  def begin(self, debugMode=DEBUG_MODE_NONE):
    self.debugMode = debugMode

    if not self.sensor.begin():
      if self.debugMode != DEBUG_MODE_NONE:
        print("Failed to initialize MAX30100 sensor")
      return False

    self.sensor.setMode(MAX30100_MODE_SPO2_HR)
    self.sensor.setLedsCurrent(self.irLedCurrent, self.redLedCurrent)


    self.irDCRemover = DCRemover(___DC_REMOVER_ALPHA)
    self.redDCRemover = DCRemover(___DC_REMOVER_ALPHA)

    self.state = ___STATE_IDLE

    return True

  def update(self):
    self.sensor.update()
    self.__checkSample__()
    self.__checkCurrentBias__()


  def getHeartRate(self):

    return self.beatdetector.getRate()

  def getSpO2(self):
    return self.spo2calculator.getSpO2()

  def onBeatDetected(self, cb):
    self.onBeatDetected = cb

  def shutdown(self):
    self.sensor.shutdown()

  def resume(self):
    self.sensor.resume()

  def setIRLedCurrent(self, irLedCurrent):
    self.irLedCurrent = irLedCurrent
    self.sensor.setLedsCurrent(self.irLedCurrent, self.redLedCurrent)

  def __checkSample__(self):
    sample = self.sensor.getRawValues()


    while sample != None:
      irACValue = self.irDCRemover.step(sample.irData)
      redACValue = self.redDCRemover.step(sample.redData)


      filteredPulseValue = self.lpf.step(-irACValue)
      beatDetected = self.beatdetector.addSample(filteredPulseValue)

      if self.beatdetector.getRate() > 0:
        self.state = ___STATE_DETECTING
        self.spo2calculator.update(irACValue, redACValue, beatDetected)
      elif self.state == ___STATE_DETECTING:
        self.state = ___STATE_IDLE
        self.spo2calculator.reset()

      if self.debugMode == DEBUG_MODE_RAW:
        print("RAW: R(%s) IR(%s)" %(sample.redData, sample.irData))
      elif self.debugMode == DEBUG_MODE_AC:
        print("AC: R(%s) IR(%s)" %(redACValue, irACValue))
      elif self.debugMode == DEBUG_MODE_PULSE:
        print("PULSE: FilteredPulseValue(%s) BeatDetectorThreshold(%s)" %(filteredPulseValue, self.beatdetector.getCurrentThreshold()))

      if beatDetected and self.onBeatDetected != None:
        self.onBeatDetected()

      sample = self.sensor.getRawValues()

  def __checkCurrentBias__(self):
    if time.time() * 1000 - self.tsLastBiasCheck > ___CURRENT_ADJUST_PERIOD/2:
      changed = False
      if self.irDCRemover.getDCW() - self.redDCRemover.getDCW() > 70000 and self.redLedCurrent < MAX30100_LED_CURR_50MA:
        self.redLedCurrent = self.redLedCurrent + 1
        changed = True
      elif self.redDCRemover.getDCW() - self.irDCRemover.getDCW() > 70000 and self.redLedCurrent > 0:
        self.redLedCurrent = self.redLedCurrent - 1
        changed = True

      if changed:
        self.sensor.setLedsCurrent(self.irLedCurrent, self.redLedCurrent)
        self.tsLastCurrentAdjustment = time.time() * 1000

        if self.debugMode != DEBUG_MODE_NONE:
          print("R I(%s)" % self.redLedCurrent)

      self.tsLastBiasCheck = time.time() * 1000