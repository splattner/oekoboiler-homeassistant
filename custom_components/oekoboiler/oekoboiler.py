#!/usr/bin/env python3

import re
from PIL import Image,ImageFilter, ImageEnhance, ImageDraw, ImageOps

import cv2 as cv
import numpy
from imutils import contours
import imutils
import logging
import io
import os
import requests


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

DEFAULT_BOUNDRY_TIME = (242, 160, 453, 245)

DEFAULT_BOUNDRY_SETTEMP = (498, 137, 555, 193)
DEFAULT_BOUNDRY_WATERTEMP = (505, 259, 563, 310)

DEFAULT_BOUNDRY_MODE_ECON = (15, 120, 150, 145)
DEFAULT_BOUNDRY_MODE_AUTO = (15, 190, 150, 215)
DEFAULT_BOUNDRY_MODE_HEATER = (15, 260, 150, 285)

DEFAULT_BOUNDRY_INDICATOR_WARM = (170, 235, 225, 260)
DEFAULT_BOUNDRY_INDICATOR_HTG = (170, 140, 225, 170)
DEFAULT_BOUNDRY_INDICATOR_DEF = (170, 190, 225, 220)
DEFAULT_BOUNDRY_INDICATOR_OFF = (170, 100, 225, 130)

DEFAULT_THESHHOLD_ILLUMINATED = 66

IMAGE_SPACING = 10


_LOGGER = logging.getLogger(__name__)

class Deformer:

    def getmesh(self, img):
        w, h = img.size

        return [(
                # target rectangle
                (0, 0, w, h),
                # corresponding source quadrilateral
                # TOP LEFT, BOTTOM LEFT, BOTTOM RIGHT, TOP RIGHT
                (0, 0, 0, h, w*0.91, h*1, w*1.05, 0)
                )]

class Oekoboiler:

    def __init__(self):

        self._setTemperature = 0
        self._waterTemperature = 0
        self._mode = ""
        self._state = ""
        self._time = ""

        self._indicator = {
            "off": False,
            "htg": False,
            "def": False,
            "warm": False,
        }

        self._boundries = {
            "time": DEFAULT_BOUNDRY_TIME,
            "setTemp": DEFAULT_BOUNDRY_SETTEMP,
            "waterTemp": DEFAULT_BOUNDRY_WATERTEMP,
            "modeEcon": DEFAULT_BOUNDRY_MODE_ECON,
            "modeAuto": DEFAULT_BOUNDRY_MODE_AUTO,
            "modeHeater": DEFAULT_BOUNDRY_MODE_HEATER,
            "indicatorOff": DEFAULT_BOUNDRY_INDICATOR_OFF,
            "indicatorHtg": DEFAULT_BOUNDRY_INDICATOR_HTG,
            "indicatorDef": DEFAULT_BOUNDRY_INDICATOR_DEF,
            "indicatorWarm": DEFAULT_BOUNDRY_INDICATOR_WARM,
        }

        self._threshhold_illumination = DEFAULT_THESHHOLD_ILLUMINATED / 100

        self._image = dict()


    def setBoundries(self, boundries):
        _LOGGER.debug("Set new boundries")
        self._boundries = boundries

        _LOGGER.debug("new Boundries {}".format(self._boundries))

    def setThreshholdIllumination(self, threshhold: int):
        _LOGGER.debug("Set new Threshold")
        self._threshhold_illumination = threshhold / 100

        _LOGGER.debug("new Threshold {}".format(self._threshhold_illumination))


    def processImage(self, original_image):
        _LOGGER.debug("Processing image")
        _LOGGER.debug("Boundries {}".format(self._boundries))

        w, h = original_image.size
        image = ImageOps.deform(original_image, Deformer())


        #Time
        img_time = self._cropToBoundry(image, self._boundries["time"], removeBlue=True)
        opencv_time = cv.cvtColor(numpy.array(img_time), cv.COLOR_RGB2BGR)
        cnts, digits, value = self._findDigits(opencv_time, "time")
        if len(digits) == 4:
            self._time = "{}{}:{}{}".format(digits[0],digits[1],digits[2],digits[3])
        else:
            self._time = "undef"


        # Set Temperature 
        img_setTemp = self._cropToBoundry(image, self._boundries["setTemp"])
        opencv_setTemp = cv.cvtColor(numpy.array(img_setTemp), cv.COLOR_RGB2BGR)

        try:
            cnts, digit, value = self._findDigits(opencv_setTemp, "setTemp", k=(1,4))
            _LOGGER.debug("Set Temperature read: {}".format(value))
            self._setTemperature = value
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Set Temperature value: %s", exc_info=1)
            self._setTemperature = None



        # Water Temperature
        img_waterTemp = self._cropToBoundry(image, self._boundries["waterTemp"])
        opencv_waterTemp = cv.cvtColor(numpy.array(img_waterTemp), cv.COLOR_RGB2BGR)

        try:
            cnts, digits,value = self._findDigits(opencv_waterTemp, "waterTemp", k=(1,4))
            _LOGGER.debug("Water Temperature read: {}".format(value))
            self._waterTemperature = value
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Water Temperature value: %s", exc_info=1)
            self._waterTemperature = None



        # Modus
        img_modeAuto = self._cropToBoundry(image, self._boundries["modeAuto"])
        opencv_modeAuto = cv.cvtColor(numpy.array(img_modeAuto), cv.COLOR_RGB2BGR)
        modeAuto = self._isIlluminated(opencv_modeAuto, "modeAuto")


        img_modeEcon = self._cropToBoundry(image, self._boundries["modeEcon"])
        opencv_modeEcon = cv.cvtColor(numpy.array(img_modeEcon), cv.COLOR_RGB2BGR)
        modeEcon = self._isIlluminated(opencv_modeEcon, "modeEcon")


        img_modeHeater = self._cropToBoundry(image, self._boundries["modeHeater"])
        opencv_modeHeater = cv.cvtColor(numpy.array(img_modeHeater), cv.COLOR_RGB2BGR)
        modeHeater = self._isIlluminated(opencv_modeHeater, "modeHeater")


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
        self._indicator["warm"] = self._isIlluminated(opencv_warmIndicator, "indicatorWarm")


        img_defIndicator = self._cropToBoundry(image, self._boundries["indicatorDef"], removeBlue=True)
        opencv_defIndicator= cv.cvtColor(numpy.array(img_defIndicator), cv.COLOR_RGB2BGR)
        self._indicator["def"] = self._isIlluminated(opencv_defIndicator, "indicatorDef")


        img_htgIndicator = self._cropToBoundry(image, self._boundries["indicatorHtg"], removeBlue=True)
        opencv_htgIndicator= cv.cvtColor(numpy.array(img_htgIndicator), cv.COLOR_RGB2BGR)
        self._indicator["htg"] = self._isIlluminated(opencv_htgIndicator, "indicatorHtg")


        img_offIndicator = self._cropToBoundry(image, self._boundries["indicatorOff"], removeBlue=True)
        opencv_offIndicator= cv.cvtColor(numpy.array(img_offIndicator), cv.COLOR_RGB2BGR)
        self._indicator["off"] = self._isIlluminated(opencv_offIndicator, "indicatorOff")

        if self._indicator["warm"]:
            self._state = "Warm"

        if self._indicator["def"]:
            self._state = "Defrosting"

        if self._indicator["htg"]:
            self._state = "Heating"

        if self._indicator["off"]:
            self._state = "Off"

        self.updatedProcessedImage(original_image)
     
    def updatedProcessedImage(self, original_image):

        _LOGGER.debug("Update processed Image")
        _LOGGER.debug("Boundries {}".format(self._boundries))

        image = ImageOps.deform(original_image, Deformer())

        opencv_image = cv.cvtColor(numpy.array(image), cv.COLOR_RGB2BGR)

        for key, value in self._boundries.items():
            opencv_image = cv.rectangle(opencv_image,(value[0], value[1]),(value[2], value[3]),(0,255,0),1)
            opencv_image = cv.putText(opencv_image, key, (value[0], value[1]), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1, cv.LINE_AA)

        _LOGGER.debug("Saving processed Image")
        self._image["processed_image"] = Image.fromarray(cv.cvtColor(opencv_image, cv.COLOR_BGR2RGB))

    def _isIlluminated(self, image, title=""):

        h, w = image.shape[:2]
        threshold = h*w*self._threshhold_illumination*0.4

        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        # theshhold and morphological for cleanup
        thresh = cv.threshold(gray, 70, 255, cv.THRESH_BINARY)[1]
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, 7))
        thresh = cv.morphologyEx(thresh, cv.MORPH_DILATE, kernel)

        nonZeroValue = cv.countNonZero(thresh)

        _LOGGER.debug("NonZero {}, Threshhold {}".format(nonZeroValue, threshold))

        if title is not None:
            if nonZeroValue > threshold:
                h, w = image.shape[:2]
                image = cv.rectangle(image,(0,0),(w,h),(0,255,0),11)
            self._image[title] = Image.fromarray(cv.cvtColor(thresh, cv.COLOR_BGR2RGB))

        return nonZeroValue > threshold


    def _findDigits(self, image, title="", segment_resize_factor=1, k=(1,7)):
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)


        # theshhold and morphological for cleanup
        thresh = cv.threshold(gray, 100, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)[1]
        kernel = cv.getStructuringElement(cv.MORPH_RECT, k)
        morph = cv.morphologyEx(thresh, cv.MORPH_DILATE, kernel)

        im_seg = cv.cvtColor(morph.copy(), cv.COLOR_GRAY2BGR)

        # im_seg = image.copy()


        # find contours
        cnts = cv.findContours(morph.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        cnts = imutils.grab_contours(cnts)
        digitCnts = []

        if len(cnts) == 0:
            raise Exception("No Contures Found")

    
        # loop over the digit area candidates
        for c in cnts:
        
            # compute the bounding box of the contour
            (x, y, w, h) = cv.boundingRect(c)
            
            # Draw rectacle for all candidates
            # print("Candidat Width {} Height {}".format(w,h))
            im_seg = cv.rectangle(im_seg,(x-1,y-1),(x+w-1+1,y+h-1+1),(255,255,0),1)
            # if the contour is sufficiently large, it must be a digit
            if w >= 10 and (h >= 40 and h <= 100):
                digitCnts.append(c)


        digitCnts = contours.sort_contours(digitCnts, method="left-to-right")[0]
        digits = []

        for c in digitCnts:
            # extract the digit ROI
            (x, y, w, h) = cv.boundingRect(c)

            # print("Width {} Height {}".format(w,h))

            if w <= 15:
                # its most sury a 1 Digit and we need to increase
                # the conture for the segments matching to have the full segment
                x = int(x - (w*2.5))
                w = int(w * 3.5)


            im_seg = cv.rectangle(im_seg,(x-1,y-1),(x+w-1+1,y+h-1+1),(0,255,0),1)


            roi = thresh[y:y + h, x:x + w]

            # compute the width and height of each of the 7 segments
            # we are going to examine
            (roiH, roiW) = roi.shape
            (dW, dH) = (int(roiW  *0.24 * segment_resize_factor ), int(roiH *0.16 * segment_resize_factor))
            dHC = int(roiH * 0.13 * segment_resize_factor)
        

            # define the set of 7 segments
            segments = [
                ((0 + dW // 2, 0), (w - dW // 2, dH)),	# top
                ((0, 0 + dH // 2), (dW, h // 2 - dHC // 4)),	# top-left
                ((w - dW, 0 + dH // 2), (w, h // 2 - dHC // 4)),	# top-right
                ((0 + dW // 2, (h // 2) - dHC // 2) , (w - dW // 2, (h // 2) + dHC // 2)), # center
                ((0, h // 2 + dHC // 4), (dW, h - dH // 2)),	# bottom-left
                ((w - dW, h // 2 + dHC // 4), (w, h - dH // 2)),	# bottom-right
                ((0 + dW // 2, h - dH), (w - dW // 2, h))	# bottom
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
                #print ("Title {} Segment {} Area {} Total {}".format(title, i, area,total))
                if area > 0 and total / float(area) > 0.4:
                    on[i]= 1
                    
                    im_seg = cv.rectangle(im_seg,(xA+x,yA+y),(xB+x,yB+y),(255,0,0),-1)
                else:
                    im_seg = cv.rectangle(im_seg,(xA+x,yA+y),(xB+x,yB+y),(70,70,70),-1)
            
            if title is not None:
                self._image["{}_segments".format(title)] = Image.fromarray(cv.cvtColor(im_seg, cv.COLOR_BGR2RGB))
                self._image["{}_thresh".format(title)] = Image.fromarray(cv.cvtColor(thresh, cv.COLOR_BGR2RGB))
                self._image["{}_morph".format(title)] = Image.fromarray(cv.cvtColor(morph, cv.COLOR_BGR2RGB))

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

    def _getBoundryWidth(self, boundry):
        return boundry[2] - boundry[0]

    def _getBoundryHeight(self, boundry):
        return boundry[3] - boundry[1]

    @property
    def time(self):
        return self._time

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
    def state(self):
        return self._state

    @property
    def indicator(self):
        return self._indicator

    @property
    def image(self):
        _LOGGER.debug("Request Processes Image")

        return self._image["processed_image"]

    @property
    def imageByteArray(self):
        _LOGGER.debug("Request Processes Image as ByteArray")

        if "processed_image" in self._image and self._image["processed_image"] is not None:
            w_processedImage, h_processedImage = self._image["processed_image"].size
            
            
            # Get Max with for indicators
            w_indicator = 0
            for indicator in ["indicatorOff", "indicatorHtg","indicatorDef","indicatorWarm"]:
                if self._getBoundryWidth(self._boundries[indicator]) > w_indicator:
                    w_indicator = self._getBoundryWidth(self._boundries[indicator]) 

            # Get Max with for modes
            w_mode = 0
            for indicator in ["modeEcon","modeAuto","modeHeater"]:
                if self._getBoundryWidth(self._boundries[indicator]) > w_mode:
                    w_mode = self._getBoundryWidth(self._boundries[indicator])

            # Width and Height of setTemp Images
            w_setTemp = self._getBoundryWidth(self._boundries["setTemp"])
            h_setTemp = self._getBoundryHeight(self._boundries["setTemp"])
            
            # Width and Height of new Image
            w = w_processedImage + w_indicator + w_mode + 3 * w_setTemp + (5 * IMAGE_SPACING)
            h = h_processedImage

            new_im = Image.new('RGB', (w,h))

            # Paste processed Image
            new_im.paste(self._image["processed_image"], (0,0))

            # Paste indicators
            y_pos = IMAGE_SPACING
            y_pos_max_indicator = 0
            for i, indicator in enumerate(["indicatorOff", "indicatorHtg","indicatorDef","indicatorWarm"]):
                img_indicator_w = self._getBoundryWidth(self._boundries[indicator])
                img_indicator_h = self._getBoundryHeight(self._boundries[indicator])


                new_im.paste(self._image[indicator], (w_processedImage + IMAGE_SPACING, y_pos))

                d = ImageDraw.Draw(new_im)
                d.rectangle([(w_processedImage + IMAGE_SPACING, y_pos),(w_processedImage + IMAGE_SPACING + img_indicator_w ,y_pos + img_indicator_h)], outline=(0,255,0))

                y_pos = y_pos + img_indicator_h + IMAGE_SPACING
                y_pos_max_indicator = y_pos

            # Paste Modes
            y_pos = IMAGE_SPACING
            for i, mode in enumerate(["modeEcon","modeAuto","modeHeater"]):
                img_mode_w = self._getBoundryWidth(self._boundries[mode])
                img_mode_h = self._getBoundryHeight(self._boundries[mode])


                new_im.paste(self._image[mode], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING , y_pos))

                d = ImageDraw.Draw(new_im)
                d.rectangle([(w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING , y_pos),(w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + img_mode_w ,y_pos + img_mode_h)], outline=(0,255,0))

                y_pos = y_pos + img_mode_h + IMAGE_SPACING 



            # Paste Temps
            new_im.paste(self._image["setTemp_segments"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING, IMAGE_SPACING))
            new_im.paste(self._image["setTemp_thresh"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING + w_setTemp + IMAGE_SPACING, IMAGE_SPACING))
            new_im.paste(self._image["setTemp_morph"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING + 2 * w_setTemp + IMAGE_SPACING, IMAGE_SPACING))
            
            
            
            new_im.paste(self._image["waterTemp_segments"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING, h_setTemp + (2 *IMAGE_SPACING)))
            new_im.paste(self._image["waterTemp_thresh"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING + w_setTemp + IMAGE_SPACING, h_setTemp + (2 *IMAGE_SPACING)))
            new_im.paste(self._image["waterTemp_morph"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING + 2 * w_setTemp + IMAGE_SPACING, h_setTemp + (2 *IMAGE_SPACING)))


            # Paste Time
            h_time = self._getBoundryHeight(self._boundries["time"])
            new_im.paste(self._image["time_segments"], (w_processedImage + IMAGE_SPACING, y_pos_max_indicator))
            new_im.paste(self._image["time_thresh"], (w_processedImage + IMAGE_SPACING, y_pos_max_indicator + h_time + IMAGE_SPACING))
            new_im.paste(self._image["time_morph"], (w_processedImage + IMAGE_SPACING, y_pos_max_indicator + h_time + IMAGE_SPACING + h_time + IMAGE_SPACING))
     


            img_byte_arr = io.BytesIO()
            new_im.save(img_byte_arr, format='JPEG')
        
            return img_byte_arr.getvalue()

        return None



if __name__ == "__main__":

    oekoboiler = Oekoboiler()

    homeassistanturl = os.getenv("HASS_URL","http://homeassistant.local:8123")
    bearer_token = os.getenv("HASS_TOKEN", "")

    headers = {
        "Authorization": "Bearer {}".format(bearer_token),
    }

    camera_entity = os.getenv("CAMERA_ENTITY", "camera.my_camera")

    url = "{}/api/camera_proxy_stream/{}".format(homeassistanturl, camera_entity)
    r = requests.request("GET", url, headers=headers, stream=True)

    image = None

    if(r.status_code == 200):
        bytes=b''

        for chunk in r.iter_content(chunk_size=1024):
            bytes += chunk
            finda = bytes.find(b'\xff\xd8')
            findb = bytes.find(b'\xff\xd9')

            if finda != -1 and findb != -1:
                jpg = bytes[finda:findb+2]
                bytes = bytes[findb+2:]

                image = Image.open(io.BytesIO(jpg))
                
                if image is not None:
                    oekoboiler.processImage(image)

                    print("Time {}".format(oekoboiler.time))
                    print("Mode {}".format(oekoboiler.mode))
                    print("State {}".format(oekoboiler.state))
                    print("Water Temp {}".format(oekoboiler.waterTemperature))
                    print("Set Temp {}".format(oekoboiler.setTemperature))

                    processedImage = Image.open(io.BytesIO(oekoboiler.imageByteArray))

                    processedImage.show()


                    break