#Sammy Door for Raspberry Pi!
#steve.a.mccluskey@gmail.com
#
# pin layout:
# 01) 3.3v
# 02) 5v
# 03) GPIO 2 -> I2C SDA
# 04) 5v
# 05) GPIO 3 -> I2C SCL
# 06) GND
# 07) GPIO 4 -> OneWire Bus
# 08) GPIO14 -> UART TXT
# 09) GND
# 10) GPIO15 -> UART RXD
# 11) GPIO17 -> motion sensor
# 12) GPIO18 -> doorServo
# 13) GPIO27 -> lockServo
# 14) GND
# 15) GPIO22 -> breakBeamSensor
# 16) GPIO23 -> magnetic door sensor
# 17) 3.3v
# 18) GPIO24 ->
# 19) GPIO10 -> SPI MOSI
# 20) GND
#
# 21) GPIO 9 -> SPI MISO
# 22) GPIO25
# 23) GPIO11 -> SPI SCLK
# 24) GPIO 8 -> SPI CE0
# 25) GND
# 26) GPIO 7 -> SPI CE1
# 27) ID SD  -> I2C BUS6 SDA
# 28) ID SC  -> I2C BUS6 SCL
# 29) GPIO 5
# 30) GND
# 31) GPIO 6
# 32) GPIO12
# 33) GPIO13
# 34) GND
# 35) GPIO19 -> PCM FS
# 36) GPIO16
# 37) GPIO26 -> N.C.
# 38) GPIO20 -> PCM DIN
# 39) GND
# 40) GPIO21 -> PCM DOUT

from typing import AnyStr
import board
import bitbangio
import busio
import busio2
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import RPi.GPIO as GPIO
from board import *
import digitalio
import time
from time import sleep
import mb_24x256_512_CP
import asyncio
import pigpio
from flask import Flask
from flask import request
from flask_cors import CORS
import atexit
import threading
import os
import logging

####################################################
#lcd setup:
lcd_columns = 16
lcd_rows = 2

i2c = busio.I2C(board.SCL, board.SDA)
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

white = [100, 100, 100]
green = [0, 100, 0]
red = [100, 0, 0]
blue = [0, 0, 100]
purple = [100, 0, 100]
yellow = [100, 100, 0]

#############################################
#eeprom setup:
i2c6 = busio2.I2C(1, 0, frequency = 100000)
time.sleep(.01)
i2c6.try_lock()
time.sleep(.01)
i2c_address = i2c6.scan()
EEPROM_DEVICE = "24x256"
memory = mb_24x256_512_CP.mb_24x256_512_CP(i2c6, i2c_address, EEPROM_DEVICE)

#############################################################
#pin assignment stuff:
doorServo = 18
lockServo = 27
breakBeamSensor = 22
motionSensor = 17
magneticDoorSensor = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(breakBeamSensor, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(motionSensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(magneticDoorSensor, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#servos:
pwm = pigpio.pi()
pwm.set_mode(doorServo, pigpio.OUTPUT)
pwm.set_mode(lockServo, pigpio.OUTPUT)

pwm.set_PWM_frequency(doorServo, 0)
pwm.set_PWM_frequency(lockServo, 0)

#########################################
#eeprom addresses and get values:
doorOpenPosEEP         = 10
doorClosedPosEEP       = 11
lockOpenPosEEP         = 12
lockClosedPosEEP       = 13
motionSensorTimeoutEEP = 14
beamSensorTimeoutEEP   = 15
doorOpenHoldTimeEEP    = 16
menuEEP                = 17
lockInEnabledEEP       = 18
lockTimeoutTimeEEP     = 19

doorOpenPosition   = memory.read_byte(doorOpenPosEEP)
doorClosedPosition = memory.read_byte(doorClosedPosEEP)
lockOpenPosition   = memory.read_byte(lockOpenPosEEP)
lockClosedPosition = memory.read_byte(lockClosedPosEEP)

#delay variables:
motionSensorTimeoutTime = memory.read_byte(motionSensorTimeoutEEP)
beamSensorTimeoutTime   = memory.read_byte(beamSensorTimeoutEEP)
doorOpenHoldTimeoutTime = memory.read_byte(doorOpenHoldTimeEEP)
lockTimeoutTime         = memory.read_byte(lockTimeoutTimeEEP)

if (memory.read_byte(lockInEnabledEEP) == 1):
    lockInEnabled = True
else:
    lockInEnabled = False

menu = memory.read_byte(menuEEP)
menu_limit = 9

#inputs states:
motionState = 0
beamState   = 0
doorState   = 0

#output statuses:
lockStatus = 0
doorStatus = 0

#set times to current time:
doorOpenTime    = time.time()
doorCloseTime   = time.time()
lockOpenTime    = time.time()
lockCloseTime   = time.time()
motionStartTime = time.time()
motionStopTime  = time.time()
beamStartTime   = time.time()
beamStopTime    = time.time()

###########################################
#webserver stuff:

app = Flask(__name__)
CORS(app)
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR) #loggin to console disabled

#####################################################
#check buttons and update accordingly
def readButtons():
    global doorState
    global motionState
    global beamState
    global menu
    global lockTimeoutTime
    global lockInEnabled

    #print("reading buttons")
    while True:
        if (not lockInEnabled):
            if (motionState):
                lcd.color = yellow
            elif (beamState):
                lcd.color = blue
            elif (doorState):
                lcd.color = green
            else:
                lcd.color = white
        elif (lockInEnabled):
            lcd.color = red

        if lcd.up_button:
            print("up button pressed ************************")
            #main menu:
            if (menu == 1):
                print("")

            #door servo open pos:
            elif (menu == 2):
                doorOpenPos(2)

            #door servo closed position:
            elif (menu == 3):
                doorClosedPos(2)

            #lock servo open position:
            elif (menu == 4):
                lockOpenPos(2)

            #lock servo closed position:
            elif (menu == 5):
                lockClosedPos(2)

            #increase motion sensor timeout:
            elif (menu == 6):
                motionSensorTimeout(1)

            #increase beam sensor timeout:
            elif (menu == 7):
                beamSensorTimeout(1)

            #increase door open hold time:
            elif (menu == 8):
                doorOpenHoldTimeout(1)

            #increase lock delay:
            elif (menu == 9):
                lockTimeout(1)

            updateScreen()

        elif lcd.down_button:
            print("down button pressed ************************")
            #main menu
            if (menu == 1):
                print("")

            #door servo open position:
            elif (menu == 2):
                doorOpenPos(-2)

            #door servo closed position:
            elif (menu == 3):
                doorClosedPos(-2)

            #lock servo open position:
            elif (menu == 4):
                lockOpenPos(-2)

            #lock servo closed position:
            elif (menu == 5):
                lockClosedPos(-2)

            #decrease motion sensor timeout:
            elif (menu == 6):
                motionSensorTimeout(-1)

            #decrease beam sensor timeout:
            elif (menu == 7):
                beamSensorTimeout(-1)

            #decrease door open hold timeout:
            elif (menu == 8):
                doorOpenHoldTimeout(-1)

            #decrease lock delay:
            elif (menu == 9):
                lockTimeout(-1)

            updateScreen()

        elif lcd.right_button:
            print("right button pressed ************************")
            menu = menu + 1
            if (menu > menu_limit):
                menu = 1
            memory.write_byte(menuEEP, menu)
            updateScreen()

        elif lcd.left_button:
            print("left button pressed ************************")
            menu = menu - 1
            if (menu < 1):
                menu = menu_limit
            memory.write_byte(menuEEP, menu)
            updateScreen()

        elif lcd.select_button:
            print("select button pressed ************************")
            if (lockInEnabled):
                lockInEnabled = False
                memory.write_byte(lockInEnabledEEP, 0)
            elif (lockInEnabled == False):
                lockInEnabled = True
                memory.write_byte(lockInEnabledEEP, 1)
            print("lockIn enabled = " + str(lockInEnabled))
            updateScreen()

        else:
            time.sleep(.01)
#end read buttions

##########################
#door/lock open/close commands:
def actuateDoor(direction):
    global doorOpenPosition
    global doorClosedPosition
    global doorStatus

    if (direction == 1):
        pwm.set_PWM_frequency(doorServo, 50)
        pwm.set_servo_pulsewidth(doorServo, degreesToPwm(doorOpenPosition))
        pwm.set_PWM_frequency(doorServo, 0)
        doorStatus = 1
        # print("door status: OPEN.")
    elif (direction == 0):
        pwm.set_PWM_frequency(doorServo, 50)
        pwm.set_servo_pulsewidth(doorServo, degreesToPwm(doorClosedPosition))
        pwm.set_PWM_frequency(doorServo, 0)
        doorStatus = 0
        # print("door status: CLOSED.")

def actuateLock(direction):
    global lockOpenPosition
    global lockClosedPosition
    global lockStatus
    if (direction == 1):
        pwm.set_PWM_frequency(lockServo, 50)
        pwm.set_servo_pulsewidth(lockServo, degreesToPwm(lockOpenPosition))
        pwm.set_PWM_frequency(lockServo, 0)
        lockStatus = 1
        # print("lock status: LOCKED.")
    elif (direction == 0):
        pwm.set_PWM_frequency(lockServo, 50)
        pwm.set_servo_pulsewidth(lockServo, degreesToPwm(lockClosedPosition))
        pwm.set_PWM_frequency(lockServo, 0)
        lockStatus = 0
        # print("lock status: UNLOCKED.")

################################################
#read digital IO:
def readDoorSensor():
    global doorState
    if(GPIO.input(magneticDoorSensor) == GPIO.HIGH):
        doorState = 1
    else:
        doorState = 0

def readBeamSensor():
    global beamState
    if(GPIO.input(breakBeamSensor) == GPIO.LOW):
        beamState = 1
    else:
        beamState = 0

def readMotionSensor():
    global motionState
    if(GPIO.input(motionSensor) == GPIO.HIGH):
        motionState = 1
    else:
        motionState = 0

#records time that sensor inputs change states:
def motionSensorInterrupt(motionSensor):
    global motionStartTime
    global motionStopTime
    global motionState
    sleep(.005)
    if GPIO.input(motionSensor) == 1:
        motionStartTime = time.time()
        print("motion detected @ " + str(motionStartTime))
        motionState = 1
    else:
        motionStopTime = time.time()
        print("motion stopped @ " + str(motionStopTime))
        motionState = 0

def beamSensorInterrupt(motionSensor):
    global beamStartTime
    global beamStopTime
    global beamState
    sleep(.005)
    if GPIO.input(breakBeamSensor) == 0:
        beamStartTime = time.time()
        print("beam detected @ " + str(beamStartTime))
        beamState = 1
    else:
        beamStopTime = time.time()
        print("beam stopped @ " + str(beamStopTime))
        beamState = 0
#end read digital IO

#converts angle parameters to PWM:
def degreesToPwm(degree):
    return int((degree) * (2000) / (180) + 500)

########################################
#screen update
def updateScreen():
    global doorOpenPosition
    global doorClosedPosition
    global lockOpenPosition
    global lockClosedPosition
    global menu
    global beamSensorTimeoutTime
    global motionSensorTimeoutTime
    global doorOpenHoldTimeoutTime
    global lockTimeoutTime

    lcdString = ""
    #top row:
    print("writing screen")

    #home menu:
    if (menu == 1):
        lcdString = "Status: OK          \nM" + str(menu) + ": "
        if (lockInEnabled):
            lcdString += "Locked In!    "
        else:
            lcdString += "Unlocked.     "

    #edit door open position:
    elif (menu == 2):
        lcdString = "Door Open Pos:   \nM" + str(menu) +  ": "
        if (doorOpenPosition < 10):
            lcdString += "00"
        elif (doorOpenPosition < 100):
            lcdString += "0"
        lcdString += str(doorOpenPosition) + " degrees   "

    #edit door closed position:
    elif (menu == 3):
        lcdString = "Door Closed Pos:      \nM" + str(menu) +  ": "
        if (doorClosedPosition < 10):
                lcdString += "00"
        elif (doorClosedPosition < 100):
            lcdString += "0"
        lcdString += str(doorClosedPosition) + " degrees    "

    #edit lock open position:
    elif (menu == 4):
        lcdString = "Lock Open Pos:        \nM" + str(menu) +  ": "
        if (lockOpenPosition < 10):
            lcdString += "00"
        elif (lockOpenPosition < 100):
            lcdString += "0"
        lcdString += str(lockOpenPosition) + " degrees   "

    #edit lock closed position:
    elif (menu == 5):
        lcdString = "Lock Closed Pos:      \nM" + str(menu) +  ": "
        if (lockClosedPosition < 10):
            lcdString += "00"
        elif (lockClosedPosition < 100):
            lcdString += "0"
        lcdString += str(lockClosedPosition) + " degrees   "

    #edit motion sensor trigger timeout:
    elif (menu == 6):
        lcdString = "Motion Timeout:   \nM" + str(menu) +  ": "
        if (motionSensorTimeoutTime < 10):
            lcdString += "0"
        lcdString += str(motionSensorTimeoutTime) + " seconds    "

    #edit beam sensor trigger timeout:
    elif (menu == 7):
        lcdString = "Beam Timeout:   \nM" + str(menu) +  ": "
        if (beamSensorTimeoutTime < 10):
            lcdString += "0"
        lcdString += str(beamSensorTimeoutTime) + " seconds  "

    #edit door open hold time:
    elif (menu == 8):
        lcdString = "Door Open Time:   \nM" + str(menu) +  ": "
        if (doorOpenHoldTimeoutTime < 10):
                lcdString += "0"
        lcdString += str(doorOpenHoldTimeoutTime) + " seconds  "

    elif (menu == 9):
        lcdString = "Lock Delay:     \nM" + str(menu) +  ": "
        if (lockTimeoutTime < 10):
                lcdString += "0"
        lcdString += str(lockTimeoutTime) + " seconds  "

    lcd.message = lcdString
#end update screen

######################################################################
# update system variables and save to eeprom:

#door open position:
def doorOpenPos(angle):
    global doorOpenPosition
    doorOpenPosition = doorOpenPosition + angle
    if (doorOpenPosition > 180):
        doorOpenPosition = 180
    if (doorOpenPosition < 0):
        doorOpenPosition = 0
    memory.write_byte(doorOpenPosEEP, doorOpenPosition)
    print("door open position: " + str(doorOpenPosition) + " degrees.")

#door closed position:
def doorClosedPos(angle):
    global doorClosedPosition
    doorClosedPosition = doorClosedPosition + angle
    if (doorClosedPosition > 180):
        doorClosedPosition = 180
    if (doorClosedPosition < 0):
        doorClosedPosition = 0
    memory.write_byte(doorClosedPosEEP, doorClosedPosition)
    print("door closed position: " + str(doorClosedPosition) + " degrees.")

#lock open position:
def lockOpenPos(angle):
    global lockOpenPosition
    lockOpenPosition = lockOpenPosition + angle
    if (lockOpenPosition > 180):
        lockOpenPosition = 180
    if (lockOpenPosition < 0):
        lockOpenPosition = 0
    memory.write_byte(lockOpenPosEEP, lockOpenPosition)
    print("lock open position: " + str(lockOpenPosition) + " degrees.")

#lock closed position:
def lockClosedPos(angle):
    global lockClosedPosition
    lockClosedPosition = lockClosedPosition + angle
    if (lockClosedPosition > 180):
        lockClosedPosition = 180
    if (lockClosedPosition < 0):
        lockClosedPosition = 0
    memory.write_byte(lockClosedPosEEP, lockClosedPosition)
    print("lock closed position: " + str(lockClosedPosition) + " degrees.")

#motion sensor timeout:
def motionSensorTimeout(second):
    global motionSensorTimeoutTime
    motionSensorTimeoutTime = motionSensorTimeoutTime + second
    if (motionSensorTimeoutTime > 10):
        motionSensorTimeoutTime = 10
    if (motionSensorTimeoutTime < 0):
        motionSensorTimeoutTime = 0
    memory.write_byte(motionSensorTimeoutEEP, motionSensorTimeoutTime)
    print("motion sensor time out: " + str(motionSensorTimeoutTime) + " seconds.")

#beam sensor timeout:
def beamSensorTimeout(second):
    global beamSensorTimeoutTime
    beamSensorTimeoutTime = beamSensorTimeoutTime + second
    if (beamSensorTimeoutTime > 10):
        beamSensorTimeoutTime = 10
    if (beamSensorTimeoutTime < 0):
        beamSensorTimeoutTime = 0
    memory.write_byte(beamSensorTimeoutEEP, beamSensorTimeoutTime)
    print("beam sensor time out: " + str(beamSensorTimeoutTime) + " seconds.")

#door open hold time:
def doorOpenHoldTimeout(second):
    global doorOpenHoldTimeoutTime
    doorOpenHoldTimeoutTime = doorOpenHoldTimeoutTime + second
    if (doorOpenHoldTimeoutTime > 10):
        doorOpenHoldTimeoutTime = 10
    if (doorOpenHoldTimeoutTime < 0):
        doorOpenHoldTimeoutTime = 0
    memory.write_byte(doorOpenHoldTimeEEP, doorOpenHoldTimeoutTime)
    print("door open hold time: " + str(doorOpenHoldTimeoutTime) + " seconds.")

#lock delay:
def lockTimeout(second):
    global lockTimeoutTime
    lockTimeoutTime = lockTimeoutTime + second
    if (lockTimeoutTime > 10):
        lockTimeoutTime = 10
    if (lockTimeoutTime < 0):
        lockTimeoutTime = 0
    memory.write_byte(lockTimeoutTimeEEP, lockTimeoutTime)
    print("lock time out time: " + str(lockTimeoutTime) + " seconds.")

##############################
#main event loop:
def mainLoop():
    global beamState
    global motionState
    global doorState
    global doorStatus
    global lockStatus
    global motionSensorTimeoutTime
    global beamSensorTimeoutTime
    global doorOpenHoldTimeoutTime
    global lockTimeoutTime

    global doorOpenTime
    global doorCloseTime
    global lockOpenTime
    global lockCloseTime
    global motionStartTime
    global motionStopTime
    global beamStartTime
    global beamStopTime

    global lockInEnabled

    while True:
        # readMotionSensor()
        # readBeamSensor()
        readDoorSensor()

        if (lockInEnabled):
            if (beamState == 0 and motionState == 0 and doorState == 0 and doorStatus == 0):
                actuateLock(1)

            if (beamState == 1):
                if ((time.time() - beamStartTime) > beamSensorTimeoutTime):
                    if (lockStatus == 1):
                        actuateLock(0)
                        time.sleep(beamSensorTimeoutTime)
                    actuateDoor(1)

            elif (beamState == 0):
                if ((time.time() - beamStopTime) > beamSensorTimeoutTime):
                    doorOpenTime = (beamStopTime + beamSensorTimeoutTime)
                    if ((time.time() - doorOpenTime ) > doorOpenHoldTimeoutTime):
                        actuateDoor(0)
                        doorCloseTime = doorOpenTime + beamStopTime + doorOpenHoldTimeoutTime
                        time.sleep(lockTimeoutTime)
                        actuateLock(1)

        if (not lockInEnabled):
            actuateLock(0)
            if (beamState == 1):
                if ((time.time() - beamStartTime) > beamSensorTimeoutTime):
                    actuateDoor(1)

            elif (motionState == 1):
                if ((time.time() - motionStartTime) > motionSensorTimeoutTime):
                    actuateDoor(1)

            elif (motionState == 0 and beamState == 0):
                if (beamStopTime > motionStopTime): #going outside, beam sensor goes low later than motion
                    if ((time.time() - beamStopTime) > beamSensorTimeoutTime):
                        doorOpenTime = (beamStopTime + beamSensorTimeoutTime)
                        if ((time.time() - doorOpenTime ) > doorOpenHoldTimeoutTime):
                            actuateDoor(0)

                elif (motionStopTime > beamStopTime): #coming in, motion goes low later than beam
                    if ((time.time() - motionStopTime) > motionSensorTimeoutTime):
                        doorOpenTime = (motionStopTime + motionSensorTimeoutTime)
                        if ((time.time() - doorOpenTime ) > doorOpenHoldTimeoutTime):
                            actuateDoor(0)

######################################
#server code:
@app.route("/lockIn")
def remoteLockin():
    global lockInEnabled
    lockRequest = request.args.get("enable")

    if (lockRequest == "enable"):
        lockInEnabled = True

    elif (lockRequest == "disable"):
        lockInEnabled = False

    returnString = "recieved : " + str(lockRequest) + " command"
    print (returnString)
    return returnString

@app.route("/getStatus")
def getStatusRequest():
    global lockInEnabled
    global doorStatus
    global lockStatus
    statusString = '{"status" : [{"doorState": '
    if (doorState == 1):
        statusString += '1, '
    else:
        statusString += '0, '
    statusString +='"doorStatus": ' 
    if (doorStatus == 1):
        statusString += '1, '
    else:
        statusString += '0, '
    statusString += '"lockStatus": '
    if (lockStatus == 1):
        statusString += '1, '
    else:
        statusString += '0, '
    statusString += '"lockIn": '
    if (lockInEnabled == True):
        statusString += '1, '
    else:
        statusString += '0, '
    statusString += '"timeStamp": '
    statusString += str(time.time())
    statusString += '}]}'
    print(statusString)
    return statusString

################################
#program start:
lcd.clear()
lcd.color = white
lcd.message = "SammyDoor\nin Python v1.0"
time.sleep(2)
lcd.clear()
print("starting server.")
updateScreen() #write screen upon startup

GPIO.add_event_detect(motionSensor, GPIO.BOTH, callback = motionSensorInterrupt, bouncetime = 5)
GPIO.add_event_detect(breakBeamSensor, GPIO.BOTH, callback = beamSensorInterrupt, bouncetime = 5)

mainLoopThread = threading.Thread(target = mainLoop)
mainLoopThread.start()

readButtonsThread = threading.Thread(target = readButtons)
readButtonsThread.start()

#start server if not already running:
test = os.popen('sudo netstat -lpn | grep :5000')
print(test.read())
if __name__ == "__main__":
    app.run(host='0.0.0.0')
