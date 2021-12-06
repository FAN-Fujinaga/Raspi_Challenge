# GrovePi Sensor Using Module
#
# History
# ------------------------------------------------
# Author	Date      		Comments
#
# Fujinaga      06 Jul 2021		Intial Authoring
#
# NOTE:
#   This program is for Thread of sensors
#   ThreadMain  ->  Super Class

import time
import threading
import grovepi
import math
import smbus

# Semaphore for I/O access
IO_Semaphore = False

# Thread Super Class																																																																																																																																																																																																																																																																																																																																																																																																																																																    
class ThreadMain(threading.Thread, object):

    def __init__(self, adrs, name):
        super(ThreadMain, self).__init__()
        self.adrs = adrs
        self.name = name

        self.started = threading.Event()    # Bound events
        self.alive = True
        self.start()                        # call run() and wait bigin()

    def bigin(self):
        self.alive = True
        self.started.set()                  # Set event to enable
        print(self.name + " is started.")

    def pause(self):
        self.started.clear()                # Set event to disable
        print(self.name + " is paused.")

    def end(self):
        self.alive = False
        self.started.set()
        self.join()                         # Wait thread closing
        print(self.name + " is ended.")


# LCD Display sensor																																																																																																																																																																																																																																																																																																																																																																																																																																															    
class Display(ThreadMain, object):

    def __init__(self, textAdrs, RGBAdrs, name):
        super(Display, self).__init__(0x0, name)
        self.bus = smbus.SMBus(1)
        self.textAdrs = textAdrs
        self.RGBAdrs = RGBAdrs

        self.red = 0
        self.green = 0
        self.blue = 0
        self.text = ""

        self.ex_red = 0
        self.ex_green = 0
        self.ex_blue = 0
        self.ex_text = ""


    def checkRBGChange(self):
        RGBChange = False
        if self.ex_red != self.red or self.ex_green != self.green or self.ex_blue != self.blue:
            RGBChange = True

        self.ex_red = self.red
        self.ex_green = self.green
        self.ex_blue =  self.blue

        return RGBChange

    def checkTextChange(self):
        textChange = False
        if self.ex_text != self.text:
            textChange = True

        self.ex_text = self.text
        return textChange

    def chgBackLight(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue =  blue

    def chgText(self, text):
        self.text = text

    # Set backlight to RGB (values from 0..255 for each)
    def setRGB(self, red, green, blue):
        self.bus.write_byte_data(self.RGBAdrs, 0, 0)
        self.bus.write_byte_data(self.RGBAdrs, 1, 0)
        self.bus.write_byte_data(self.RGBAdrs, 8, 0xaa)
        self.bus.write_byte_data(self.RGBAdrs, 4, red)
        self.bus.write_byte_data(self.RGBAdrs, 3, green)
        self.bus.write_byte_data(self.RGBAdrs, 2, blue)

    # Send command to display (no need for external use)
    def textCommand(self, cmd):
        self.bus.write_byte_data(self.textAdrs, 0x80, cmd)

    # Set display text \n for second line(or auto wrap)
    def setText(self, text, delay = 0.0):
        self.textCommand(0x01)               # Clear Display
        time.sleep(0.05)
    
        self.textCommand(0x08 | 0x04)        # Display on without cursor
        self.textCommand(0x28)               # 2 lines
        time.sleep(0.05)

        count = 0
        row = 0
        for c in text:
            if c == "\n" or count == 16:
                count = 0
                row += 1
                if row == 2:
                    break
                self.textCommand(0xc0)
                if c == "\n":
                    continue
            count += 1
            self.bus.write_byte_data(self.textAdrs, 0x40, ord(c))
            time.sleep(delay)

    # Update the display without erasing the display
    def setText_norefresh(self, text):
        self.textCommand(0x02)              # Return home
        time.sleep(0.05)

        self.textCommand(0x08 | 0x04)       # Display on without cursor
        self.textCommand(0x28)              # 2 lines
        time.sleep(0.05)

        count = 0
        row = 0
        while len(text) < 32:               #clear the rest of the screen
            text += " "

        for c in text:
            if c == "\n" or count == 16:
                count = 0
                row += 1
                if row == 2:
                    break
                self.textCommand(0xc0)
                if c == "\n":
                    continue
            count += 1
            self.bus.write_byte_data(self.textAdrs, 0x40, ord(c))


    def run(self):
        global IO_Semaphore
        
        self.started.wait()
        while self.alive:
            if IO_Semaphore == False:
                IO_Semaphore = True

                try:
                    if self.checkRBGChange() == True:
                        self.setRGB(self.red, self.green, self.blue)

                    if self.checkTextChange() == True:
                        self.setText(self.text)

                except IOError:
                    print ("IOError")
                
                IO_Semaphore = False
                time.sleep(1.0)
            else:
                time.sleep(0.01)

    def bigin(self):
        super(Display, self).bigin()

    def pause(self):
        super(Display, self).pause()

    def end(self):
        super(Display, self).end()


# temperature & humidity Sensor
class DHT(ThreadMain, object):

    def __init__(self, adrs, name, snsType):
        super(DHT, self).__init__(adrs, name)
        self.snsType = snsType   

    def run(self):
        global IO_Semaphore
        
        self.started.wait()
        while self.alive:
            if IO_Semaphore == False:
                
                IO_Semaphore = True
                try:
                    [temp,humidity] = grovepi.dht(self.adrs, self.snsType)
                    if math.isnan(temp) == False and math.isnan(humidity) == False:
                        print("temp = %.02f C humidity =%.02f%%" %(temp, humidity))
                        self.temp = temp
                        self.humid = humidity

                except IOError:
                    print ("IOError")
                
                IO_Semaphore = False
                time.sleep(0.5)
            else:
                time.sleep(0.01)

    def bigin(self):
        super(DHT, self).bigin()

    def pause(self):
        super(DHT, self).pause()

    def end(self):
        super(DHT, self).end()

# Light sensor																																																																																																																																																																																																																																																																																																																																																																																																																																															    
class Light(ThreadMain, object):

    def __init__(self, adrs, name):
        super(Light, self).__init__(adrs, name)

        grovepi.pinMode(self.adrs, "INPUT")
        self.SensVal = 0
        self.LightVal = 0

    def run(self):
        global IO_Semaphore
        
        self.started.wait()
        while self.alive:
            if IO_Semaphore == False:
                
                IO_Semaphore = True
                try:
                    self.SensVal = grovepi.analogRead(self.adrs)
                    self.LightVal = (self.SensVal * 100) / 1023
                    print("Light = %d" %self.LightVal)

                except IOError:
                    print ("IOError")
                
                IO_Semaphore = False
                time.sleep(1.0)
            else:
                time.sleep(0.01)

    def bigin(self):
        super(Light, self).bigin()

    def pause(self):
        super(Light, self).pause()

    def end(self):
        super(Light, self).end()

# Sound sensor																																																																																																																																																																																																																																																																																																																																																																																																																																															    
class Sound(ThreadMain, object):

    def __init__(self, adrs, name):
        super(Sound, self).__init__(adrs, name)

        grovepi.pinMode(self.adrs, "INPUT")
        self.SoundVal = 0

    def run(self):
        global IO_Semaphore
        
        self.started.wait()
        while self.alive:
            if IO_Semaphore == False:
                
                IO_Semaphore = True
                try:
                    self.SoundVal = grovepi.analogRead(self.adrs)
                    print("Sound = %d" %self.SoundVal)

                except IOError:
                    print ("IOError")
                
                IO_Semaphore = False
                time.sleep(1.0)
            else:
                time.sleep(0.01)

    def bigin(self):
        super(Sound, self).bigin()

    def pause(self):
        super(Sound, self).pause()

    def end(self):
        super(Sound, self).end()

# Ultrasonic sensor																																																																																																																																																																																																																																																																																																																																																																																																																																															    
class Sonic(ThreadMain, object):

    def __init__(self, adrs, name):
        super(Sonic, self).__init__(adrs, name)

        grovepi.set_bus("RPI_1")
        self.SonicVal = 0

    def run(self):
        global IO_Semaphore
        
        self.started.wait()
        while self.alive:
            if IO_Semaphore == False:
                
                IO_Semaphore = True
                try:
                    self.SonicVal = grovepi.ultrasonicRead(self.adrs)
                    print("Ultrasonic = %d" %self.SonicVal)

                except IOError:
                    print ("IOError")
                
                IO_Semaphore = False
                time.sleep(1.0)
            else:
                time.sleep(0.01)

    def bigin(self):
        super(Sonic, self).bigin()

    def pause(self):
        super(Sonic, self).pause()

    def end(self):
        super(Sonic, self).end()

# DI Control ex.Switch																																																																																																																																																																																																																																																																																																																																																																																																																																																    
class DI(ThreadMain, object):

    def __init__(self, adrs, name, onTimerSetting):
        super(DI, self).__init__(adrs, name)

        grovepi.pinMode(self.adrs, "INPUT")
        self.onTimerSetting = onTimerSetting
        self.DISts = 0

    def run(self):
        global IO_Semaphore
        DIStsOld = False
        DIStsCur = False
        self.DIOnTimeCnt = 0

        self.started.wait()
        while self.alive:

            if IO_Semaphore == False:
                IO_Semaphore = True
                DIStsCur = grovepi.digitalRead(self.adrs)
                
                if DIStsCur == False and DIStsOld == False:     # OFF
                    self.DISts = 0

                elif DIStsCur == False and DIStsOld == True:    # OFF Trigger
                    self.DISts = 1

                elif DIStsCur == True and DIStsOld == False:    # ON Trigger
                    self.DISts = 2
                    self.DIOnTimeCnt = 0
                else:
                    self.DIOnTimeCnt += 1
                    if self.DIOnTimeCnt < self.onTimerSetting:  # ON Timer Counting
                        self.DISts = 3
                    else:                                       # ON Timer Count Up
                        self.DISts = 4
                    
                DIStsOld = DIStsCur
                IO_Semaphore = False
            
            time.sleep(0.01)

    def bigin(self):
        super(DI, self).bigin()

    def pause(self):
        super(DI, self).pause()

    def end(self):        
        super(DI, self).end()

# DO Control ex.Led Lighting Buzzer Beeping																																																																																																																																																																																																																																																																																																																																																																																																																																																    
class DO(ThreadMain, object):

    def __init__(self, adrs, name):
        super(DO, self).__init__(adrs, name)

        self.DOSts = 0
        grovepi.pinMode(self.adrs, "OUTPUT")
        grovepi.digitalWrite(self.adrs, False)
																																																							
    def run(self):
        global IO_Semaphore
        BlinkCnt = 0
        blinkSts = 0

        self.started.wait()
        while self.alive:

            if IO_Semaphore == False:
                IO_Semaphore = True

                if self.DOSts == 2:
                    grovepi.digitalWrite(self.adrs, blinkSts)

                elif self.DOSts == 1:
                    grovepi.digitalWrite(self.adrs, True)

                else:
                    grovepi.digitalWrite(self.adrs, False)  

                IO_Semaphore = False
                BlinkCnt += 1

            time.sleep(0.01)

            if BlinkCnt >= 0 and BlinkCnt <= 40:
                blinkSts = 0
            elif BlinkCnt > 40 and BlinkCnt <= 80:
                blinkSts = 1
            else:
                BlinkCnt = 0

    def bigin(self):
        super(DO, self).bigin()

    def pause(self):
        super(DO, self).pause()

    def end(self):
        super(DO, self).end()
