#!/usr/bin/python
'''
    Author: Guido Diepen <gdiepen@deloitte.nl>
'''

#Import the OpenCV and dlib libraries
import cv2
import dlib


import threading
import time

#Initialize a face cascade using the frontal face haar cascade provided with
#the OpenCV library
#Make sure that you copy this file from the opencv project to the root of this
#project folder
faceCascade = cv2.CascadeClassifier('../haarcascade_frontalface_default.xml')

#The deisred output width and height
OUTPUT_SIZE_WIDTH = 775
OUTPUT_SIZE_HEIGHT = 600


#We are not doing really face recognition
def doRecognizePerson(faceNames, fid):
    time.sleep(2)
    faceNames[ fid ] = "Person " + str(fid)




def detectAndTrackMultipleFaces():
    #Open the first webcame device
    capture = cv2.VideoCapture(0)

    #Create two opencv named windows
    cv2.namedWindow("base-image", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("result-image", cv2.WINDOW_AUTOSIZE)

    #Position the windows next to eachother
    cv2.moveWindow("base-image",0,100)
    cv2.moveWindow("result-image",400,100)

    #Start the window thread for the two windows we are using
    cv2.startWindowThread()


    #The variable we use to keep track of the fact whether we are
    #currently using the dlib tracker
    trackingFace = 0

    #The color of the rectangle we draw around the face
    rectangleColor = (0,165,255)

    frameCounter = 0

    currentFaceID = 0

    faceTrackers = {}

    faceNames = {}

    try:
        while True:
            #Retrieve the latest image from the webcam
            rc,fullSizeBaseImage = capture.read()

            #Resize the image to 320x240
            baseImage = cv2.resize( fullSizeBaseImage, ( 320, 240))


            #Check if a key was pressed and if it was Q, then destroy all
            #opencv windows and exit the application
            pressedKey = cv2.waitKey(2)
            if pressedKey == ord('Q'):
                cv2.destroyAllWindows()
                exit(0)



            #Result image is the image we will show the user, which is a
            #combination of the original image from the webcam and the
            #overlayed rectangle for the largest face
            resultImage = baseImage.copy()




            #STEPS:
            # * Update all trackers and remove the ones that are not 
            #   relevant anymore
            # * if framecounter >= 5:
            #       + Use face detection on the current frame and look
            #         for faces. 
            #       + For each found face, check if centerpoint is within
            #         existing tracked box. If so, nothing to do
            #       + If centerpoint is NOT in existing tracked box, then
            #         we add a new tracker with a new face-id


            #Increase the framecounter
            frameCounter += 1 


            fidsToDelete = []


            #Update all the trackers
            for fid in faceTrackers.keys():
                trackingQuality = faceTrackers[ fid ].update( baseImage )

                #If the tracking quality is good enough, we must delete
                #this tracker
                if trackingQuality < 7:
                    fidsToDelete.append( fid )

            for fid in fidsToDelete:
                print("Removing fid " + str(fid) + " from list of trackers")
                faceTrackers.pop( fid , None )




            #Every 10 frames, we will have to determine which faces
            #are present in the frame
            if (frameCounter % 10) == 0:



                #print("********************************************************************************")
                #For the face detection, we need to make use of a gray
                #colored image so we will convert the baseImage to a
                #gray-based image
                gray = cv2.cvtColor(baseImage, cv2.COLOR_BGR2GRAY)
                #Now use the haar cascade detector to find all faces
                #in the image
                faces = faceCascade.detectMultiScale(gray, 1.3, 5)



                #Loop over all faces and check if the area for this
                #face is the largest so far
                #We need to convert it to int here because of the
                #requirement of the dlib tracker. If we omit the cast to
                #int here, you will get cast errors since the detector
                #returns numpy.int32 and the tracker requires an int
                for (_x,_y,_w,_h) in faces:
                    x = int(_x)
                    y = int(_y)
                    w = int(_w)
                    h = int(_h)


                    #calculate the centerpoint
                    x_bar = x + 0.5 * w
                    y_bar = y + 0.5 * h




                    matchedFid = None

                    #Now loop over all the trackers and check if the 
                    #centerpoint of the face is within the box of a 
                    #tracker
                    for fid in faceTrackers.keys():
                        tracked_position =  faceTrackers[fid].get_position()

                        t_x = int(tracked_position.left())
                        t_y = int(tracked_position.top())
                        t_w = int(tracked_position.width())
                        t_h = int(tracked_position.height())

                        #check if the centerpoint of the face is within the rectangle
                        #of a tracker region
                        if ( t_x <= x_bar <= (t_x + t_w) ) and (  t_y <= y_bar <= (t_y + t_h)):
                            matchedFid = fid


                    #If no matched fid, then add a new one
                    if matchedFid is None:


                        tracker = dlib.correlation_tracker()
                        tracker.start_track(baseImage,
                                            dlib.rectangle( x-10,
                                                            y-20,
                                                            x+w+10,
                                                            y+h+20))

                        print("Creating new tracker " + str(currentFaceID))
                        faceTrackers[ currentFaceID ] = tracker

                        t = threading.Thread( target = doRecognizePerson , args=( faceNames, currentFaceID))
                        t.start()

                        currentFaceID += 1



            for fid in faceTrackers.keys():
                tracked_position =  faceTrackers[fid].get_position()

                t_x = int(tracked_position.left())
                t_y = int(tracked_position.top())
                t_w = int(tracked_position.width())
                t_h = int(tracked_position.height())

                cv2.rectangle(resultImage, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        rectangleColor ,2)


                if fid in faceNames.keys():
                    cv2.putText(resultImage, faceNames[fid] , (int(t_x + t_w/2), int(t_y)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255), 2)
                else:
                    cv2.putText(resultImage, "Detecting..." , (int(t_x + t_w/2), int(t_y)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255), 2)






            #Since we want to show something larger on the screen than the
            #original 320x240, we resize the image again
            #
            #Note that it would also be possible to keep the large version
            #of the baseimage and make the result image a copy of this large
            #base image and use the scaling factor to draw the rectangle
            #at the right coordinates.
            largeResult = cv2.resize(resultImage,
                                     (OUTPUT_SIZE_WIDTH,OUTPUT_SIZE_HEIGHT))

            #Finally, we want to show the images on the screen
            cv2.imshow("base-image", baseImage)
            cv2.imshow("result-image", largeResult)




    #To ensure we can also deal with the user pressing Ctrl-C in the console
    #we have to check for the KeyboardInterrupt exception and destroy
    #all opencv windows and exit the application
    except KeyboardInterrupt as e:
        cv2.destroyAllWindows()
        exit(0)


if __name__ == '__main__':
    detectAndTrackMultipleFaces()
