# dji log parser version 0.0
# Carolus Vrattos, et Marcellus Magnasco Rockefellersiis faciebat me, anno Domine MMXVII 

#ACKNOWLEDGEMENTS
#The structure of the log data was obtained from Mikee Franklin's project https://github.com/mikeemoo/dji-log-parser

from pylab import *
import numpy as np
import struct as struct
from math import *
import os

#This dictionary is not used but it specifies the integer that corresponds to each data type
#Only some attributes of the OSD and GIMBAL data are extracted by this program
#To obtain other attributes or types of data, copy the format of this program 
#and obtain the structure of the packets from https://github.com/mikeemoo/dji-log-parser
typedict =  {   1: 'OSD',  2: "HOME",   3: "GIMBAL",  4: "RC",  5: "CUSTOM",  6: "DEFORM",  7: "CENTER_BATTERY",
    8: "SMART_BATTERY",  9: "APP_TIP",  10: "APP_WARN",  11: "RC_GPS",  12: "RC_DEBUG",  13: "RECOVER",
    14: "APP_GPS",  15: "FIRMWARE",  255: "END",  254: "OTHER"  } 

def main(inputFile):

    array = []
    latitude = 0
    longitude = 0
    height = 0
    flyTime = 0
    pitch = 0
    roll = 0
    yaw = 0

    #Read the input file first as a raw binary file
    #fdata is the datastream that will be read packet by packet
    myFile = open(inputFile,'rb')
    printing = False
    fdata = myFile.read()

    #Read the input file a second time as an array integers
    #These integers are read to determine the type of each packet
    myFile.seek(0)
    data = np.fromfile(myFile, dtype=np.uint8)
    myFile.close()

    #I am unsure of what the first 12 bytes contain but the information is not relevant to this program
    packetstart = 12

    #Towards the end of the data the data types returned do not match the integers in the dictionary above
    #I do not know what these integers signify but as soon as the loop hits them it stops
    while data[packetstart] <= 15:
        #The ptype specifies the type of data contained by a packet
        ptype = data[packetstart]
        #The plen specifies the length of the packet
        plen  = data[packetstart+1]
        #The payload is a binary string of length plen
        payload = fdata[(packetstart+2):(packetstart+2+plen)]
        endmark = data[packetstart+2+plen]

        #At the end of every packet there should be an endmark which is equal to 255
        if endmark != 255:
            print("Error")
            print(endmark)

        #OSD packet parser
        if  ptype == 1:
            if printing:
                #Latitude and Longitude are stored as doubles (bytes 0 to 8 and 8 to 16) and height is stored as a short (bytes 16 to 18)
                longitude, latitude, height = struct.unpack("2dh",payload[0:18])
                #Flytime is stored as a short (bytes 42 to 44)
                flyTime = struct.unpack("h", payload[42:44])
                #Convert the flytime to seconds from tenths of a second
                flyTime = flyTime[0] / 10
                #Convert height to meters from decimeters
                height = height / 10
                #Longitude and latitude are both converted from radians to degrees
                latitude = double(latitude) * 180 / math.pi
                longitude = double(longitude) * 180 / math.pi
                #There are a couple extraneous flytime values so I only start recording at 0.1 seconds
                #The current value of every global variable is recorded for each flytime
                #The GIMBAL values only update when changed but the OSD values are updated every 0.1 seconds
                if(flyTime > 0):
                    dictionary = {"flyTime": flyTime, "longitude": longitude, "latitude": latitude, "height": height, "pitch": pitch, "roll": roll, "yaw": yaw}
                    array.append(dictionary)
            else: 
                printing = True

        #GIMBAL packet parser
        elif ptype == 3 :
            #Pitch, roll, and yaw are all stored as shorts (bytes 0 to 2, 2 to 4, and 4 to 8)
            pitch, roll, yaw = struct.unpack("3h",payload[0:6])
            #The pitch yaw and roll are stored as values between -1800 and 1800
            #I convert these to -180 and 180 for ease of use
            pitch = pitch/10
            roll = roll/10
            yaw = yaw/10
        #iterate the packet start by plen and the 2 bytes that specify type and length
        packetstart = packetstart + plen+ 2 + 1
    #A file containing the array is saved locally
    np.save("SaveFile",array)
