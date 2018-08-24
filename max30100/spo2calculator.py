#!/usr/bin/env python

import math

_SpO2Calculator___CALCULATE_EVERY_N_BEATS = 1
_SpO2Calculator___SPO2LUT = [100,100,100,100,99,99,99,99,99,99,98,98,98,98,
                             98,97,97,97,97,97,97,96,96,96,96,96,96,95,95,
                             95,95,95,95,94,94,94,94,94,93,93,93,93,93,93,93,
                             92,92,92,92,91,91,90,90,90,90,89,89,89,89,88,87]

class SpO2Calculator:
  def __init__(self):
    self.spO2 = 0
    self.reset()
  def update(self, irValue, redValue, beatDetected):
    self.irValueSqSum = self.irValueSqSum + irValue * irValue
    self.redValueSqSum = self.redValueSqSum + redValue * redValue
    self.samplesRecorded = self.samplesRecorded + 1

    if beatDetected:
      self.beatsDetectedNum = self.beatsDetectedNum + 1

      if self.beatsDetectedNum == ___CALCULATE_EVERY_N_BEATS:
        acSqRatio = 100.0 * math.log(self.redValueSqSum / self.samplesRecorded) / math.log(self.irValueSqSum / self.samplesRecorded)
        index = 0
        
        index = int(acSqRatio - 66 if acSqRatio > 66 else acSqRatio - 50)
        
        if(index > 60 or index<0):
            index = 24
        
        self.reset()
        try:
          self.spO2 = ___SPO2LUT[index]
        except Exception as e:
          print(e)
          print(index)


  def reset(self):
    self.irValueSqSum = 0
    self.redValueSqSum = 0
    self.beatsDetectedNum = 0
    self.samplesRecorded = 0

  def getSpO2(self):
    return self.spO2
