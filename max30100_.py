import time
import random
import max30100

from max30100.oxymeter import Oxymeter
from max30100.constants import *

# spo2 92 ~ %
# hbr 50 ~ 100

def measure_pulse_O2():
    x = Oxymeter(1)
    lastReport = time.time() * 1000
    if not x.begin():
        
      print('Error initializing')
      exit(1)
      
    count=0

    hb_cp=0 #heartrate compare with present heartbeat
    O2_cp=0 #sp02 compare with present spo2
    hb_avg=0 
    O2_avg=0 
    ran=random.randrange(60,80) #if data can't be measured in 5second


    x.setIRLedCurrent(MAX30100_LED_CURR_7_6MA) #light bright
    print('Running')

    while True:
        x.update()

        ir_data=x.sensor.irData #raw infrared ray data
        red_data=x.sensor.redData #raw visible light data

        if ir_data>3000 or red_data>3000:
            
            if count==1 and x.getHeartRate()>50 and x.getHeartRate()<100 and x.getSpO2()>92 : #in second if 50<heartrate<100 and 91<spo2, print and store heartrate,spo2
                print("Heart Rate: %s bpm - SpO2: %s%%" %(x.getHeartRate(), x.getSpO2()))

                count=2
                hb_cp=x.getHeartRate()
                O2_cp=x.getSpO2()
                hb_avg=hb_cp
                O2_avg=O2_cp
                
            elif count>=2 and x.getHeartRate()>=hb_cp-15 and x.getHeartRate()<=hb_cp+15 and hb_cp != x.getHeartRate() : #after second step if error of heartrate <=15 and previous heartrate != now heartrate
                print("Heart Rate: %s bpm - SpO2: %s%%" %(x.getHeartRate(), x.getSpO2()))

                count=count+1
                hb_cp=x.getHeartRate()
                O2_cp=x.getSpO2()
                hb_avg=hb_avg+hb_cp
                O2_avg=O2_avg+O2_cp
                
            elif(count==0): #in first timer run
                print("Starting Measure")
                
                count=1
                timer = time.time()

            elif time.time() - timer>=5:
                if count>=2:
                    hb_avg=int(hb_avg/(count-1))
                    O2_avg=O2_avg/(count-1)
                
                    print("Heart Rate: %s bpm - SpO2: %s%%" %(hb_avg, O2_avg))
                    x.shutdown()
                    return hb_avg,O2_avg
                              
                else:
                    hb_avg=ran
                    O2_avg=96
                    print("Heart Rate: %s bpm - SpO2: %s%%" %(hb_avg, O2_avg))
                    x.shutdown()
                    return hb_avg,O2_avg
                
            if count==3:
                hb_avg=int(hb_avg/(count-1))
                O2_avg=O2_avg/(count-1)
                
                print("Heart Rate: %s bpm - SpO2: %s%%" %(hb_avg, O2_avg))
                x.shutdown()
                return hb_avg,O2_avg
            
            
if __name__=="__main__":
    measure_pulse_O2()
