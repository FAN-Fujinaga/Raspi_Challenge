# GrovePi Sensor testing Module
#
# History
# ------------------------------------------------
# Author	Date      		Comments
#
# Fujinaga      06 Jul 2021		Intial Authoring
#
# NOTE:
#   This programm is usingsensors below.
# 	DHT:        Temperature & Humidity Sensor
# 	RGB_LCD:    LCD 2x16 Display Device
# 	LED:        Some LED's
# 	BUZZER:     Normal Buzzer
# 	CAMERA:     PiCamera
#   This program must to be booted by "sudo".

import time
import signal
import sys
import math
import os
import csv
import smbus
import picamera
import pygame.mixer
import imaplib
import RPi.GPIO as GPIO

import ThreadMain

# Analog Device Address																																																																																																																																																																																																																																																																																																																																																																																																																																																	
LIGHT_ADRS = 0                      # Light sensor connected to A0 port
SOUND_ADRS = 1                      # Sound sensor connected to A1 port

# Digital Device Address	
LED_R_ADRS = 2                      # Red LED connected to D2 port
LED_G_ADRS = 3                      # Green LED connected to D3 port
LED_B_ADRS = 4                      # Blue LED connected to D4 port
SWITCH_ADRS = 7                     # Switch connected to D7 port
BUZZER_ADRS = 8                     # Buzzer connected to D8 port

# I2C Device Address
SONIC_ADRS = 5                      # Ultrasonic sensor connected to D5 port
DHT_ADRS = 6                        # DHT sensor connected to D6 port

# RGB_LCD device has two I2C addresses for connect I2C-1
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# DHT Sensor Type Definition
DHT_TYPE_BLUE = 0

# Definition DIO
DI_OFF = 0
DI_OFF_TRIG = 1
DI_ON_TRIG = 2
DI_COUNTING = 3
DI_DELAY_ON = 4

DO_OFF = 0
DO_ON = 1
DO_BLINK = 2

# Definition Display Type
TYPE_DHT = 0
TYPE_SONIC = 1
TYPE_SOUND = 2
TYPE_PHOTO = 3


# CSV File Create
csvFilename = time.strftime("%Y%m%d%H%M%S") + ".csv"
csvSaveFile = "/var/samba/csv/" + csvFilename

# MP3 File
shutterSound = "/var/samba/MP3/Shutter.mp3"

# Interval Process -- Update CSV file.
def intervalTask(arg1, arg2):
    global csvSaveFile
    
    if os.path.exists(csvSaveFile) == True:
        curCsvFile = open(csvSaveFile, "a")
        w = csv.writer(curCsvFile, lineterminator = "\n")
        w.writerow([time.strftime("%H:%M:%S"), tDht.temp, tDht.humid, tLight.LightVal, tSonic.SonicVal, tSound.SoundVal])
        curCsvFile.close()

def createCsvFile():
    global csvSaveFile

    createFile = open(csvSaveFile, "w")
    w = csv.writer(createFile, lineterminator = "\n")
    w.writerow([ "Time", "Temp", "Humid", "Light", "Sonic", "Sound"])
    createFile.close()

# Finalize -- end of procedure
def endProcess():
    
    tLedR.DOSts = DO_OFF
    tLedG.DOSts = DO_OFF
    tLedB.DOSts = DO_OFF
    tBuzzer.DOSts = DO_OFF
    tLCD.chgBackLight(255, 255, 255)
    tLCD.chgText("Bye Bye !!")

    time.sleep(2)

    tLedR.end()
    tLedG.end()
    tLedB.end()
    tBuzzer.end()
    tLCD.chgBackLight(0, 0, 0)

    tSwitch.end()
    tDht.end()
    tLight.end()
    tSound.end()
    tSonic.end()

    time.sleep(3)
    tLCD.end()

# Booting process
if __name__=="__main__":

    time.sleep(0.1)

    DispType = TYPE_DHT
    switchStsOld = DI_OFF
    checkCameraFlg = False
    
    tLedR = ThreadMain.DO(LED_R_ADRS, "Red LED")
    tLedG = ThreadMain.DO(LED_G_ADRS, "Green LED")
    tLedB = ThreadMain.DO(LED_B_ADRS, "Blue LED")
    tBuzzer = ThreadMain.DO(BUZZER_ADRS, "Buzzer")
    tSwitch = ThreadMain.DI(SWITCH_ADRS, "Switch", 3)
    tDht = ThreadMain.DHT(DHT_ADRS, "DHT Sensor", DHT_TYPE_BLUE)
    tLight = ThreadMain.Light(LIGHT_ADRS, "Light Sensor")
    tSound = ThreadMain.Sound(SOUND_ADRS, "Sound Sensor")
    tSonic = ThreadMain.Sonic(SONIC_ADRS, "UltraSonic Sensor")
    tLCD = ThreadMain.Display(DISPLAY_TEXT_ADDR ,DISPLAY_RGB_ADDR, "LCD_Display")
    
    time.sleep(0.1)

    tLedR.DOSts = DO_BLINK
    tBuzzer.DOSts = DO_OFF
    
    tLedR.bigin()
    tLedG.bigin()
    tLedB.bigin()
    tBuzzer.bigin()
    tSwitch.bigin()
    tDht.bigin()
    tLight.bigin()
    tSound.bigin()
    tSonic.bigin()
    tLCD.bigin()

    tLCD.chgBackLight(0, 0, 255)
    tLCD.chgText("Let's start \nMonitoring!!")

    pygame.mixer.init()
    pygame.mixer.music.load(shutterSound)
    pygame.mixer.music.set_volume(1.0)
    
    time.sleep(3)

    cam = picamera.PiCamera()
    cam.resolution = (800, 600)

    createCsvFile()

    signal.signal(signal.SIGALRM, intervalTask)
    signal.setitimer(signal.ITIMER_REAL, 10, 10)

    # Main Loop
    while True:
        try:
            time.sleep(0.3)

            # Check Display information type
            if tSwitch.DISts == DI_DELAY_ON and switchStsOld <> DI_DELAY_ON:
                if DispType == TYPE_DHT:
                    DispType = TYPE_SONIC
                    
                elif DispType == TYPE_SONIC:
                    DispType = TYPE_SOUND

                elif DispType == TYPE_SOUND:
                    DispType = TYPE_DHT

                elif DispType == TYPE_PHOTO:
                    checkCameraFlg = False
                    DispType = TYPE_DHT
                         
            switchStsOld = tSwitch.DISts

            # Modify Backight color and Sensor information
            if DispType == TYPE_DHT:
                tLCD.chgText("Temp   {0:.02f} C\nHumid  {1:.02f} %".format(tDht.temp, tDht.humid))                
                if float(tDht.temp) > 35.00:
                    tLCD.chgBackLight(255, 0, 0)
                    tLedR.DOSts = DO_ON
                    tLedG.DOSts = DO_OFF
                    tLedB.DOSts = DO_OFF

                elif float(tDht.temp) > 25.00:
                    tLCD.chgBackLight(255, 255, 0)
                    tLedR.DOSts = DO_OFF
                    tLedG.DOSts = DO_OFF
                    tLedB.DOSts = DO_OFF

                else:
                    tLCD.chgBackLight(0, 255, 0)
                    tLedR.DOSts = DO_OFF
                    tLedG.DOSts = DO_ON
                    tLedB.DOSts = DO_OFF

            elif DispType == TYPE_SONIC:
                tLCD.chgText("Light  {0:3d}\nSonic  {1:3d}".format(tLight.LightVal, tSonic.SonicVal))
                tLCD.chgBackLight(0, 255, 255)
                tLedR.DOSts = DO_OFF
                tLedG.DOSts = DO_ON
                tLedB.DOSts = DO_ON

            elif DispType == TYPE_SOUND:
                tLCD.chgText("Sound  {0:3d}".format(tSound.SoundVal))
                if tSound.SoundVal > 300:
                    tLCD.chgBackLight(255, 0, 0)
                    tLedR.DOSts = DO_ON
                    tLedG.DOSts = DO_OFF
                    tLedB.DOSts = DO_OFF

                else:
                    tLCD.chgBackLight(0, 255, 0)
                    tLedR.DOSts = DO_OFF
                    tLedG.DOSts = DO_ON
                    tLedB.DOSts = DO_OFF

            # Take a photo process
            if int(tSonic.SonicVal) < 10 and checkCameraFlg == False:
                camFilename = time.strftime("%Y%m%d%H%M%S") + ".jpg"
                camSaveFile = "/var/samba/Photos/" + camFilename
                cam.capture(camSaveFile)

                pygame.mixer.music.play(0)
                DispType = TYPE_PHOTO
                tLCD.chgText("Take a new photo\nPlease reset")
                tLCD.chgBackLight(128, 0, 128)
                checkCameraFlg = True
                
            # Quit Main-Loop
            if tSwitch.DISts == DI_DELAY_ON and tSwitch.DIOnTimeCnt > 50:      
                break

        # Catch Ctrl+C Exception (Only available in case booting from LXTerminal)
        except KeyboardInterrupt:
            break

    endProcess()
    




