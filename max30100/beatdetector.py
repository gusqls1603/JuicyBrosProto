import time

# Machine State Status
_BeatDetector___STATE_INIT = 0
_BeatDetector___STATE_WAITING = 1
_BeatDetector___STATE_SLOPE = 2
_BeatDetector___STATE_MAYBE_DETECTED = 3
_BeatDetector___STATE_MASKING = 4

# Constants
_BeatDetector___INIT_HOLDOFF              = 2000    # in ms, how long to wait before counting
_BeatDetector___MASKING_HOLDOFF           = 200     # in ms, non-retriggerable window after beat detection
_BeatDetector___BPFILTER_ALPHA            = 0.6     # EMA factor for the beat period value
_BeatDetector___MIN_THRESHOLD             = 20      # minimum threshold (filtered) value
_BeatDetector___MAX_THRESHOLD             = 800     # maximum threshold (filtered) value
_BeatDetector___STEP_RESILIENCY           = 30      # maximum negative jump that triggers the beat edge
_BeatDetector___THRESHOLD_FALLOFF_TARGET  = 0.3     # thr chasing factor of the max value when beat
_BeatDetector___THRESHOLD_DECAY_FACTOR    = 0.99    # thr chasing factor when no beat
_BeatDetector___INVALID_READOUT_DELAY     = 2000    # in ms, no-beat time to cause a reset
_BeatDetector___SAMPLES_PERIOD            = 10      # in ms, 1/Fs

class BeatDetector:

  def __init__(self):
    self.state = ___STATE_INIT
    self.threshold = ___MIN_THRESHOLD
    self.beatPeriod = 0
    self.lastMaxValue = 0
    self.tsLastBeat = 0
    self.startTime = time.time() * 1000

  def addSample(self, sample):
    beatDetected = False

    if self.state == ___STATE_INIT:
      if self.__getTimeDelta() > ___INIT_HOLDOFF:
        self.state = ___STATE_WAITING

    elif self.state == ___STATE_WAITING:
      if sample > self.threshold:
        self.threshold = min(sample, ___MAX_THRESHOLD)
        self.state = ___STATE_SLOPE

      # Tracking Lost, reset
      if self.__getTimeDelta() - self.tsLastBeat > ___INVALID_READOUT_DELAY:
        self.beatPeriod = 0
        lastMaxValue = 0

      self.__decreaseThreshold()

    elif self.state == ___STATE_SLOPE:
      if sample < self.threshold:
        self.state = ___STATE_MAYBE_DETECTED

      else:
        self.threshold = min(sample, ___MAX_THRESHOLD)

    elif self.state == ___STATE_MAYBE_DETECTED:
      if sample + ___STEP_RESILIENCY < self.threshold:
        # Found a beat
        beatDetected = True
        self.lastMaxValue = sample
        self.state = ___STATE_MASKING
        delta = self.__getTimeDelta() - self.tsLastBeat
        if delta:
          self.beatPeriod = ___BPFILTER_ALPHA * delta + ( 1 - ___BPFILTER_ALPHA) * self.beatPeriod

        self.tsLastBeat = self.__getTimeDelta()
      else:
        self.state = ___STATE_SLOPE

    elif self.state == ___STATE_MASKING:
      if self.__getTimeDelta() - self.tsLastBeat > ___MASKING_HOLDOFF:
        self.state = ___STATE_WAITING
      self.__decreaseThreshold()

    return beatDetected

  def getRate(self):
    return 1 / self.beatPeriod * 1000 * 60 if self.beatPeriod != 0 else 0

  def getCurrentThreshold(self):
    return self.threshold

  def __decreaseThreshold(self):
    # When a valid beat is available, target it.
    if self.lastMaxValue > 0 and self.beatPeriod > 0:
      self.threshold = self.threshold - self.lastMaxValue * ( 1 - ___THRESHOLD_FALLOFF_TARGET) / ( self.beatPeriod / ___SAMPLES_PERIOD)
    else:
      self.threshold = self.threshold * ___THRESHOLD_DECAY_FACTOR

    if self.threshold < ___MIN_THRESHOLD:
      self.threshold = ___MIN_THRESHOLD

  def __getTimeDelta(self):
    return time.time() * 1000 - self.startTime