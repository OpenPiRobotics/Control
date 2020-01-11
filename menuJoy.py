# Code for Brian Corteil's Tiny 4WD robot, based on code from Brian as modified by Emma Norling.
# Subsequently modified by Tom Oinn to add dummy functions when no explorer hat is available,
# modified by Brian Corteil to use the redboard+ motor controller hat and a menu using the SDD1306 OLED display
# use any available joystick, use the new function in 1.0.6 of approxeng.input to get multiple
# axis values in a single call, use implicit de-structuring of tuples to reduce verbosity, add
# an exception to break out of the control loop on pressing SELECT etc.

from time import sleep, time
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# for ip address

import subprocess

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# is OLED fitted

OLEDflag = False

# Create the SSD1306 OLED class and setup the display
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
try:
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    OLEDflag = True
except ValueError:
    print('')
    print('SSD1306 OLED Screen not found')
    print('')

if OLEDflag:

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('/home/pi/RedBoard/system/Greenscr.ttf', 12)



try:
    # Attempt to import the REDBOARD HAT library. If this fails, because we're running somewhere
    # that doesn't have the library, we create dummy functions for set_speeds and stop_motors which
    # just print out what they'd have done. This is a fairly common way to deal with hardware that
    # may or may not exist! Obviously if you're actually running this on one of Brian's robots you
    # should have the Explorer HAT libraries installed, this is really just so I can test on my big
    # linux desktop machine when coding.

    import redboard

    print('Redboard HAT library available.')


    def set_speeds(power_left, power_right):
        """
        As we have an motor hat, we can use the motors

        :param power_left:
            Power to send to left motor
        :param power_right:
            Power to send to right motor, will be inverted to reflect chassis layout
        """
        redboard.M1(-power_right)
        redboard.M2(power_left)


    def stop_motors():
        """
        As we have an motor hat, stop the motors using their motors call
        """
        redboard.M1(0)
        redboard.M2(0)

except ImportError:

    print('No Redboard HAT library available, using dummy functions.')


    def set_speeds(power_left, power_right):
        """
        No motor hat - print what we would have sent to it if we'd had one.
        """
        print('Left: {}, Right: {}'.format(power_left, power_right))
        sleep(0.1)


    def stop_motors():
        """
        No motor hat, so just print a message.
        """
        print('Motors stopping')

# All we need, as we don't care which controller we bind to, is the ControllerResource
from approxeng.input.selectbinder import ControllerResource


class RobotStopException(Exception):
    """
    The simplest possible subclass of Exception, we'll raise this if we want to stop the robot
    for any reason. Creating a custom exception like this makes the code more readable later.
    """
    pass


def mixer(yaw, throttle, max_power=100):
    """
    Mix a pair of joystick axes, returning a pair of wheel speeds. This is where the mapping from
    joystick positions to wheel powers is defined, so any changes to how the robot drives should
    be made here, everything else is really just plumbing.

    :param yaw:
        Yaw axis value, ranges from -1.0 to 1.0
    :param throttle:
        Throttle axis value, ranges from -1.0 to 1.0
    :param max_power:
        Maximum speed that should be returned from the mixer, defaults to 100
    :return:
        A pair of power_left, power_right integer values to send to the motor driver
    """
    left = throttle + yaw
    right = throttle - yaw
    scale = float(max_power) / max(1, abs(left), abs(right))
    return int(left * scale), int(right * scale)

# functions for OLED display

if OLEDflag:

    def clearDisplay():
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

    def lineOneText(text):
        draw.rectangle((0, 0, width, height / 2), outline=0, fill=0)
        draw.text((0, 2), text, font=font, fill=255)

    def lineTwoText(text):

        draw.rectangle((0, 32, width, height / 2), outline=0, fill=0)
        draw.text((0, 16), text, font=font, fill=255)

    def updateDisplay():

        disp.image(image)
        disp.show()

else:

    def clearDisplay():
        pass


    def lineOneText(text):
        print(text)


    def lineTwoText(text):

        print(text)

        
    def updateDisplay():

        pass


# end OLED functions

def homeDisplayUpdate():
    cmd = "python3 /home/pi/RedBoard/system/bat_check.py"
    mainBattery = subprocess.check_output(cmd, shell=True).decode()
    mainBattery = mainBattery.replace("\n", "")
    if len(mainBattery) == 4:
        mainBattery += "0"
    text1 = "Batt: " + mainBattery + "V"
    lineOneText(text1)
    if not joystick.battery_level == None:
        joy_battery_level = joystick.battery_level * 100
        text2 = "Joy: " + str(joy_battery_level) + "%"
    else:
        text2 = "Joy: Not supported"
    lineTwoText(text2)

    print(text1 + " " + text2)


# setup for main loop

menu = {'Manual': True, 'Line': False, 'Maze': False, 'Toxic': False, 'Zombie': False, 'IP': False, 'Exit': False,
        'Shutdown': False, 'Reboot': False}
menuItems = list(menu)
menuLenght = len(menuItems)
menuIndex = 0
lastMenuIndex = menuIndex
menuFlag = False
mode = menuIndex
oldMode = mode
currentMenu = {**menu}
displayTimeOut = 1 # time in seconds for display to blank or return to home screen
displayTimeOutFlag = False
savedTime = time()
currentTime = time()
newModeFlag = False
lastBatteryTime = time()
refreshTime = 60 # in seconds
lastRefresh = time() - refreshTime
displayHomeScreenFlag = False



# End of setup

# Outer try / except catches the RobotStopException we just defined, which we'll raise when we want to
# bail out of the loop cleanly, shutting the motors down. We can raise this in response to a button press
try:
    while True:
        # Inner try / except is used to wait for a controller to become available, at which point we
        # bind to it and enter a loop where we read axis values and send commands to the motors.
        try:
            # Bind to any available joystick, this will use whatever's connected as long as the library
            # supports it.
            with ControllerResource(dead_zone=0.1, hot_zone=0.2) as joystick:
                print('Controller found, press SELECT button to exit, use left stick for power, right to steer.')
                print(joystick.controls)
                # Loop until the joystick disconnects, or we deliberately stop by raising a
                # RobotStopException
                while joystick.connected:
                    # Get joystick values from the left & right analogue sticks
                    x_axis, y_axis = joystick['rx', 'ly']
                    # Get power from mixer function
                    power_left, power_right = mixer(yaw=x_axis, throttle=y_axis)
                    #print(power_left, power_right)
                    # Set motor speeds
                    if power_left == 0 and power_right == 0:
                        stop_motors()
                    elif menu['Manual']:
                        set_speeds(power_left, power_right)
                    else:
                        stop_motors()
                    # Get a ButtonPresses object containing everything that was pressed since the last
                    # time around this loop.
                    joystick.check_presses()
                    # Print out any buttons that were pressed, if we had any
                    if joystick.has_presses:
                        print(joystick.presses)
                    # If SELECT was pressed, raise a RobotStopException to bail out of the loop

                        if 'select' in joystick.presses:
                            raise RobotStopException()


                        # menu flag set/unset  ** is the unpacking operator and enables a shallow copy of the dictionary

                        if 'home' in joystick.presses:

                            clearDisplay()

                            if menuFlag:
                                menuFlag = False
                                menu = {**currentMenu}
                                print("Menu exitied")
                                displayHomeScreenFlag = True

                                #print(menu)

                            else:
                                currentMenu = {**menu}
                                # print(currentMenu)
                                menuFlag = True
                                if menu[menuItems[mode]]:
                                    text = "MODE: " + menuItems[mode]
                                    print(text)
                                else:
                                    text = "No mode selected"
                                print("menu entered")
                                lineOneText(text)
                                for key in menuItems:
                                    menu[key] = False




                        #print("MenuFlag status: " + str(menuFlag))

                        # if d up is pressed move menu up

                        if 'dup' in joystick.presses and menuFlag:
                            menuIndex -= 1
                            if menuIndex < 0:
                                 menuIndex = menuLenght -1

                        # if d down is pressed move menu down

                        if 'ddown' in joystick.presses and menuFlag:
                            menuIndex += 1
                            if menuIndex == menuLenght:
                                menuIndex =  0

                        # if 'cycle' is press when in menu select assign current menu item to mode

                        if 'circle' in joystick.presses and menuFlag:
                            oldMode = mode
                            mode = menuIndex
                            menuFlag = False
                            newModeFlag = True
                            for key in menuItems:
                                if key == menuItems[mode]:
                                    menu[key] = True
                                else:
                                    menu[key] = False

                            savedTime = time()
                            displayTimeOutFlag = True
                            displayTimeOut = 2



                        # print menu item to command line

                        if lastMenuIndex != menuIndex and menuFlag:
                            text = menuItems[menuIndex]
                            print(text)
                            lineOneText(text)
                            print("Press 'O' to select")
                            lineTwoText("'O' to select")
                            lastMenuIndex = menuIndex

                    # screen blanking or home screen update
                    # home screen refresh time in seconds

                    currentTime = time()
                    if displayTimeOutFlag and (currentTime - savedTime > displayTimeOut):
                        clearDisplay()
                        displayTimeOutFlag = False
                        displayHomeScreenFlag = True


                    #updateDisplay()

                    if menuFlag == False and displayTimeOutFlag == False:
                        if currentTime - lastRefresh > refreshTime or displayHomeScreenFlag:
                            homeDisplayUpdate()
                            lastRefresh = time()
                            displayHomeScreenFlag = False

                    updateDisplay()


                    # end of screen blanking or home screen update



                    if menu['Manual']:

                        # code to be run while in manual mode here
                        pass

                    if menu['Line']:

                        # code for line following here
                        pass

                    if menu['Maze']:

                        # code for Maze here
                        pass

                    if menu['Toxic']:
                        # code for Toxic here
                        pass

                    if menu['Zombie']:
                        # code for Zombie here
                        pass

                    if menu['IP']:
                        # code for displaying IP address
                        cmd = "hostname -I | cut -d\' \' -f1"
                        IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
                        print(IP)
                        lineOneText('')
                        lineTwoText(IP)

                        menu['IP'] = False
                        newModeFlag = False
                        mode = 0
                        savedTime = time()
                        displayTimeOutFlag = True
                        displayTimeOut = 5

                    if menu['Exit']:
                        # Exit to commard line
                        newModeFlag = False
                        raise RobotStopException()

                    if menu['Shutdown']:
                        # Shutdown the Raspberry Pi
                        newModeFlag = False
                        cmd = "sudo halt"
                        subprocess.call(cmd, shell=True)

                    if menu['Reboot']:
                        # Reboot the Raspberry Pi
                        newModeFlag = False
                        cmd = "sudo reboot"
                        subprocess.call(cmd, shell=True)

                    if newModeFlag:
                        clearDisplay()
                        text = "New Mode: " + menuItems[mode]
                        print(text)
                        lineOneText(text)
                        newModeFlag = False


        except IOError:
            # We get an IOError when using the ControllerResource if we don't have a controller yet,
            # so in this case we just wait a second and try again after printing a message.
            print('No controller found yet')
            lineOneText("No Controller")
            lineTwoText("  Connected")
            updateDisplay()
            sleep(1)
            clearDisplay()

except RobotStopException:
    # This exception will be raised when the home button is pressed, at which point we should
    # stop the motors.
    print("stoping motors and exit to commard line")
    stop_motors()
    # write to display exit message
    lineOneText("exited to ")
    lineTwoText("command line")
    updateDisplay()
    sleep(1)
    clearDisplay()
    updateDisplay()
