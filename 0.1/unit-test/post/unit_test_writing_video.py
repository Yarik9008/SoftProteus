from importlib.resources import path
import cv2
import numpy as np
from datetime import datetime


PATCH  = '/home/yarik9001/video_proteus/'

# Create a VideoCapture object

cap = cv2.VideoCapture(0)

# Check if camera opened successfully

if (cap.isOpened() == False):
    print("Unable to read camera feed")

# Default resolutions of the frame are obtained.The default resolutions are system dependent.

# We convert the resolutions from float to integer.

frame_width = int(cap.get(3))
height = int(cap.get(4))

# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.

name  = PATCH + 'record' + '-'.join('-'.join('-'.join(str(datetime.now()).split()).split('.')).split(':')) + '.avi'



out = cv2.VideoWriter(name ,cv2.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,height))

 

while(True):
    ret, frame = cap.read()
    if ret == True:
        out.write(frame)

        cv2.imshow('frame',frame)

    # Press Q on keyboard to stop recording
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break 

cap.release()
out.release()

 

# Closes all the frames

cv2.destroyAllWindows()
