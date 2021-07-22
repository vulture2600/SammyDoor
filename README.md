# SammyDoor
Automated door for my cat Sammy using Raspberry Pi and Python.


This project was an upgrade from the previous version which was using an Arduino Uno. It never really handled web requests very well so I decided to go down many recursively nested rabbit holes and upgrade it to a Raspberry Pi model 3A+. After about 2 and a half weeks, I had a functioning prototype on my desktop Raspberry Pi 4B/4GB. 
I then powered up and configured the new Pi and installed it where the arduino used to be. I used all the same connectors for each connection so it was a direct swap.

During this project, I learned several new python technologies including Flask, and threading, and gained more experience with Python over all. It was also my first project using Microsoft VS Code for the entire development. I've recently started using it and will never go back.  

Hardware used:
Raspberry Pi model 3A+: https://www.raspberrypi.org/products/raspberry-pi-3-model-a-plus/
Adafruit Perma-Proto hat for Pi with EEPROM: https://www.adafruit.com/product/2314
Adafruit RGB Positive 16x2 LCD + Keypad Kid for Raspberry Pi: https://www.adafruit.com/product/1109
SparkFun Open PIR: https://www.sparkfun.com/products/13968
IR Break Beam Sensors: https://www.adafruit.com/product/2167
Two servos, one large, one micro for the door and lock respectively.
Magnetic door sensor.
Various 2, 3 and 4 pin connectors.

Special thanks to https://github.com/MarksBench for his help with his EEPROM library. I had to edit one line in busio.py to allow it to talk to the secondary I2C bus. See busio2.py. Line 65 specifies bus #6 as one of the arguments.




