import RPi.GPIO as GPIO
import DHT11.dht11
import time
import datetime

def measure_tem_humi():
    # initialize GPIO

    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)

    # read data using pin 21
    instance = DHT11.dht11.DHT11(pin=21)

    while True:
        result = instance.read()
        if result.is_valid():
            print("Last valid input: " + str(datetime.datetime.now()))
            print("Temperature: %d C" % result.temperature)
            print("Humidity: %d %%" % result.humidity)
                      
            return result.temperature,result.humidity


if __name__=="__main__":
    measure_tem_humi()
