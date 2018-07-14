# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 11:55:13 2018

@author: henra
"""

import time
import sys
#import serial
import numpy
#from RPi import GPIO
import binascii

#Function (Sent by host)
General_Read =          0x0e
Set_Origin =            0x00
Go_Absolute_Pos =       0x01
Make_LinearLine =       0x02
Go_Relative_Pos =       0x03
Make_CircularArc =      0x04            #define Go_Relative_PosM = 0x04
Assign_Driver_ID =      0x05
Read_Driver_ID =        0x06
Set_Driver_Config =     0x07
Read_Driver_Config =    0x08
Read_Driver_Status =    0x09
Turn_ConstSpeed =       0x0a
Square_Wave =           0x0b
Sin_Wave =              0x0c
SS_Frequency =          0x0d
Read_PosCmd32 =	        0x0e
Set_MainGain =          0x10
Set_SpeedGain =         0x11
Set_IntGain =           0x12
Set_TrqCons =           0x13
Set_HighSpeed =		    	0x14
Set_HighAccel =		    	0x15
Set_Pos_OnRange =       0x16
Set_FoldNumber =		  0x17
Read_MainGain =         0x18
Read_SpeedGain =        0x19
Read_IntGain =          0x1a
Read_TrqCons =          0x1b
Read_HighSpeed =    	  0x1c
Read_HighAccel =	     0x1d
Read_Pos_OnRange =      0x1e
Read_FoldNumber =	     0x1f

#functions (sent by driver)
Is_MainGain =           0x10
Is_SpeedGain =          0x11
Is_IntGain =            0x12
Is_TrqCons =            0x13
Is_HighSpeed =			  0x14
Is_HighAccel =			  0x15
Is_Driver_ID =			  0x16
Is_Pos_OnRange =        0x17
Is_FoldNumber =			  0x18
Is_Status =             0x19
Is_Config =             0x1a

#For driver status
Driver_OnPos =          0xfe
Driver_Busy =           0x01            #for b0
Driver_Servo =          0xfd
Driver_Free =           0x02            #for b1
Driver_Normal =         0x00
Driver_LostPhase =      0x04
Driver_OverCurrent =    0x08
Driver_OverHeat =       0x0c            #for b4 b3 b2 */
Driver_OverVolts =		  0x14
Is_AbsPos32 =			  0x1b		    #Absolute position 32
Is_TrqCurrent =			  0x1e		    #Motor current

#Following are used for Machine Code interpreting
Line_Error =			   0xff
Line_OK =				   0x00
Motor_OnPos =			0x00
Motor_Busy =			   0x01
Motor_Free =			   0x02
Motor_Alarm =			0x03

# Drive ID's
stage1_drive_id = 10 # drive id for stage 1 servo drive that runs the stage 1 set of rollers
stage2_drive_id = 20 # drive id for stage 2 servo drive that runs the stage 2 set of rollers
radius_drive_id = 21 # drive id for the servo drive that controls the stage 2 platform that changes the bend radius of the machine
angle_drive_id = 22 # drive id for the servo drive that controls the angle of the entire stage 2 platform.
# the servo driven by this servo drive is attached to the rack and pinion on stage 2 of the machine


# ---------------------Functions for Testing--------------------------------------------------------

def binary_display_int(integer):
    '''
    Takes in an integer
    Returns the binary representation of the argument as a string

    A helpful tool to check the binary representation of an integer
    '''
    binary_number = bin(integer)[2:].zfill(8)
    # bin converts the integer to a binary string with 0b in front
    # using the [2:] reference we can just show what we want to see, 0's and 1's.
    return binary_number


def binary_display_byte(byte):
    '''
    Takes in a byte
    returns the binary representation of the arguement as a string

    A helpful tool to check the binary representation of a byte
    '''
    byte_as_integer = int.from_bytes(byte, byteorder='big', signed=True)
    # class method that takes in a byte and returns the integer
    # byte order needs to be big if you want the MSB on the left side. Byte order= little gives you MSB on the right.
    # the signed argument indicates whether two's complement is used to represent the integer

    binary_number = bin(byte_as_integer)[2:].zfill(8)
    # bin converts the integer to a binary string with 0b in front
    # using the [2:] reference we can just show what we want to see, 0's and 1's.

    return binary_number


# ------------------------------------------------------------------------------------------------


def DriveByte(a): #formats start byte properly pg 52
    #if this returns nothing then there is an error
    if a >= 0 and a <= 63: 
        return a
    else:
        print('Error: drive location out of range')

def FunctionAndLength(length,code): #formats 2nd byte pg53
    l = (length-1) * 32 #pg53, 32 is placeholder moving l to proper position
    output = 0x80 + l + code #0x80 adds 1000 0000 to the number
    return output

def int2ControllerFormat(num):
    #import numpy
    #make sure 'import numpy' is at top of file
    if num > 0 and num < 64:
        output = int(numpy.binary_repr(num,7),2)
        return output
    if num > 63  and num < 8192:
        output = int(numpy.binary_repr(num,14),2)
        return output
    if num > 8191  and num < 1048576:
        output = int(numpy.binary_repr(num,21),2)
        return output
    if num > 1048575:
        output = int(numpy.binary_repr(num,28),2)
        return output
    if num > 134217727:
        print('error, input data out of range')
        return

    if num < 0 and num > -65:
        output = int(numpy.binary_repr(num,7),2)
        return output
    if num <-64  and num > -8193:
        output = int(numpy.binary_repr(num,14),2)
        return output
    if num <-8192  and num > -1048577:
        output = int(numpy.binary_repr(num,21),2)
        return output
    if num <-1048576:
        output = int(numpy.binary_repr(num,28),2)
        return output
    if num <-134217728:
        print('error, input data out of range')
        return

def OutData(data): #returns a list containing properly formatted integers to transmit data
    # input data must be a large integer we want to transmit
    #In C data is sent out without adjusting for negative numbers so make sure
    #python is representing data the same as C represents an integer
    #Incoming data is interpreted using Cal_SignValue or Cal_Value, both 
    #functions do the same thing.
    BinData = bin(int2ControllerFormat(data))[2:] #converts input integer to binary string and chops off 0b
    length = len(BinData)   #number of binary digits in data
    b = divmod(length,7)
    outlist=list()
    
    if (length == 7 or length == 14 or length == 21 or length == 28) and BinData[0] == '1':  #number is negative
       numbyte=int(b[0]) # number of bytes required to send data 
       for i in range(0,numbyte):
           start = b[1] + (i) * 7
           end = b[1] +(i+1) * 7
           outlist.append(int(BinData[start:end],2) + 0x80)
       return outlist

    else:
       numbyte=int(b[0]+1) # number of bytes required to send data
    
    if numbyte > 4:
        print('Error: data too large to be sent')
        return
        
    if b[1] != 0: #append partial start byte to the beginning of BinData
        outlist.append(int(BinData[0:b[1]],2) + 0x80)  
        for i in range(1,numbyte):
            start = b[1] + (i-1) * 7
            end   = b[1] + (i) * 7
            outlist.append(int(BinData[start:end],2) + 0x80)
        return outlist
        
    if b[1] == 0:
        outlist.append(0x80) #need a leading blank byte see example 3 pg 62
        for i in range(0,numbyte-1):
            start = b[1] + (i) * 7
            end = b[1] +(i+1) * 7
            outlist.append(int(BinData[start:end],2) + 0x80)
        return outlist

def OutputSize(data): #notice how function is very similar to OutData, 
    BinData = bin(int2ControllerFormat(data))[2:] #converts input integer to binary string and chops off 0b
    length = len(BinData)   #number of binary digits in data

    #figure out how many bytes are in the data
    b = divmod(length,7)

    if (length == 7 or length == 14 or length == 21 or length == 28) and BinData[0] == '1':  #number is negative
       numbyte=int(b[0]) # number of bytes required to send data 
    else:
       numbyte=int(b[0]+1) # number of bytes required to send data

    # check if the data meets the criteria of being less than equal to 4 packets.
    # If it meets the criteria return the data, if not then return an error.
    if numbyte > 4:
        print('Error: data too large to be sent')
        return
    else:
        return numbyte
    
def CheckSum(BnA, BnMinus1A, DatalistA): # see page 55
    numData = len(DatalistA) #number of bytes used to transmit data   
    dataSum = 0
    for i in range(0,numData): # Calculates sum of data integers
        dataSum = dataSum + DatalistA[i]
    S = BnA + BnMinus1A +dataSum
    output = 0x80 + (S%128)
    return output

def Send(driveID, ToDo, packet):
    #packet should be integer not hex
    #Send packet to controller
    OutLen = OutputSize(packet) #of data bits see page 54 for how to set
    OutArray = bytearray(OutLen+3) # data to send to controller
    Bn = DriveByte(driveID)
    BnMinus1 = FunctionAndLength(OutLen, ToDo)
    DataList = OutData(packet) 
    B0 = CheckSum(Bn, BnMinus1, DataList)
    #assign variables to output byte array
    OutArray[0] = Bn
    OutArray[1] = BnMinus1
    for i in range(2,OutLen+2):
        a = DataList[i-2]
        OutArray[i] = a
    OutArray[OutLen+2] = B0
    #ser.write(OutArray)
    #ser.flush()
    return OutArray

# Start of Send code -------------------------------------------------------

# initialize the pi's serial port to controller parameters
# page 50 of controller manual
#ser = serial.Serial("/dev/serial0", baudrate =  38400, timeout = 2, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE)  #this is the only serial port we use on the pi
#ser.baudrate = 38400
#ser.timeout = 2
#ser.PARITY_NONE
#ser.STOPBITS_ONE
#ser.EIGHTBITS

#PACKET DEFINITION
#DRIVE ID, FUNCTION CODE, AND DATA
#set the varibles below to set the data that will be sent.
driveID = 0x08
FunctionCode = Turn_ConstSpeed #packet function code see page 53. Function Code
data = -121 #data to be sent. Data can be max speed, gear number, etc.

ToController = Send(driveID, FunctionCode, data)
#everything works, packets are sent properly, negative numbers may need to 
#be properly formatted

#Sends Binary output to console for debugging purposes
print(ToController)
for a in ToController:
    print(bin(a)[2:])

# End of Send code ---------------------------------------------------------