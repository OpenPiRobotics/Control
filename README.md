# Control

Code for controlling a Raspberry Pi robot with a gamepad.

The code has been writen for a Raspberry Pi robot using the Red Robotics RedBoard+ robot controller hat and can be modified to use a different motor controller by changing the functions set_speeds and stop_motors.

Note: you may also need to adjust the output from the function mixer to suit your controller.

# Display

The Redboard+ can be fitted with a daughter board with a built in display, if you are not using a Redboard+ a generic SSD1306 OLED 32 x 16 display can be used instead. A display is not required for the code to run.

# Battery Reading

The RedBoard+ has a 4 channel analogue to digital conveter (ADS1X15).
The first channel (channel_0) is used to measure the battery voltage (through a voltage divider).
You can buy the ADS1X15 on a breakout board.

# Dependencies

Tom Oinn's input Python3 library is used for reading the joypad. Instutions for installing the library is available from https://approxeng.github.io/approxeng.input/

Follow the instutions on Red Robotics github account for the other dependencies on a clean build of Raspbian
https://github.com/RedRobotics/RedBoard

you will need to edit your rc.local file and hash out this line python3 /home/pi/RedBoard/ssd1306_stats.py&
