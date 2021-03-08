"""Quadcopter Interceptor project
Mouse click select using screen in lab
Simple peak min value of rows and clmns summed method
YUV 'Y' only , not RGB
RaspividYUV used
How to use:
run program,
left click on target (this is in slow mode~55ms due to waitkey +)
right click anywhere on image window to go into 'stopshowing' mode, or fast mode ~12ms or faster
   this mode automatically records some # (set here "if len(tp0)>700:" ast 700)
   automatic exit causes plot of tpoint x and y axis in time and save jpegs of every frame with target box marked
Press <esc> to quit from slow mode
"""
#
#tracks using only 'blue' minimum x and y magnitude point
#ccblobfinder works, but not used in tracking
#
#
#this is not using python enviroments #!/usr/bin/env python3
import cv2
import time
from matplotlib import pyplot as plt
import os #for CPU temperature
import array #stock python array handling
import serial #serial port
import numpy as np
import subprocess as sp #for streaming frames
import atexit
import sys

readin = bytearray(25) #'bytearray'init the array bytes to read in
sendout = bytearray(25)
La = list(range(16)) #0 to 15 ; 16 positions
Ld = list(range(4)) #0 to 15 ; 16 positions
achannel = array.array('I',La) #initialize a basic python array as 'I' is unsigned integer, 2 bytes
digichannel = array.array('I',Ld) #initialize a basic python array

rstickhorz = int
stickvert = int

(w,h) = (640,480)#(640,480) mode 7 for 120fps / (1280,720) mode 6 for 90fps
bytesPerFrame = w * h
fps = 120

# ---- Function definition for converting scales ------
# def remap(unscaled, to_min, to_max, from_min, from_max):
#     return (to_max-to_min)*(unscaled-from_min)/(from_max-from_min)+to_min

#----Function to measure CPU temp  use print(measure_temp())
def measure_temp():
        temp = os.popen("vcgencmd measure_temp").readline()
        return (temp.replace("temp=",""))

# #---- Function Timer, returns current time
# def how_long(start, activity):
#     print('%s time %.3fs' % (activity, time.time()-start))
#     return time.time()

def stop_loop(frame,cameraProcess):#break jumps us out of inner most loop and used in an if statement of the loop
    global imagestor
    global stopshowing
    global tp0
    global tp1
    print(measure_temp())
    print(type(frame))
    print(frame.shape)
    print(frame.dtype)
#    cv2.waitKey(100)
    cv2.destroyAllWindows()
    cameraProcess.terminate() # stop the camera
    if stopshowing==1:#only plot the recorded tpoint values if we went into the stopshowing mode that runs very quick
        for nmbr in range(0,len(imagestor)):
            if nmbr < 10:
                cv2.imwrite('RVd000'+str(nmbr)+'.jpg',imagestor[nmbr])
            elif nmbr<100:
                cv2.imwrite('RVd00'+str(nmbr)+'.jpg',imagestor[nmbr])
            else:
                cv2.imwrite('RVd0'+str(nmbr)+'.jpg',imagestor[nmbr])
        fig=plt.figure()
        plt.subplot(121)
        plt.plot(tp0)
        plt.subplot(122)
        plt.plot(tp1)
        plt.show()
    
def parse_serin(readin):#Bitwise or is |, regular or is ||   #Bitwise and is &, regular and is &&
    achannel[0]  = ((readin[1]     | readin[2]<<8)                   & 0x07FF)
    achannel[1]  = ((readin[2]>>3  | readin[3]<<5)                   & 0x07FF)
    achannel[2]  = ((readin[3]>>6  | readin[4]<<2 | readin[5]<<10)   & 0x07FF)
    achannel[3]  = ((readin[5]>>1  | readin[6]<<7)                   & 0x07FF)
    achannel[4]  = ((readin[6]>>4  | readin[7]<<4)                   & 0x07FF)
    achannel[5]  = ((readin[7]>>7  | readin[8]<<1 | readin[9]<<9)    & 0x07FF)
    achannel[6]  = ((readin[9]>>2  | readin[10]<<6)                  & 0x07FF)
    achannel[7]  = ((readin[10]>>5 | readin[11]<<3)                  & 0x07FF)
    achannel[8]  = ((readin[12]    | readin[13]<<8)                  & 0x07FF)
    achannel[9]  = ((readin[13]>>3 | readin[14]<<5)                  & 0x07FF)
    achannel[10] = ((readin[14]>>6 | readin[15]<<2 | readin[16]<<10) & 0x07FF)
    achannel[11] = ((readin[16]>>1 | readin[17]<<7)                  & 0x07FF)
    achannel[12] = ((readin[17]>>4 | readin[18]<<4)                  & 0x07FF)
    achannel[13] = ((readin[18]>>7 | readin[19]<<1 |readin[20]<<9)   & 0x07FF)
    achannel[14] = ((readin[20]>>2 | readin[21]<<6)                  & 0x07FF)
    achannel[15] = ((readin[21]>>5 | readin[22]<<3)                  & 0x07FF)

def parse_serout(achannel,readin):#digichannel):
    sendout[0] = 0x0F #valid first byte to flight controller
    sendout[1] =  (achannel[0]  & 0x07FF) & 0xFF #07FF is 11111111111 to filter value to 11bit
    sendout[2] =  (((achannel[0]  & 0x07FF) >> 8)  | ((achannel[1] << 3) & 0x07FF)) & 0xFF
    sendout[3] =  (((achannel[1]  & 0x07FF) >> 5)  | ((achannel[2] << 6) & 0x07FF)) & 0xFF
    sendout[4] =  ((achannel[2]  & 0x07FF) >> 2) & 0xFF
    sendout[5] =  (((achannel[2]  & 0x07FF) >> 10) | ((achannel[3] << 1) & 0x07FF)) & 0xFF
    sendout[6] =  (((achannel[3]  & 0x07FF) >> 7)  | ((achannel[4] << 4) & 0x07FF)) & 0xFF
    sendout[7] =  (((achannel[4]  & 0x07FF) >> 4)  | ((achannel[5] << 7) & 0x07FF)) & 0xFF
    sendout[8] =  ((achannel[5]  & 0x07FF) >> 1) & 0xFF
    sendout[9] =  (((achannel[5]  & 0x07FF) >> 9)  | ((achannel[6] << 2) & 0x07FF)) & 0xFF
    sendout[10] = (((achannel[6]  & 0x07FF) >> 6)  | ((achannel[7] << 5) & 0x07FF)) & 0xFF
    sendout[11] = ((achannel[7]  & 0x07FF) >> 3) & 0xFF
    sendout[12] = (achannel[8]  & 0x07FF) & 0xFF
    sendout[13] = (((achannel[8]  & 0x07FF) >> 8)  | ((achannel[9] << 3) & 0x07FF)) & 0xFF
    sendout[14] = (((achannel[9]  & 0x07FF) >> 5)  | ((achannel[10] << 6) & 0x07FF)) & 0xFF
    sendout[15] = ((achannel[10] & 0x07FF) >> 2) & 0xFF
    sendout[16] = (((achannel[10] & 0x07FF) >> 10) | ((achannel[11] << 1) & 0x07FF)) & 0xFF
    sendout[17] = (((achannel[11] & 0x07FF) >> 7)  | ((achannel[12] << 4) & 0x07FF)) & 0xFF
    sendout[18] = (((achannel[12] & 0x07FF) >> 4)  | ((achannel[13] << 7) & 0x07FF)) & 0xFF
    sendout[19] = ((achannel[13] & 0x07FF) >> 1) & 0xFF
    sendout[20] = ((achannel[13] & 0x07FF) >> 9  | (achannel[14] & 0x07FF) << 2) & 0xFF
    sendout[21] = ((achannel[14] & 0x07FF) >> 6  | (achannel[15] & 0x07FF) << 5) & 0xFF
    sendout[22] = ((achannel[15] & 0x07FF) >> 3) & 0xFF
    sendout[23]=readin[23];#no digichannels used on Radiolink AT9S
    sendout[24]=readin[24];#footer byte 0x00

def return_mouse_click(event,x,y,flags,param):#special var return via global vars
    global tpoint
    global clickflag
    global stopshowing
    print("Mouse ",repr(event))
    if event == 1:#left mouse button depress
        clickflag=1 #simple_tracker will automatically calc new luminosity value for this pixel and surrounding
        tpoint=(x,y)        
    if event ==5:#right mouse click
        stopshowing=1#used for high speed testing without cv2.waitKey...to break
    return tpoint#manually set a new target center(tpoint) with mouse click


def simple_tracker(tpoint,width,frame):#tpoint is [x,y] / width is frame width / frame is total camera pict
    global clickflag
    global SelctPtVal
#     width=300
    newwidth=width
    #
    #if Target is dark,low values, wrt background; then expect Target values to be low
#    start=time.time()
    halfwidth=width/2
    x1=int(tpoint[0]-(halfwidth))
    y1=int(tpoint[1]-(halfwidth))
    x2=int(tpoint[0]+(halfwidth))
    y2=int(tpoint[1]+(halfwidth))
    if x1<0:
        x1=int(0)
        x2=int(x1+width)
    if y1<0:
        y1=int(0)
        y2=int(y1+width)
    if x2>(w-1):
        x2=int((w-1))
        x1=int(x2-width)
    if y2>(h-1):
        y2=int((h-1))
        y1=int(y2-width)
    oldbox=(int(x1),int(y1),int(x2),int(y2))#old box
    subframe=frame[int(y1):int(y2),int(x1):int(x2)]#smaller tracking frame inside large image frame
#    print('subframe size = ',subframe.shape)
    if clickflag==1:#when user selects target, perform threshold calc
        sv1=frame[tpoint[1]-1,tpoint[0]-1]
        sv2=frame[tpoint[1]-1,tpoint[0]]
        sv3=frame[tpoint[1]-1,tpoint[0]+1]
        sv4=frame[tpoint[1],tpoint[0]-1]
        sv5=frame[tpoint[1],tpoint[0]]
        sv6=frame[tpoint[1],tpoint[0]+1]
        sv7=frame[tpoint[1]+1,tpoint[0]-1]
        sv8=frame[tpoint[1]+1,tpoint[0]]
        sv9=frame[tpoint[1]+1,tpoint[0]+1]
        SelctPtVal=(sv1+sv2+sv3+sv4+sv5+sv6+sv7+sv8+sv9)/9#applies to BandPass
        clickflag=0
    x=80.00#pixel magnitude width
    halfx=x/2#use half magnitude to go up and down from user selected pixel target point
#only good for dark objects less
    #BandPass processing
#     LoPassVal=int(SelctPtVal+halfx)
#     if LoPassVal>254:
#         LoPassVal=254
#     HiPassVal=int(SelctPtVal-halfx)
#     if HiPassVal<2:  #this sequence ends with inverted image because we track a 'dark' object on a bright background
#         HiPassVal=2  #first do HiPass shift down and then invert to add LoPass, this sequence matters!
#     HiPass=subframe-HiPassVal#shift it down
#     HiPass=np.clip(HiPass,0,255)#clip all neg values to 0
#     LoPass=halfx-HiPass#invert image and shift up; all values more than (SelctPtVal+halfx) become zero
#     BandPass=np.clip(LoPass,0,255)
#    print('width = ',width)
#    print('SelctPtVal = ',SelctPtVal)
#    print('BandPass MAX = ',np.amax(BandPass))
#    print('BandPass min = ',np.amin(BandPass))
#    print('Bandpass size = ',BandPass.shape)
    #End of BandPass processing
    BandPass=255-subframe#skip doing real BandPass, just pass thru subframe
    sumx=np.sum(BandPass,axis=0)
    sumy=np.sum(BandPass,axis=1)
    if sumx.size > 1:
        sxMax=np.argmax(sumx)#pixel x location where min occurs
        if sumy.size > 1:
            syMax=np.argmax(sumy)
            tpoint=(int(sxMax+x1),int(syMax+y1))#tpoint is absolute to camera image frame
    x1=int(tpoint[0]-(halfwidth))
    y1=int(tpoint[1]-(halfwidth))
    x2=int(tpoint[0]+(halfwidth))
    y2=int(tpoint[1]+(halfwidth))
    if x1<0:
        x1=int(0)
        x2=int(x1+width)
    if y1<0:
        y1=int(0)
        y2=int(y1+width)
    if x2>(w-1):
        x2=int((w-1))
        x1=int(x2-width)
    if y2>(h-1):
        y2=int((h-1))
        y1=int(y2-width)
    newbox=(int(x1),int(y1),int(x2),int(y2))#new box
    return tpoint,newwidth,subframe,newbox,BandPass,sumx,sumy#subframe,subframeG,subframeR#bbox

def main():
    global tpoint
    global SelctPtVal
    global clickflag
    global stopshowing
    global showblob
    global tp0
    global tp1
    global imagestor
    tp0=[]#x vals list to keep tpoints history
    tp1=[]#y vals
#     global w#camera frame
#     global h#camera frame
    #
    clickflag=0#flag indicating mouse click or target selection
    stopshowing=0
    loop=1#while loop control
    trackerinit=2#0=user has new targeting / 1=tracker running / 2=program start nothing happening
    params = cv2.SimpleBlobDetector_Params
    rsh = np.empty(0) #right stick horz center bias (trim)
    rsv = np.empty(0) #right stick vert center bias (trim)
    #
    ser = serial.Serial(#init serial
    port='/dev/ttyAMA0',
    baudrate=100000,
    bytesize=8,
    parity='E',
    stopbits=2,
    timeout=None,
    )
    #set up 
    tpoint=(int(w/2), int(h/2))
    width=50
    SelctPtVal=int(127)
#
    cv2.namedWindow("Show", cv2.WINDOW_NORMAL)#Declare the image window
    cv2.resizeWindow("Show",w,h)
    cv2.setMouseCallback('Show',return_mouse_click)#event driven hook to this window
    #
#     cv2.namedWindow("BandPass", cv2.WINDOW_NORMAL)#Declare the image window
#     cv2.resizeWindow("BandPass",w,h)

##    cv2.setWindowProperty("Show",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)#fullscreen for FPV use
    #
#Pi Camera Setup w, h, and fps at beginning of program
    # see "raspividyuv --help" for more information on the parameters
    #videoCmd = "raspividyuv -w "+str(w)+" -h "+str(h)+" --output - --timeout 0 --framerate "+str(fps)+" --luma --nopreview"
    videoCmd = "raspividyuv -w "+str(w)+" -h "+str(h)+" --output - --timeout 0 --framerate "+str(fps)+" --luma --nopreview --mode 7"
    videoCmd = videoCmd.split() # Popen requires that each parameter is a separate string
    #Pi Camera Setup Complete
    cameraProcess = sp.Popen(videoCmd, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=((w*h)+20)) # start the camera
    atexit.register(cameraProcess.terminate) # this closes the camera process in case the python scripts exits unexpectedly
    #Pi Camera subprocess started above
    rawStream = cameraProcess.stdout.read(bytesPerFrame)
#     print(sys.getsizeof(rawStream))
    cameraProcess.stdout.flush()#be sure to clear the buffer
    if sys.getsizeof(rawStream) == ((w*h)+17):#cam function check, expect to get 1 byte for every pixel pluse 17(?metadata?) bytes, 921617(1280,720)
        frame=np.frombuffer(rawStream, dtype=np.uint8)
        frame=frame[0:bytesPerFrame]#get frame, first time in this program
        frame.shape=(h,w)

#     time.sleep(0.5)#camera warmup for half second
    #
    time.sleep(.05)#must init & warm-up cam, this frame usually takes .250sec
    n=int(0)
    imagestor=[]#list of images store to see later
    start=time.time()
    while loop==1:#*******************************************
        rawStream = cameraProcess.stdout.read(bytesPerFrame)
#     print(sys.getsizeof(rawStream))
        cameraProcess.stdout.flush()#be sure to clear the buffer
        if sys.getsizeof(rawStream) == ((w*h)+17):#cam function check, expect to get 1 byte for every pixel pluse 17(?metadata?) bytes, 921617(1280,720)
            frame=np.frombuffer(rawStream, dtype=np.uint8)
            frame=frame[0:bytesPerFrame]
            frame.shape=(h,w)
        tpoint,newwidth,subframe,box,BandPass,sumx,sumy= simple_tracker(tpoint,width,frame)#returns: tpoint,newwidth,subframe,box,BandPass,sumx,sumy
        frame
        if stopshowing==1:
            tp0.append(tpoint[0])#record tpoint to plt later
            tp1.append(tpoint[1])
            cv2.rectangle(frame,(int(box[0]),int(box[1])),(int(box[2]),int(box[3])),(0,0,255),2)#0.5ms
            imagestor.append(frame)
            if len(tp0)>700:#do not go more than 330 (1280/720)  or 800 640/480 due to  memory issues.
                stop_loop(frame,cameraProcess)
                break
#             print(time.time()-start,' high Speed')
        if stopshowing==0:
            cv2.rectangle(frame,(int(box[0]),int(box[1])),(int(box[2]),int(box[3])),(0,0,255),2)#0.5ms
            cv2.line(frame,(int(tpoint[0]),0),(int(tpoint[0]),int(frame.shape[0]-1)),(0,255,0),1)#0.5ms
            cv2.line(frame,(0,int(tpoint[1])),(int(frame.shape[1]-1),int(tpoint[1])),(0,255,0),1)#0.5ms
            cv2.imshow("Show", frame)# Display result
#
            if cv2.waitKey(50) == 27:# esc to quit; this .waitKey consumes at least 22ms time
                stop_loop(frame,cameraProcess)
                break
#             print(time.time()-start,' Show and breakwait')
        start=time.time()
#        print(np.amax(BandPass),' BandPass max val')
#        print(np.amin(BandPass),' BandPass min val')
        width=newwidth#set new width of track frame

if __name__ == '__main__':
    main()
