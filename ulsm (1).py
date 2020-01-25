#!/usr/local/bin/python

import RPi.GPIO as GPIO
import time
import smtplib
import math
import smbus
from datetime import datetime
from lcd import lcd
import imaplib

#GPIO.cleanup()

sent = 1
warnings = 3
runs = 0

#subject = 'Security Notice! (Pi)'
#header = 'To: ' + brandon.w.ngo@gmail.com + '\nFrom: ' + brandon.w.ngo@gmail.com + '\nSubject' + subject
subject = 'Project Email'
#message = 'From Raspberry Pi: Security Compromised ' + str(sent)

GPIO.setmode(GPIO.BOARD)

#define the pin that goes to the circuit
pin_to_circuit = 37
PIN_TRIGGER = 7
PIN_ECHO = 11

address = 0x48 
bus=smbus.SMBus(1) 
cmd=0x40
chn = 0

def rc_time (pin_to_circuit):
    count = 0
  
    #Output on the pin for 
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)

    #Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)
  
    #Count until the pin goes high
    while (GPIO.input(pin_to_circuit) == GPIO.LOW):
        count += 1
    return count

def distanceIN (PIN_TRIGGER, PIN_ECHO):
    stopecho = 0
    pulse_end_time = 0
    pulse_start_time = 0
    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)

    GPIO.output(PIN_TRIGGER, GPIO.LOW)
    print "Waiting for sensor to settle"
    time.sleep(2)

    GPIO.output(PIN_TRIGGER, GPIO.HIGH)
 
    time.sleep(0.00001)

    GPIO.output(PIN_TRIGGER, GPIO.LOW)
    print 2
    while GPIO.input(PIN_ECHO)==0:
        pulse_start_time = time.time()
        stopecho = stopecho + 1
        #print stopecho
        if stopecho > 10:
            break
    print 3
    stopecho = 0
    while GPIO.input(PIN_ECHO)==1:
        pulse_end_time = time.time()
        stopecho = stopecho + 1
        if stopecho > 10:
            break
    #if stopecho>10:
        #pulse_end_time = pulse_start_time
    print 4
    #print pulse_end_time
    #print pulse_start_time
    pulse_duration = pulse_end_time - pulse_start_time
    distance = round(pulse_duration * 17150 * 0.3937, 8)
    if distance < 0:
        return 60
    return distance

trigPin = 16
echoPin = 18
MAX_DISTANCE = 220          #define the maximum measured distance
timeOut = MAX_DISTANCE*60   #calculate timeout according to the maximum measured distance



def pulseIn(pin,level,timeOut): # function pulseIn: obtain pulse time of a pin
   t0 = time.time()
   while(GPIO.input(pin) != level):
       if((time.time() - t0) > timeOut*0.000001):
           return 0;
   t0 = time.time()
   while(GPIO.input(pin) == level):
       if((time.time() - t0) > timeOut*0.000001):
           return 0;
   pulseTime = (time.time() - t0)*1000000
   return pulseTime
  
def getSonar():     #get the measurement results of ultrasonic module,with unit: cm
   GPIO.output(trigPin,GPIO.HIGH)      #make trigPin send 10us high level
   time.sleep(0.00001)     #10us
   GPIO.output(trigPin,GPIO.LOW)
   pingTime = pulseIn(echoPin,GPIO.HIGH,timeOut)   #read plus time of echoPin
   distance = pingTime * 340.0 / 2.0 / 10000.0     # the sound speed is 340m/s, and calculate distance
   return distance

def getDistanceIn():
   GPIO.setup(trigPin, GPIO.OUT)   #
   GPIO.setup(echoPin, GPIO.IN)
   GPIO.setup(11,GPIO.IN)
   distance = getSonar() * 0.3937    #multiply to get inches
   time.sleep(1)
   return distance

def send_email(subject, message):
    try:
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.login('brandon.w.ngo@gmail.com', 'GuySolo721')
        print 'login success'
        message = 'Subject: {}\n\n{}'.format(subject,message)
        s.sendmail('brandon.w.ngo@gmail.com', 'brandon.w.ngo@gmail.com', message)
        s.quit()
        print 'email sent'
    except:
        print 'email failed to send'

def read_email():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('brandon.w.ngo@gmail.com', 'GuySolo721')
    mail.list()
    # Out: list of "folders" aka labels in gmail.
    mail.select("inbox") # connect to inbox.
    result, data = mail.search(None, "ALL")

    ids = data[0] # data is a list.
    id_list = ids.split() # ids is a space separated string
    latest_email_id = id_list[-1] # get the latest

    # fetch the email body (RFC822) for the given ID
    result, data = mail.fetch(latest_email_id, "(RFC822)") 

    raw_email = data[0][1] # here's the body, which is raw text of the whole email
    # including headers and alternate payloads

    print raw_email
    print mail.search( None, '(BODY "Compromised")')[1]
    index = mail.search( None, '(BODY "Compromised")')[1]
    print index[0]
    
def temp():
    value = bus.read_byte_data(address,cmd+chn)
    voltage = value / 255.0 * 3.3 #calculate voltage
    Rt = 10 * voltage / (3.3 - voltage) #calculate resistance value of thermistor 
    tempK = 1/(1/(273.15 + 25) + math.log(Rt/10)/3950.0) #calculate temperature (Kelvin) 
    tempC = tempK -273.15 #calculate temperature (Celsius)
    tempF = 1.8 * (tempK -273 ) + 32
    tempF = round(tempF, 1)
    #print 'ADC Value : %d, Voltage : %.2f, Temperature : %.2f'%(value,voltage,tempC)
    #time.sleep(0.0 1)
    return tempF

def switchB():
    GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    return GPIO.input(13)

mode = 0
switches = 0
#Catch when script is interupted, cleanup correctly
#light > 20000 equals dark
#distance < 20in then movement
try:
    # Main loop
    while True:
        runs = 0
        sent = 1
        #security mode
        while (mode == 1 & (runs < 10)):
            lcd.lcd_display_string(lcd(), 'Security Mode',1)
            message = 'From Raspberry Pi: Security Compromised ' + str(sent)
            light = rc_time(pin_to_circuit)
            if light > 20000:
                lightprint = 'It is dark'
            else:
                lightprint = 'Light has been shown'
            #distance = distanceIN(PIN_TRIGGER, PIN_ECHO)
            #setup()
            distance = getDistanceIn()
            
            print "Light:", light, ' ',lightprint
            print "Distance:",distance,"in"
            #for movement or light send email
            if(light < 20000 or int(distance) < 20):
                if light < 20000:
                    print 'light detected'
                    lcd.lcd_display_string(lcd(), 'light detected',1)
                    time.sleep(.5)
                    lcd.lcd_display_string(lcd(), 'Email Sent',1)
                elif int(distance) < 20:
                    print 'movement detected'
                    lcd.lcd_display_string(lcd(), 'movement detected',1)
                    time.sleep(.5)
                    lcd.lcd_display_string(lcd(), 'Email Sent',1)
                if sent < (warnings + 1):
                    send_email(subject,message)
                    lcd.lcd_display_string(lcd(), 'Email Sent',1)
                    sent = sent + 1
            runs = runs + 1
            print runs, '\n'
            if switchB():
                mode = 0
                switches = switches + 1
                
        #normal mode        
        while (mode == 0 & (runs < 10)):
            print 'Temp: ', temp(), ' F'
            print datetime.now()
            lcd.lcd_display_string(lcd(),str(datetime.now()),1)
            time.sleep(1)
            lcd.lcd_display_string(lcd(),'Temp: ' + str(temp()) + ' F',2)
            time.sleep(1)
            runs = runs + 1
            print runs
            if switchB():
                mode = 1
                switches = switches + 1

                
except KeyboardInterrupt:
    GPIO.cleanup()
finally:
    GPIO.cleanup()

