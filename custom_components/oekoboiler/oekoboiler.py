#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageOps, ImageFont

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

DEFAULT_BOUNDRY_TIME = (280, 245, 565, 365)

DEFAULT_BOUNDRY_SETTEMP = (630, 210, 710, 285)
DEFAULT_BOUNDRY_WATERTEMP = (630, 375, 710, 448)

DEFAULT_BOUNDRY_MODE_ECON = (15, 210, 170, 230)
DEFAULT_BOUNDRY_MODE_AUTO = (15, 280, 170, 310)
DEFAULT_BOUNDRY_MODE_HEATER = (15, 350, 170, 380)

DEFAULT_BOUNDRY_INDICATOR_OFF = (210, 275, 265, 300)
DEFAULT_BOUNDRY_INDICATOR_HTG = (210, 240, 265, 265)
DEFAULT_BOUNDRY_INDICATOR_DEF = (210, 310, 265, 335)
DEFAULT_BOUNDRY_INDICATOR_WARM = (210, 355, 265, 380)

DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP = (480, 170, 540, 200)

DEFAULT_THESHHOLD_ILLUMINATED = 66

IMAGE_SPACING = 10

TEMPTERATURE_UPPER_VALID = 100
TEMPTERATURE_LOWER_VALID = 0

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)

class Deformer:

    def getmesh(self, img):
        w, h = img.size

        return [(
                # target rectangle
                (0, 0, w, h),
                # corresponding source quadrilateral
                # TOP LEFT, BOTTOM LEFT, BOTTOM RIGHT, TOP RIGHT
                (0, 0, 0, h, w*1.0, h*1, w*0.98, 0)
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
            "highTemp": False
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
            "indicatorHighTemp": DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP,
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

        # Adapt for rounded display (at least a bit..)
        image = ImageOps.deform(original_image, Deformer())

        #Time
        img_time = self._cropToBoundry(image, self._boundries["time"], removeBlue=True)

        try:
            digits, value = self._findDigits(img_time, "time")
            if len(digits) == 4:
                self._time = "{}{}:{}{}".format(digits[0],digits[1],digits[2],digits[3])
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Set Temperature value: %s", exc_info=1)
            self._time  = None

        # Set Temperature 
        img_setTemp = self._cropToBoundry(image, self._boundries["setTemp"])

        try:
            digit, value = self._findDigits(img_setTemp, "setTemp", k=(1,8))
            _LOGGER.debug("Set Temperature read: {}".format(value))
            if value >= TEMPTERATURE_LOWER_VALID and value <= TEMPTERATURE_UPPER_VALID:
                self._setTemperature = value
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Set Temperature value: %s", exc_info=1)
            #self._setTemperature = None



        # Water Temperature
        img_waterTemp = self._cropToBoundry(image, self._boundries["waterTemp"])

        try:
            digits,value = self._findDigits(img_waterTemp, "waterTemp", k=(1,8))
            _LOGGER.debug("Water Temperature read: {}".format(value))
            if value >= TEMPTERATURE_LOWER_VALID and value <= TEMPTERATURE_UPPER_VALID:
                self._waterTemperature = value
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Water Temperature value: %s", exc_info=1)
            #self._waterTemperature = None



        # Modus
        img_modeAuto = self._cropToBoundry(image, self._boundries["modeAuto"])
        modeAuto = self._isIlluminated(img_modeAuto, "modeAuto")


        img_modeEcon = self._cropToBoundry(image, self._boundries["modeEcon"])
        modeEcon = self._isIlluminated(img_modeEcon, "modeEcon")


        img_modeHeater = self._cropToBoundry(image, self._boundries["modeHeater"])
        modeHeater = self._isIlluminated(img_modeHeater, "modeHeater")


        if modeAuto:
            self._mode = "Auto"
        
        if modeEcon:
            self._mode = "Econ"

        if modeHeater:
            self._mode = "Heater"

        _LOGGER.debug("Mode read: {}".format(self._mode))

        # Indicators
        img_warmIndicator = self._cropToBoundry(image, self._boundries["indicatorWarm"], removeBlue=True)
        self._indicator["warm"] = self._isIlluminated(img_warmIndicator, "indicatorWarm")


        img_defIndicator = self._cropToBoundry(image, self._boundries["indicatorDef"], removeBlue=True)
        self._indicator["def"] = self._isIlluminated(img_defIndicator, "indicatorDef")


        img_htgIndicator = self._cropToBoundry(image, self._boundries["indicatorHtg"], removeBlue=True)
        self._indicator["htg"] = self._isIlluminated(img_htgIndicator, "indicatorHtg")


        img_offIndicator = self._cropToBoundry(image, self._boundries["indicatorOff"], removeBlue=True)
        self._indicator["off"] = self._isIlluminated(img_offIndicator, "indicatorOff")

        if self._indicator["warm"]:
            self._state = "Warm"

        if self._indicator["def"]:
            self._state = "Defrosting"

        if self._indicator["htg"]:
            self._state = "Heating"

        if self._indicator["off"]:
            self._state = "Off"

        img_highTempIndicator = self._cropToBoundry(image, self._boundries["indicatorHighTemp"], removeBlue=True)
        self._indicator["highTemp"] = self._isIlluminated(img_highTempIndicator, "indicatorHighTemp")

        self.updatedProcessedImage(original_image)
     
    def updatedProcessedImage(self, original_image):

        _LOGGER.debug("Update processed Image due to new boundries {}".format(self._boundries))

        # Adapt for rounded display (at least a bit..)
        image = ImageOps.deform(original_image, Deformer())
        draw = ImageDraw.Draw(image)
        
        for key, value in self._boundries.items():
            draw.rectangle([(value[0],value[1]),(value[2],value[3])], outline="white", width=1)
            draw.text((value[0], value[1]), key)

        _LOGGER.debug("Saving processed Image")
        self._image["processed_image"] = image


    def _isIlluminated(self, image, title=""):


        h, w = image.size
        threshold = h*w*self._threshhold_illumination*0.4

        gray = image.convert('L')
        thresh = gray.point( lambda p: 255 if p > 70 else 0)
        nonZeroValue = sum(thresh.point( bool).getdata())

        _LOGGER.debug("{} NonZero {}, Threshhold {}".format(title, nonZeroValue, threshold))

        if title is not None:
            if nonZeroValue > threshold:
                h, w = image.size
                draw = ImageDraw.Draw(image)
                draw.rectangle([(0,0),(w,h)], outline="blue", width=1)

            self._image[title] = thresh

        return nonZeroValue > threshold


    def _findDigits(self, image, title="", segment_resize_factor=1, k=(1,7)):

        

        gray_image = image.convert('L')
        thresh_image = gray_image.point( lambda p: 255 if p > 80 else 0)
        w,h = thresh_image.size
        _LOGGER.debug("Image Size {} {}/{} ".format(title, w,h))

        # convert the threshhold image back to RGB so we can draw in color on in
        image = thresh_image.convert('RGB')
        draw = ImageDraw.Draw(image)
        

        # we know that there are 2 digits, left and right side of the image
        rois = [(0, 0, int(w/2), h), (int(w/2), 0, w, h)]

        digits = []

        # go trough all region of interest (digits)
        for roi in rois:
            #print ("Roi {} ".format(roi))
            draw.rectangle(roi, outline="yellow", width=1)

            # as migt not begin at the border of the roi
            # scan roi from the right to left until the digit really begins
            adapted_roi = roi
            for i in range(roi[2]-1, roi[0], -1):
                crop = (i-1,0, i,roi[3]-roi[1]-1)
                #print ("Scaning roi for right end {}".format(i))
                # Get one pixel line
                
                scan = thresh_image.crop(crop)
                total = sum(scan.point( bool).getdata())
                if total > 10:
                    adapted_roi = (roi[0],roi[1],i,roi[3])
                    break
            
            #scan from left to right
            # for i in range(roi[0], roi[2]-1):
            #     crop = (i,0, i+1,roi[3]-roi[1]-1)
            #     print ("Scaning roi for left end {}".format(i))
            #     # Get one pixel line
                
            #     scan = thresh_image.crop(crop)
            #     total = sum(scan.point( bool).getdata())
            #     if total > 10:
            #         adapted_roi = (i,roi[1],roi[2],roi[3])
            #         break
               
            #print ("Adapted Roi after scan {} ".format(roi))
            draw.rectangle(adapted_roi, outline="orange", width=1)
            # get only one part of the image
            im_seg = thresh_image.crop(adapted_roi)


            # compute the width and height of each of the 7 segments
            # we are going to examine

            (roiW, roiH) = im_seg.size

            # width and height of a segment
            (dW, dH) = (int(roiW  *0.25 * segment_resize_factor ), int(roiH *0.15 * segment_resize_factor))
            # height of vertical segment
            dHC = int(roiH * 0.18 * segment_resize_factor)
        

            # define the set of 7 segments
            segments = [
                ((0 + dW // 2, 0), (roiW - dW // 2, dH)),	# top
                ((0, 0 + dH // 2), (dW, roiH // 2 - dHC // 4)),	# top-left
                ((roiW - dW, 0 + dH // 2), (roiW, roiH // 2 - dHC // 4)),	# top-right
                ((0 + dW, (roiH // 2) - dHC // 2) , (roiW - dW, (roiH // 2) + dHC // 2)), # center
                #((0 + dW // 2, (roiH // 2) - dHC // 2) , (roiW - dW // 2, (roiH // 2) + dHC // 2)), # center
                ((0, roiH // 2 + dHC // 4), (dW, roiH - dH // 2)),	# bottom-left
                ((roiW - dW, roiH // 2 + dHC // 4), (roiW, roiH - dH // 2)),	# bottom-right
                ((0 + dW // 2, roiH - dH), (roiW - dW, roiH))	# bottom
                #((0 + dW // 2, roiH - dH), (roiW - dW // 2, roiH))	# bottom
            ]
            on = [0] * len(segments)

            # loop over the segments
            for (i, ((xA, yA), (xB, yB))) in enumerate(segments):

                # extract the segment ROI, count the total number of
                # thresholded pixels in the segment, and then compute
                # the area of the segment
                segROI = im_seg.crop((xA,yA, xB,yB))

                total = sum(segROI.point( bool).getdata())
                area = (xB - xA) * (yB - yA)
                # if the total number of non-zero pixels is greater than
                # 40% of the area, mark the segment as "on"
                _LOGGER.debug("Title {} Segment {} Area {} Total {}".format(title, i, area,total))
                
                draw.text((roi[0]+xA, roi[1]+yA), str(i))
                
                if area > 0 and total / float(area) > 0.4:
                    on[i]= 1
                    draw.rectangle([(roi[0]+xA,roi[1]+yA),(roi[0]+xB,roi[1]+yB)], outline="red", width=1)

                else:
                    draw.rectangle([(roi[0]+xA,roi[1]+yA),(roi[0]+xB,roi[1]+yB)], outline="blue", width=1)

            
            if title is not None:
                self._image["{}_segments".format(title)] = image

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

        return digits, value


    def _cropToBoundry(self, image, boundry, convertToGray=False, removeBlue=False):

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
            w = w_processedImage + w_indicator + w_mode + 1 * w_setTemp + (3 * IMAGE_SPACING)
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
            if "setTemp_segments" in self._image:
                new_im.paste(self._image["setTemp_segments"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING, IMAGE_SPACING))
            
            
            if "waterTemp_segments" in self._image:
                new_im.paste(self._image["waterTemp_segments"], (w_processedImage + IMAGE_SPACING + w_indicator + IMAGE_SPACING + w_mode + IMAGE_SPACING, h_setTemp + (2 *IMAGE_SPACING)))
            

            img_byte_arr = io.BytesIO()
            new_im.save(img_byte_arr, format='JPEG')
        
            return img_byte_arr.getvalue()

        return None



if __name__ == "__main__":


    _LOGGER.setLevel(logging.DEBUG)

    oekoboiler = Oekoboiler()

    homeassistanturl = os.getenv("HASS_URL","http://homeassistant.local:8123")
    bearer_token = os.getenv("HASS_TOKEN", "")

    headers = {
        "Authorization": "Bearer {}".format(bearer_token),
    }

    camera_entity = os.getenv("CAMERA_ENTITY", "camera.oekoboiler_camera")

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

                    #print("Time {}".format(oekoboiler.time))
                    print("Mode {}".format(oekoboiler.mode))
                    print("State {}".format(oekoboiler.state))
                    print("Water Temp {}".format(oekoboiler.waterTemperature))
                    print("Set Temp {}".format(oekoboiler.setTemperature))

                    print("High Temp {}".format(oekoboiler.indicator["highTemp"]))

                    processedImage = Image.open(io.BytesIO(oekoboiler.imageByteArray))

                    #processedImage.show()
                    processedImage.save("test.png")



                    break