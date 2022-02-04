#!/usr/bin/env python3

from PIL import Image,ImageFilter, ImageEnhance, ImageDraw, ImageOps

import cv2 as cv
import numpy
from imutils import contours
import imutils
import logging
import io


BLUE_START_THRESHOLD = 40

DIGITS_LOOKUP = {
	(1, 1, 1, 0, 1, 1, 1): 0,
	(0, 0, 1, 0, 0, 1, 0): 1,
	(1, 0, 1, 1, 1, 0, 1): 2,
	(1, 0, 1, 1, 0, 1, 1): 3,
	(0, 1, 1, 1, 0, 1, 0): 4,
	(1, 1, 0, 1, 0, 1, 1): 5,
	(1, 1, 0, 1, 1, 1, 1): 6,
	(1, 1, 1, 0, 0, 1, 0): 7,
	(1, 1, 1, 1, 1, 1, 1): 8,
	(1, 1, 1, 1, 0, 1, 1): 9
}

DRAW_DIGIT_SEGMENTS = False
DRAW_DIGIT_CONTURES = False
DRAW_ILLUMINATION = False

DEFAULT_BOUNDRY_TIME = (230, 170, 455, 270)

DEFAULT_BOUNDRY_SETTEMP = (485, 145, 550, 215)
DEFAULT_BOUNDRY_WATERTEMP = (485, 265, 555, 328)

DEFAULT_BOUNDRY_MODE_ECON = (20, 140, 155, 170)
DEFAULT_BOUNDRY_MODE_AUTO = (20, 210, 155, 240)
DEFAULT_BOUNDRY_MODE_HEATER = (20, 280, 155, 310)

DEFAULT_BOUNDRY_INDICATOR_WARM = (170, 250, 225, 275)
DEFAULT_BOUNDRY_INDICATOR_HTG = (170, 155, 225, 185)
DEFAULT_BOUNDRY_INDICATOR_DEF = (170, 205, 225, 235)
DEFAULT_BOUNDRY_INDICATOR_OFF = (170, 115, 225, 145)

BOUNDRIES = [
    DEFAULT_BOUNDRY_TIME,
    DEFAULT_BOUNDRY_SETTEMP,
    DEFAULT_BOUNDRY_WATERTEMP,
    DEFAULT_BOUNDRY_MODE_AUTO,
    DEFAULT_BOUNDRY_MODE_ECON,
    DEFAULT_BOUNDRY_MODE_HEATER,
    DEFAULT_BOUNDRY_INDICATOR_WARM,
    DEFAULT_BOUNDRY_INDICATOR_HTG,
    DEFAULT_BOUNDRY_INDICATOR_DEF,
    DEFAULT_BOUNDRY_INDICATOR_OFF
    ]

THESHHOLD_ILLUMINATED = 0.66


_LOGGER = logging.getLogger(__name__)

class Deformer:

    def getmesh(self, img):
        w, h = img.size

        return [(
                # target rectangle
                (0, 0, w, h),
                # corresponding source quadrilateral
                # TOP LEFT, BOTTOM LEFT, BOTTOM RIGHT, TOP RIGHT
                (0, 0, 0, h, w*0.95, h*1, w*1.05, 0)
                )]

class Oekoboiler:

    def __init__(self):

        self._setTemperature = 0
        self._waterTemperature = 0
        self._mode = ""

        self._indicator = {
            "warm": False,
            "def": False,
            "off": False,
            "htg": False
        }

        self._boundries = {
            "time": DEFAULT_BOUNDRY_TIME,
            "setTemp": DEFAULT_BOUNDRY_SETTEMP,
            "waterTemp": DEFAULT_BOUNDRY_WATERTEMP,
            "modeAuto": DEFAULT_BOUNDRY_MODE_AUTO,
            "modeEcon": DEFAULT_BOUNDRY_MODE_ECON,
            "modeHeater": DEFAULT_BOUNDRY_MODE_HEATER,
            "indicatorWarm": DEFAULT_BOUNDRY_INDICATOR_WARM,
            "indicatorOff": DEFAULT_BOUNDRY_INDICATOR_OFF,
            "indicatorHtg": DEFAULT_BOUNDRY_INDICATOR_HTG,
            "indicatorDef": DEFAULT_BOUNDRY_INDICATOR_DEF,

        }

        self._image = None

    def setBoundries(self, boundries):
        _LOGGER.debug("Set new boundries")
        self._boundries = boundries


    def processImage(self, image):
        _LOGGER.debug("Processing image")

        w, h = image.size
        image = ImageOps.deform(image, Deformer())

        # Time
        # img_time = self.cropToBoundry(image, BOUNDRY_TIME)
        # opencv_time = cv.cvtColor(numpy.array(img_time), cv.COLOR_RGB2BGR)
        # cnts, digits, value = self.findDigits(opencv_time, "Time")
        # time = "{}{}:{}{}".format(digits[0],digits[1],digits[2],digits[3])


        # Set Temperature 
        img_setTemp = self._cropToBoundry(image, self._boundries["setTemp"])
        opencv_setTemp = cv.cvtColor(numpy.array(img_setTemp), cv.COLOR_RGB2BGR)

        try:
            cnts, digit, value = self._findDigits(opencv_setTemp, "Set Temp")
            _LOGGER.debug("Set Temperature read: {}".format(value))
            self._setTemperature = value
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Set Temperature value: %s", exc_info=1)
            self._setTemperature = None




        # Water Temperature
        img_waterTemp = self._cropToBoundry(image, self._boundries["waterTemp"])
        opencv_waterTemp = cv.cvtColor(numpy.array(img_waterTemp), cv.COLOR_RGB2BGR)

        try:
            cnts, digits,value = self._findDigits(opencv_waterTemp)
            _LOGGER.debug("Water Temperature read: {}".format(value))
            self._waterTemperature = value
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Water Temperature value: %s", exc_info=1)
            self._waterTemperature = None



        # Modus
        img_modeAuto = self._cropToBoundry(image, self._boundries["modeAuto"])
        opencv_modeAuto = cv.cvtColor(numpy.array(img_modeAuto), cv.COLOR_RGB2BGR)
        modeAuto = self._isIlluminated(opencv_modeAuto)


        img_modeEcon = self._cropToBoundry(image, self._boundries["modeEcon"])
        opencv_modeEcon = cv.cvtColor(numpy.array(img_modeEcon), cv.COLOR_RGB2BGR)
        modeEcon = self._isIlluminated(opencv_modeEcon)


        img_modeHeater = self._cropToBoundry(image, self._boundries["modeHeater"])
        opencv_modeHeater = cv.cvtColor(numpy.array(img_modeHeater), cv.COLOR_RGB2BGR)
        modeHeater = self._isIlluminated(opencv_modeHeater)


        if modeAuto:
            self._mode = "Auto"
        
        if modeEcon:
            self._mode = "Econ"

        if modeHeater:
            self._mode = "Heater"

        _LOGGER.debug("Mode read: {}".format(self._mode))

        # Indicators
        img_warmIndicator = self._cropToBoundry(image, self._boundries["indicatorWarm"], removeBlue=True)
        opencv_warmIndicator= cv.cvtColor(numpy.array(img_warmIndicator), cv.COLOR_RGB2BGR)
        self._indicator["warm"] = self._isIlluminated(opencv_warmIndicator, "warm")


        img_defIndicator = self._cropToBoundry(image, self._boundries["indicatorDef"], removeBlue=True)
        opencv_defIndicator= cv.cvtColor(numpy.array(img_defIndicator), cv.COLOR_RGB2BGR)
        self._indicator["def"] = self._isIlluminated(opencv_defIndicator, "def")


        img_htgIndicator = self._cropToBoundry(image, self._boundries["indicatorHtg"], removeBlue=True)
        opencv_htgIndicator= cv.cvtColor(numpy.array(img_htgIndicator), cv.COLOR_RGB2BGR)
        self._indicator["htg"] = self._isIlluminated(opencv_htgIndicator, "htg")


        img_offIndicator = self._cropToBoundry(image, self._boundries["indicatorOff"], removeBlue=True)
        opencv_offIndicator= cv.cvtColor(numpy.array(img_offIndicator), cv.COLOR_RGB2BGR)
        self._indicator["off"] = self._isIlluminated(opencv_offIndicator, "off")
     
    def updatedProcessedImage(self, image):

        _LOGGER.debug("Update processed Image")

        image = ImageOps.deform(image, Deformer())

        opencv_image = cv.cvtColor(numpy.array(image), cv.COLOR_RGB2BGR)

        for boundry in BOUNDRIES:
            opencv_image = cv.rectangle(opencv_image,(boundry[0], boundry[1]),(boundry[2], boundry[3]),(0,255,0),1)

        _LOGGER.debug("Saving processed Image")
        self._image = Image.fromarray(cv.cvtColor(opencv_image, cv.COLOR_BGR2RGB) )
        w, h = self._image.size
        _LOGGER.debug("Image Size: w={}, h={}".format(w,h))

    def _isIlluminated(self, image, title=""):

        h, w = image.shape[:2]
        threshold = h*w*THESHHOLD_ILLUMINATED*0.4

        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        # theshhold and morphological for cleanup
        thresh = cv.threshold(gray, 128, 255, cv.THRESH_BINARY)[1]
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, 7))
        thresh = cv.morphologyEx(thresh, cv.MORPH_DILATE, kernel)

        nonZeroValue = cv.countNonZero(thresh)

        #print ("NonZero {}, Threshhold {}".format(nonZeroValue, threshold))

        # if DRAW_ILLUMINATION and nonZeroValue > threshold:
        #     h, w = image.shape[:2]
        #     im = cv.rectangle(image,(0,0),(w,h),(0,255,0),11)

        return nonZeroValue > threshold


    def _findDigits(self, image, title=""):
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)


        # theshhold and morphological for cleanup
        thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)[1]
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (1,7))
        thresh = cv.morphologyEx(thresh, cv.MORPH_DILATE, kernel)

        im_seg = image.copy()


        # find contours
        cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        cnts = imutils.grab_contours(cnts)
        digitCnts = []

        if len(cnts) == 0:
            raise Exception("No Contures Found")

    
        # loop over the digit area candidates
        for c in cnts:
        
            # compute the bounding box of the contour
            (x, y, w, h) = cv.boundingRect(c)
            # if the contour is sufficiently large, it must be a digit
            #if w >= 15 and (h >= 40 and h <= 90):
            digitCnts.append(c)


        
        digitCnts = contours.sort_contours(digitCnts, method="left-to-right")[0]
        digits = []

        for c in digitCnts:
            # extract the digit ROI
            (x, y, w, h) = cv.boundingRect(c)

            if w <= 15:
                # its most sury a 1 Digit and we need to increase
                # the conture for the segments matching to have the full segment
                x = int(x - (w*2.5))
                w = int(w * 3.5)

            # if (DRAW_DIGIT_CONTURES):
            #     im = cv.rectangle(im,(x,y),(x+w-1,y+h-1),(0,255,0),1)


            roi = thresh[y:y + h, x:x + w]

            # compute the width and height of each of the 7 segments
            # we are going to examine
            (roiH, roiW) = roi.shape
            (dW, dH) = (int(roiW  *0.2), int(roiH *0.20))
            dHC = int(roiH * 0.1)
        

            # define the set of 7 segments
            segments = [
                ((0, 0), (w, dH)),	# top
                ((0, 0), (dW, h // 2)),	# top-left
                ((w - dW, 0), (w, h // 2)),	# top-right
                ((0, (h // 2) - dHC) , (w, (h // 2) + dHC)), # center
                ((0, h // 2), (dW, h)),	# bottom-left
                ((w - dW, h // 2), (w, h)),	# bottom-right
                ((0, h - dH), (w, h))	# bottom
            ]
            on = [0] * len(segments)

            # loop over the segments
            for (i, ((xA, yA), (xB, yB))) in enumerate(segments):

                # extract the segment ROI, count the total number of
                # thresholded pixels in the segment, and then compute
                # the area of the segment
                segROI = roi[yA:yB, xA:xB]
                
                total = cv.countNonZero(segROI)
                area = (xB - xA) * (yB - yA)
                # if the total number of non-zero pixels is greater than
                # 50% of the area, mark the segment as "on"
                if area > 0 and total / float(area) > 0.5:
                    on[i]= 1
                    # if (DRAW_DIGIT_SEGMENTS):
                    #     im_seg = cv.rectangle(im_seg,(xA+x,yA+y),(xB+x,yB+y),(255,255,255),-1)
                # else:
                #     if (DRAW_DIGIT_SEGMENTS):
                #         im_seg = cv.rectangle(im_seg,(xA+x,yA+y),(xB+x,yB+y),(0,0,0),-1)
                

            # lookup the digit and draw it on the image
            try:
                digit = DIGITS_LOOKUP[tuple(on)]
            except KeyError:
                digit = 0
            digits.append(digit)

        ## Return all contures and digits found + calcucate value with the digits
        value = 0
        num_digits = len(digits)
        for i in range(num_digits):
            value = value + digits[i] * (10**(num_digits-1-i))

        return digitCnts, digits, value


    def _cropToBoundry(self, image, boundry, convertToGray=True, removeBlue=False):

        if removeBlue:
            matrix = (
                        1, 0, 0, 0,
                        0, 1, 0, 0,
                        0, 0, 0, 0
                    )
            image = image.convert("RGB", matrix)

        if convertToGray:
            image = image.convert('L')
        
        output = image.crop(boundry)

        return output

    @property
    def setTemperature(self):
        return self._setTemperature

    @property
    def waterTemperature(self):
        return self._waterTemperature

    @property
    def mode(self):
        return self._mode

    @property
    def indicator(self):
        return self._indicator

    @property
    def image(self):
        _LOGGER.debug("Request Processes Image")

        return self._image

    @property
    def imageByteArray(self):
        _LOGGER.debug("Request Processes Image as ByteArray")

        if self._image is not None:

            img_byte_arr = io.BytesIO()
            self._image.save(img_byte_arr, format='JPEG')
        
            return img_byte_arr.getvalue()

        return None



if __name__ == "__main__":

    oekoboiler = Oekoboiler()
    oekoboiler.processImage(Image.open('boiler3.jpg'))
