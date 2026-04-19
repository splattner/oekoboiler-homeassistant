#!/usr/bin/env python3
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat

import logging
import io
import importlib.util
import os
from pathlib import Path
import sys
import time
import requests
from typing import Optional

try:
    from .models import AlignmentResult, ParsedFrame
except ImportError:  # pragma: no cover - allows direct script execution
    _MODELS_PATH = Path(__file__).with_name("models.py")
    _MODELS_SPEC = importlib.util.spec_from_file_location("oekoboiler_models", _MODELS_PATH)
    if _MODELS_SPEC is None or _MODELS_SPEC.loader is None:
        raise RuntimeError("Unable to load models module")
    _MODELS_MODULE = importlib.util.module_from_spec(_MODELS_SPEC)
    sys.modules[_MODELS_SPEC.name] = _MODELS_MODULE
    _MODELS_SPEC.loader.exec_module(_MODELS_MODULE)
    AlignmentResult = _MODELS_MODULE.AlignmentResult
    ParsedFrame = _MODELS_MODULE.ParsedFrame


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

DEFAULT_BOUNDRY_TIME = (285, 255, 569, 365)

DEFAULT_BOUNDRY_SETTEMP = (615, 223, 700, 295)
DEFAULT_BOUNDRY_WATERTEMP = (620, 383, 705, 455)

DEFAULT_BOUNDRY_MODE_ECON = (20, 220, 170, 240)
DEFAULT_BOUNDRY_MODE_AUTO = (20, 295, 170, 320)
DEFAULT_BOUNDRY_MODE_HEATER = (20, 380, 170, 410)

DEFAULT_BOUNDRY_INDICATOR_OFF = (210, 185, 270, 215)
DEFAULT_BOUNDRY_INDICATOR_HTG = (210, 235, 270, 265)
DEFAULT_BOUNDRY_INDICATOR_DEF = (210, 290, 270, 320)
DEFAULT_BOUNDRY_INDICATOR_WARM = (210, 345, 270, 375)

DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP = (480, 175, 540, 205)

DEFAULT_BOUNDRY_LEVEL = (770, 194, 795, 402)

DEFAULT_THESHHOLD_ILLUMINATED = 55
DEFAULT_THESHHOLD_GRAY = 85

IMAGE_SPACING = 10

TEMPTERATURE_UPPER_VALID = 100
TEMPTERATURE_LOWER_VALID = 0

ALIGNMENT_DOWNSAMPLED_SIZE = (160, 90)
ALIGNMENT_MAX_SHIFT = 8
ALIGNMENT_ERROR_THRESHOLD = 14.0
ALIGNMENT_DEADBAND_PX = 1
ALIGNMENT_MAX_STEP_PX = 12
ALIGNMENT_BORDER_RATIO = 0.20

LEVEL_BAR_COUNT = 9

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
                (0, 0, 0, h, w*0.99, h*1, w*1.01, 0)
                )]

class Oekoboiler:

    def __init__(self):

        self._boundaries = {
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
            "level": DEFAULT_BOUNDRY_LEVEL,
        }

        self._threshold_illumination = DEFAULT_THESHHOLD_ILLUMINATED / 100
        self._threshold_gray = DEFAULT_THESHHOLD_GRAY

        self._image = dict()
        self._frame = 0
        self._parsed_frame = ParsedFrame()
        self._working_frame = None
        self._previous_alignment_image = None
        self._raw_alignment_shift = (0, 0)
        self._alignment_shift = (0, 0)
        self._alignment_error = None
        self._active_boundaries = dict(self._boundaries)
        self._last_level_bars = None

    def _set_quality(self, key: str, status: str, confidence: Optional[float] = None):
        if self._working_frame is None:
            return

        self._working_frame.set_quality(key, status, self._frame, confidence)

    def _set_failed_quality(self, key: str, confidence: Optional[float] = None):
        if self._working_frame is None:
            return

        self._working_frame.set_failed_quality(key, self._frame, confidence)

    def _create_next_frame(self):
        next_frame = self._parsed_frame.clone()
        next_frame.alignment = AlignmentResult()
        return next_frame


    def setBoundries(self, boundaries):
        _LOGGER.debug("Set new boundries")
        self._boundaries = boundaries

        _LOGGER.debug("new Boundries {}".format(self._boundaries))

    def setThreshholdIllumination(self, threshold: int):
        _LOGGER.debug("Set new Illumination Threshold")
        self._threshold_illumination = threshold / 100

        _LOGGER.debug("new Illumination Threshold {}".format(self._threshold_illumination))

    def setThreshholdGray(self, threshold: int):
        _LOGGER.debug("Set new Gray Threshold")
        self._threshold_gray = int(threshold)

        _LOGGER.debug("new Gray Threshold {}".format(self._threshold_gray))

    def processImage(self, original_image):
        _LOGGER.debug("Processing image")
        _LOGGER.debug("Boundries {}".format(self._boundaries))
        self._frame += 1
        self._working_frame = self._create_next_frame()

        w, h = original_image.size

        # Adapt for rounded display (at least a bit..)
        image = ImageOps.deform(original_image, Deformer())
        #image = original_image

        self._raw_alignment_shift, self._alignment_error = self._estimate_frame_shift(image)
        self._alignment_shift = self._stabilize_alignment_shift(
            self._raw_alignment_shift,
            self._alignment_error,
        )
        self._working_frame.alignment = AlignmentResult(
            raw_shift_x=self._raw_alignment_shift[0],
            raw_shift_y=self._raw_alignment_shift[1],
            shift_x=self._alignment_shift[0],
            shift_y=self._alignment_shift[1],
            error=self._alignment_error,
            frame=self._frame,
        )
        self._active_boundaries = {
            key: self._shift_boundary_for_image(boundary, image.size, self._alignment_shift)
            for key, boundary in self._boundaries.items()
        }

        #Time
        img_time = self._crop_to_boundary(image, self._active_boundaries["time"], removeBlue=True)
        try:
            digits, value, confidence = self._findDigits(img_time, "time", numDigits=4, withSeperator=True)
            if len(digits) == 4 and all(digit is not None for digit in digits):
                self._working_frame.time = "{}{}:{}{}".format(digits[0],digits[1],digits[2],digits[3])
                self._set_quality("time", "ok", confidence)
            else:
                self._working_frame.time = None
                self._set_failed_quality("time", confidence)
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Set Temperature value: %s", exc_info=1)
            self._working_frame.time = None
            self._set_failed_quality("time")

        # Set Temperature 
        img_setTemp = self._crop_to_boundary(image, self._active_boundaries["setTemp"])
        try:
            digits, value, confidence = self._findDigits(img_setTemp, "setTemp", numDigits=2)
            _LOGGER.debug("Set Temperature read: {}".format(value))
            if value is not None and value >= TEMPTERATURE_LOWER_VALID and value <= TEMPTERATURE_UPPER_VALID:
                self._working_frame.set_temperature = value
                self._set_quality("set_temperature", "ok", confidence)
            else:
                self._set_failed_quality("set_temperature", confidence)
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Set Temperature value: %s", exc_info=1)
            self._set_failed_quality("set_temperature")



        # Water Temperature
        img_waterTemp = self._crop_to_boundary(image, self._active_boundaries["waterTemp"])
        try:
            digits, value, confidence = self._findDigits(img_waterTemp, "waterTemp", numDigits=2)
            _LOGGER.debug("Water Temperature read: {}".format(value))
            if value is not None and value >= TEMPTERATURE_LOWER_VALID and value <= TEMPTERATURE_UPPER_VALID:
                self._working_frame.water_temperature = value
                self._set_quality("water_temperature", "ok", confidence)
            else:
                self._set_failed_quality("water_temperature", confidence)
        except Exception as error:
            _LOGGER.debug("Could not find digits for the Water Temperature value: %s", exc_info=1)
            self._set_failed_quality("water_temperature")



        # Modus
        img_modeAuto = self._crop_to_boundary(image, self._active_boundaries["modeAuto"])
        modeAuto, modeAutoConf = self._isIlluminated(img_modeAuto, "modeAuto", with_confidence=True)


        img_modeEcon = self._crop_to_boundary(image, self._active_boundaries["modeEcon"])
        modeEcon, modeEconConf = self._isIlluminated(img_modeEcon, "modeEcon", with_confidence=True)


        img_modeHeater = self._crop_to_boundary(image, self._active_boundaries["modeHeater"])
        modeHeater, modeHeaterConf = self._isIlluminated(img_modeHeater, "modeHeater", with_confidence=True)

        mode_candidates = [
            ("Auto", modeAuto, modeAutoConf),
            ("Econ", modeEcon, modeEconConf),
            ("Heater", modeHeater, modeHeaterConf),
        ]
        active_modes = [candidate for candidate in mode_candidates if candidate[1]]
        if len(active_modes) == 1:
            self._working_frame.mode = active_modes[0][0]
            self._set_quality("mode", "ok", active_modes[0][2])
        else:
            best_confidence = max((candidate[2] for candidate in mode_candidates), default=0.0)
            self._set_failed_quality("mode", best_confidence)

        _LOGGER.debug("Mode read: {}".format(self._working_frame.mode))

        # Indicators
        img_warmIndicator = self._crop_to_boundary(image, self._active_boundaries["indicatorWarm"], removeBlue=True)
        self._working_frame.indicator["warm"], warmConf = self._isIlluminated(
            img_warmIndicator,
            "indicatorWarm",
            with_confidence=True,
        )


        img_defIndicator = self._crop_to_boundary(image, self._active_boundaries["indicatorDef"], removeBlue=True)
        self._working_frame.indicator["def"], defConf = self._isIlluminated(
            img_defIndicator,
            "indicatorDef",
            with_confidence=True,
        )


        img_htgIndicator = self._crop_to_boundary(image, self._active_boundaries["indicatorHtg"], removeBlue=True)
        self._working_frame.indicator["htg"], htgConf = self._isIlluminated(
            img_htgIndicator,
            "indicatorHtg",
            with_confidence=True,
        )


        img_offIndicator = self._crop_to_boundary(image, self._active_boundaries["indicatorOff"], removeBlue=True)
        self._working_frame.indicator["off"], offConf = self._isIlluminated(
            img_offIndicator,
            "indicatorOff",
            with_confidence=True,
        )

        state_candidates = [
            ("Warm", self._working_frame.indicator["warm"], warmConf),
            ("Defrosting", self._working_frame.indicator["def"], defConf),
            ("Heating", self._working_frame.indicator["htg"], htgConf),
            ("Off", self._working_frame.indicator["off"], offConf),
        ]
        active_states = [candidate for candidate in state_candidates if candidate[1]]
        if len(active_states) == 1:
            self._working_frame.state = active_states[0][0]
            self._set_quality("state", "ok", active_states[0][2])
        else:
            best_confidence = max((candidate[2] for candidate in state_candidates), default=0.0)
            self._set_failed_quality("state", best_confidence)

        # High Temp Indicator
        img_highTempIndicator = self._crop_to_boundary(image, self._active_boundaries["indicatorHighTemp"], removeBlue=True)
        self._working_frame.indicator["highTemp"] = self._isIlluminated(img_highTempIndicator, "indicatorHighTemp")

        img_level = self._crop_to_boundary(image, self._active_boundaries["level"])
        try:
            self._working_frame.level, level_confidence = self._getLevel(img_level)
            self._set_quality("level", "ok", level_confidence)
        except Exception:
            self._set_failed_quality("level")


        self.updatedProcessedImage(original_image)
        self._parsed_frame = self._working_frame
        self._working_frame = None
     
    def updatedProcessedImage(self, original_image):

        _LOGGER.debug("Update processed Image due to new boundries {}".format(self._boundaries))

        # Adapt for rounded display (at least a bit..)
        image = ImageOps.deform(original_image, Deformer())
        #image = original_image
        draw = ImageDraw.Draw(image)
        
        active_boundries = self._active_boundaries if self._active_boundaries else self._boundaries
        for key, value in active_boundries.items():
            draw.rectangle([(value[0],value[1]),(value[2],value[3])], outline="white", width=1)
            draw.text((value[0], value[1]), key)

        _LOGGER.debug("Saving processed Image")
        self._image["processed_image"] = image

    def _getLevel(self, image):
        """Estimate level from 9 vertical bars and return percentage + confidence."""

        w, h = image.size
        gray = image.convert("L")
        thresh = gray.point(lambda p: 255 if p > 90 else 0)
        self._image["level"] = thresh

        if w <= 0 or h <= 0:
            return 0.0, 0.0

        slot_height = h / float(LEVEL_BAR_COUNT)
        lit_flags = []
        slot_scores = []

        for slot_index in range(LEVEL_BAR_COUNT):
            # bottom -> top mapping
            y_top = int(h - ((slot_index + 1) * slot_height))
            y_bottom = int(h - (slot_index * slot_height))

            if y_bottom <= y_top:
                lit_flags.append(False)
                slot_scores.append(0.0)
                continue

            # Ignore border pixels to avoid frame noise.
            x0 = 1 if w > 2 else 0
            x1 = w - 1 if w > 2 else w

            # Ignore top and bottom fraction of each slot to reduce separator bleed.
            trim = max(0, int((y_bottom - y_top) * 0.15))
            y0 = y_top + trim
            y1 = y_bottom - trim
            if y1 <= y0:
                y0, y1 = y_top, y_bottom

            slot_roi = thresh.crop((x0, y0, x1, y1))
            area = max(1, (x1 - x0) * (y1 - y0))
            lit = slot_roi.histogram()[255]
            fill_ratio = lit / float(area)

            slot_scores.append(fill_ratio)
            lit_flags.append(fill_ratio >= 0.38)

        # Real bar displays fill from bottom continuously; ignore isolated lit noise above gaps.
        bars_lit = 0
        for lit in lit_flags:
            if lit:
                bars_lit += 1
            else:
                break

        bars_lit = self._apply_level_state_rules(bars_lit)

        # Confidence increases when lit bars are clearly lit and unlit bars remain dark.
        lit_scores = slot_scores[:bars_lit]
        unlit_scores = slot_scores[bars_lit:]
        lit_conf = sum(lit_scores) / len(lit_scores) if lit_scores else 0.0
        dark_conf = (sum((1.0 - s) for s in unlit_scores) / len(unlit_scores)) if unlit_scores else 1.0
        confidence = max(0.0, min(1.0, (lit_conf + dark_conf) / 2.0))

        level_percent = (bars_lit / float(LEVEL_BAR_COUNT)) * 100.0

        _LOGGER.debug(
            "Level bars=%s/%s confidence=%.2f scores=%s",
            bars_lit,
            LEVEL_BAR_COUNT,
            confidence,
            [round(score, 2) for score in slot_scores],
        )

        return level_percent, confidence

    def _apply_level_state_rules(self, bars_lit):
        """Apply state-aware smoothing constraints to level bar count."""
        bars_lit = max(0, min(LEVEL_BAR_COUNT, int(bars_lit)))
        previous = self._last_level_bars
        current_state = self._working_frame.state if self._working_frame is not None else self._parsed_frame.state

        if previous is None:
            self._last_level_bars = bars_lit
            return bars_lit

        if current_state == "Heating" and bars_lit < previous:
            # During heating, level should generally rise, so suppress regressions.
            bars_lit = previous
        elif current_state == "Warm" and abs(bars_lit - previous) > 1:
            # During warm, expect stability; ignore abrupt jumps as likely noise.
            bars_lit = previous

        self._last_level_bars = bars_lit
        return bars_lit

    def _build_alignment_anchor_image(self, image):
        """Build a reduced grayscale image emphasizing stable border regions."""
        anchor_image = image.convert("L").resize(
            ALIGNMENT_DOWNSAMPLED_SIZE,
            Image.Resampling.BILINEAR,
        )

        w, h = anchor_image.size
        margin_x = int(w * ALIGNMENT_BORDER_RATIO)
        margin_y = int(h * ALIGNMENT_BORDER_RATIO)

        # Ignore central dynamic display areas and keep border structure.
        draw = ImageDraw.Draw(anchor_image)
        draw.rectangle(
            (margin_x, margin_y, w - margin_x, h - margin_y),
            fill=0,
        )

        return anchor_image

    def _estimate_frame_shift(self, image, max_shift=ALIGNMENT_MAX_SHIFT):
        """Estimate frame-to-frame translation in pixels."""
        downsampled = self._build_alignment_anchor_image(image)

        if self._previous_alignment_image is None:
            self._previous_alignment_image = downsampled
            return (0, 0), None

        previous = self._previous_alignment_image
        width, height = downsampled.size

        best_dx = 0
        best_dy = 0
        best_error = float("inf")

        for dy in range(-max_shift, max_shift + 1):
            for dx in range(-max_shift, max_shift + 1):
                shifted = ImageChops.offset(downsampled, dx, dy)

                # Remove wrapped pixels introduced by offset.
                if dx > 0:
                    shifted.paste(0, (0, 0, dx, height))
                elif dx < 0:
                    shifted.paste(0, (width + dx, 0, width, height))
                if dy > 0:
                    shifted.paste(0, (0, 0, width, dy))
                elif dy < 0:
                    shifted.paste(0, (0, height + dy, width, height))

                error = ImageStat.Stat(ImageChops.difference(previous, shifted)).mean[0]
                if error < best_error:
                    best_error = error
                    best_dx = dx
                    best_dy = dy

        self._previous_alignment_image = downsampled

        scale_x = image.size[0] / float(width)
        scale_y = image.size[1] / float(height)
        # best_dx/best_dy align the current frame back to the previous one;
        # invert sign to get the observed frame motion to apply to boundaries.
        full_dx = int(round(-best_dx * scale_x))
        full_dy = int(round(-best_dy * scale_y))

        return (full_dx, full_dy), best_error

    def _stabilize_alignment_shift(self, shift, error):
        """Gate and smooth raw alignment shifts before applying them to ROIs."""
        shift_x, shift_y = shift

        if error is not None and error > ALIGNMENT_ERROR_THRESHOLD:
            return (0, 0)

        if abs(shift_x) <= ALIGNMENT_DEADBAND_PX:
            shift_x = 0
        if abs(shift_y) <= ALIGNMENT_DEADBAND_PX:
            shift_y = 0

        previous_x, previous_y = self._alignment_shift
        if abs(shift_x - previous_x) > ALIGNMENT_MAX_STEP_PX:
            shift_x = previous_x
        if abs(shift_y - previous_y) > ALIGNMENT_MAX_STEP_PX:
            shift_y = previous_y

        return (int(shift_x), int(shift_y))

    def _shift_boundary_for_image(self, boundary, image_size, shift):
        """Shift a boundary and clamp it to image limits while preserving size."""
        image_w, image_h = image_size
        x1, y1, x2, y2 = boundary
        dx, dy = shift

        bw = max(1, x2 - x1)
        bh = max(1, y2 - y1)

        shifted_x1 = x1 + dx
        shifted_y1 = y1 + dy

        max_x1 = max(0, image_w - bw)
        max_y1 = max(0, image_h - bh)

        shifted_x1 = max(0, min(shifted_x1, max_x1))
        shifted_y1 = max(0, min(shifted_y1, max_y1))

        return (
            int(shifted_x1),
            int(shifted_y1),
            int(shifted_x1 + bw),
            int(shifted_y1 + bh),
        )


    def _isIlluminated(self, image, title="", with_confidence=False):


        w,h = image.size
        threshold = h*w*self._threshold_illumination*0.4

        gray = image.convert('L')
        thresh = gray.point( lambda p: 255 if p > 50 else 0)
        nonZeroValue = thresh.histogram()[255]

        _LOGGER.debug("{} NonZero {}, Threshhold {}".format(title, nonZeroValue, threshold))

        confidence = 0.0
        if threshold > 0:
            confidence = min(1.0, nonZeroValue / threshold)

        if title is not None:
            if nonZeroValue > threshold:
                h, w = image.size
                draw = ImageDraw.Draw(image)
                draw.rectangle([(0,0),(w,h)], outline="blue", width=1)

            self._image[title] = thresh

        illuminated = nonZeroValue > threshold
        if with_confidence:
            return illuminated, confidence
        return illuminated

    @staticmethod
    def _decode_segments(on_segments) -> tuple[Optional[int], float]:
        """Decode a 7-segment activation tuple.

        Returns a digit when there is an exact match or a unique, close match.
        Returns None when the pattern is ambiguous.
        """
        pattern = tuple(on_segments)
        digit = DIGITS_LOOKUP.get(pattern)
        if digit is not None:
            return digit, 1.0

        ranked_candidates = []
        for candidate_pattern, candidate_digit in DIGITS_LOOKUP.items():
            distance = sum(
                int(current != reference)
                for current, reference in zip(pattern, candidate_pattern)
            )
            ranked_candidates.append((distance, candidate_digit))

        ranked_candidates.sort(key=lambda item: item[0])
        best_distance, best_digit = ranked_candidates[0]
        second_best_distance = ranked_candidates[1][0] if len(ranked_candidates) > 1 else 7

        confidence = max(0.0, 1 - (best_distance / 7))

        # Accept a fuzzy match only when it is both close and unambiguous.
        if best_distance <= 1 and best_distance < second_best_distance:
            return best_digit, confidence

        return None, confidence


    def _findDigits(self, image, title="", segment_resize_factor=1, numDigits = 2, withSeperator=False):

        gray_image = image.convert('L')
        thresh_image = gray_image.point( lambda p: 255 if p > self._threshold_gray else 0)
        w,h = thresh_image.size
        _LOGGER.debug("Image Size {} {}/{} ".format(title, w,h))

        # convert the threshhold image back to RGB so we can draw in color on in
        image = thresh_image.convert('RGB')
        draw = ImageDraw.Draw(image)

        if withSeperator:
            seperatorSize = w // numDigits // 4
        else:
            seperatorSize = 0

        rois = self._find_digit_rois_from_components(
            thresh_image,
            numDigits=numDigits,
            withSeperator=withSeperator,
        )

        if rois is None:
            # Fallback to the legacy equal-split approach when component detection
            # cannot reliably identify all digits.
            rois = []
            for i in range(0, numDigits):
                seperator = 0
                # Shift for the seperator, assuming its in the middle
                if i >= numDigits/2 and withSeperator:
                    seperator = seperatorSize

                roi = (
                        (i * int((w-seperatorSize)/numDigits)) + seperator,
                        0,
                        ((i+1) * int((w-seperatorSize)/numDigits)) + seperator,
                        h)

                rois.append(roi)

        #rois = [(0, 0, int(w/2), h), (int(w/2), 0, w, h)]

        # draw seperator
        if withSeperator:
            draw.rectangle((int(w/numDigits)*numDigits/2 - seperatorSize//2 ,0,(int(w/numDigits)*numDigits/2 + seperatorSize//2,h)), fill="grey", outline="grey", width=1)

        #_LOGGER.debug("Rois: {}".format(rois))

        digits = []
        confidence_scores = []

        # go trough all region of interest (digits)
        for roi in rois:
            #print ("Roi {} ".format(roi))
            draw.rectangle(roi, outline="yellow", width=2)

            # as might not begin at the border of the roi
            # scan roi from the right to left until the digit really begins
            adapted_roi = roi
            for i in range(roi[2]-1, roi[0], -1):
                crop = (i-1,0, i,roi[3]-roi[1]-1)
                # Get one pixel line
                
                scan = thresh_image.crop(crop)
                total = scan.histogram()[255]
                if total > 2:
                    adapted_roi = (adapted_roi[0],adapted_roi[1],i,adapted_roi[3])
                    break

            
            #scan from left to right
            for i in range(roi[0], roi[0]+((roi[2]- roi[0]) // 2)):
                crop = (i,0, i+1,roi[3]-roi[1]-1)
                # Get one pixel line
                
                scan = thresh_image.crop(crop)
                total = scan.histogram()[255]
                if total > 2:
                    adapted_roi = (i,adapted_roi[1],adapted_roi[2],adapted_roi[3])
                    break
               
            draw.rectangle(adapted_roi, outline="green", width=1)

            roi = adapted_roi
            # get only one part of the image
            im_seg = thresh_image.crop(roi)


            # compute the width and height of each of the 7 segments
            # we are going to examine

            (roiW, roiH) = im_seg.size

            # width and height of a segment
            (dW, dH) = (int(roiW  *0.25 * segment_resize_factor ), int(roiH *0.15 * segment_resize_factor))
            # height of vertical segment
            dHC = int(roiH * 0.13 * segment_resize_factor)
        

            # define the set of 7 segments
            segments = [
                ((0 + dW // 2, 0), (roiW - dW // 2, dH)),	# top
                ((0, 0 + dH ), (dW, roiH // 2 - dHC // 2)),	# top-left
                ((roiW - dW, 0 + dH), (roiW, roiH // 2 - dHC // 2)),	# top-right
                ((0 + dW, (roiH // 2) - dHC // 2) , (roiW - dW, (roiH // 2) + dHC // 2)), # center
                #((0 + dW // 2, (roiH // 2) - dHC // 2) , (roiW - dW // 2, (roiH // 2) + dHC // 2)), # center
                ((0, roiH // 2 + dHC // 2), (dW, roiH - dH )),	# bottom-left
                ((roiW - dW, roiH // 2 + dHC // 2), (roiW, roiH - dH )),	# bottom-right
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

                total = segROI.histogram()[255]
                area = (xB - xA) * (yB - yA)
                # if the total number of non-zero pixels is greater than
                # 40% of the area, mark the segment as "on"
                _LOGGER.debug("Title {} Segment {} Area {} Total {}".format(title, i, area,total))
                
                draw.text((roi[0]+xA, roi[1]+yA), str(i))

                theshhold = 0.3
                # lower theshhold a bit for top line
                #if i == 0:
                #    theshhold = 0.35
                
                if area > 0 and total / float(area) > theshhold:
                    on[i]= 1
                    draw.rectangle([(roi[0]+xA,roi[1]+yA),(roi[0]+xB,roi[1]+yB)], outline="red", width=1)
                else:
                    draw.rectangle([(roi[0]+xA,roi[1]+yA),(roi[0]+xB,roi[1]+yB)], outline="blue", width=1)

                #draw.text((roi[0]+xA, roi[1]+yA + 10), str(total / float(area)), fill="orange")

            
            if title is not None:
                self._image["{}_segments".format(title)] = image

            # lookup the digit and draw it on the image
            digit, confidence = self._decode_segments(on)
            confidence_scores.append(confidence)

            if digit is None:
                _LOGGER.debug(
                    "Title %s unknown digit for segments %s (confidence %.2f)",
                    title,
                    tuple(on),
                    confidence,
                )
            digits.append(digit)

        ## Return all contures and digits found + calcucate value with the digits
        if any(digit is None for digit in digits):
            value = None
        else:
            value = 0
            num_digits = len(digits)
            for i in range(num_digits):
                value = value + digits[i] * (10**(num_digits-1-i))

        if confidence_scores:
            _LOGGER.debug(
                "Title %s average digit confidence %.2f",
                title,
                sum(confidence_scores) / len(confidence_scores),
            )

        avg_confidence = 0.0
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)

        return digits, value, avg_confidence

    def _find_digit_rois_from_components(self, thresh_image, numDigits=2, withSeperator=False):
        """Find digit ROIs from a binarized image using connected regions.

        The method uses a light dilation to connect segments of the same digit,
        then derives contiguous x-runs that likely correspond to each digit.
        Returns None if a reliable set of digit boxes cannot be found.
        """
        w, h = thresh_image.size
        if w <= 0 or h <= 0 or numDigits <= 0:
            return None

        # Dilation helps connect seven-segment strokes into broader digit blobs.
        work_image = thresh_image.filter(ImageFilter.MaxFilter(size=5))
        pixels = work_image.load()

        separator_start = -1
        separator_end = -1
        if withSeperator:
            separator_half_width = max(1, w // (numDigits * 6))
            center = w // 2
            separator_start = max(0, center - separator_half_width)
            separator_end = min(w - 1, center + separator_half_width)

        min_column_pixels = max(1, h // 8)
        min_run_width = max(2, w // (numDigits * 7))

        runs = []
        run_start = None

        for x in range(w):
            if separator_start <= x <= separator_end:
                column_active = False
            else:
                lit_pixels = 0
                for y in range(h):
                    if pixels[x, y] > 0:
                        lit_pixels += 1
                column_active = lit_pixels >= min_column_pixels

            if column_active and run_start is None:
                run_start = x
            elif not column_active and run_start is not None:
                run_end = x - 1
                if (run_end - run_start + 1) >= min_run_width:
                    runs.append((run_start, run_end))
                run_start = None

        if run_start is not None:
            run_end = w - 1
            if (run_end - run_start + 1) >= min_run_width:
                runs.append((run_start, run_end))

        if len(runs) != numDigits:
            return None

        rois = []
        for run_start, run_end in runs:
            left = max(0, run_start - 1)
            right = min(w, run_end + 2)
            if right - left < 2:
                return None
            rois.append((left, 0, right, h))

        return rois


    def _crop_to_boundary(self, image, boundary, convertToGray=False, removeBlue=False):

        if removeBlue:
            matrix = (
                        1, 0, 0, 0,
                        0, 1, 0, 0,
                        0, 0, 0, 0
                    )
            image = image.convert("RGB", matrix)

        if convertToGray:
            image = image.convert('L')
        
        output = image.crop(boundary)

        return output

    def _get_boundary_width(self, boundary):
        return boundary[2] - boundary[0]

    def _get_boundary_height(self, boundary):
        return boundary[3] - boundary[1]

    @property
    def time(self):
        return self._parsed_frame.time

    @property
    def setTemperature(self):
        return self._parsed_frame.set_temperature

    @property
    def waterTemperature(self):
        return self._parsed_frame.water_temperature

    @property
    def mode(self):
        return self._parsed_frame.mode

    @property
    def state(self):
        return self._parsed_frame.state

    @property
    def indicator(self):
        return self._parsed_frame.indicator

    @property
    def level(self):
        return self._parsed_frame.level

    def get_quality(self, key: str):
        return self._parsed_frame.get_quality_dict(key)

    def get_alignment(self):
        return self._parsed_frame.get_alignment_dict()

    @property
    def parsed_frame(self):
        return self._parsed_frame

    @property
    def image(self):
        _LOGGER.debug("Request Processes Image")

        return self._image.get("processed_image")

    @property
    def imageByteArray(self):
        _LOGGER.debug("Request Processes Image as ByteArray")

        if "processed_image" in self._image and self._image["processed_image"] is not None:
            # Paste processed Image
            w_processedImage, h_processedImage = self._image["processed_image"].size
            new_im = Image.new('RGB', (w_processedImage,h_processedImage))
            new_im.paste(self._image["processed_image"], (0,0))

            # Paste indicators
            for i, indicator in enumerate(["indicatorOff", "indicatorHtg","indicatorDef","indicatorWarm"]):
                boundry = self._active_boundaries.get(indicator, self._boundaries[indicator])
                indicator_image = self._image.get(indicator)
                if indicator_image is not None:
                    new_im.paste(indicator_image, (boundry[0], boundry[1]))

            # Paste Modes
            for i, mode in enumerate(["modeEcon","modeAuto","modeHeater"]):
                boundry = self._active_boundaries.get(mode, self._boundaries[mode])
                mode_image = self._image.get(mode)
                if mode_image is not None:
                    new_im.paste(mode_image, (boundry[0], boundry[1]))


            # Paste Temps
            if "setTemp_segments" in self._image:
                boundry = self._active_boundaries.get("setTemp", self._boundaries["setTemp"])
                new_im.paste(self._image["setTemp_segments"], (boundry[0], boundry[1]))
            if "waterTemp_segments" in self._image:
                boundry = self._active_boundaries.get("waterTemp", self._boundaries["waterTemp"])
                new_im.paste(self._image["waterTemp_segments"], (boundry[0], boundry[1]))

            # Paste time
            if "time_segments" in self._image:
                boundry = self._active_boundaries.get("time", self._boundaries["time"])
                new_im.paste(self._image["time_segments"], (boundry[0], boundry[1]))

            # Paste time
            if "level" in self._image:
                boundry = self._active_boundaries.get("level", self._boundaries["level"])
                new_im.paste(self._image["level"], (boundry[0], boundry[1]))

            

            # ## Grid
            # for x in range(10,w_processedImage,10):
            #     draw = ImageDraw.Draw(new_im)
            #     draw.line((x,0,x,h_processedImage), width=1, fill="#222222")
            # for y in range(10,h_processedImage,10):
            #     draw = ImageDraw.Draw(new_im)
            #     draw.line((0,y,w_processedImage,y), width=1, fill="#222222")

            

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

    scan_interval = int(os.getenv("LOCAL_TEST_INTERVAL", "30"))
    max_iterations = int(os.getenv("LOCAL_TEST_MAX_ITERATIONS", "0"))
    request_timeout = int(os.getenv("LOCAL_TEST_TIMEOUT", "10"))
    url = "{}/api/camera_proxy/{}".format(homeassistanturl, camera_entity)

    print(
        "Local test loop started: interval={}s, max_iterations={} (0 means forever), entity={}".format(
            scan_interval,
            max_iterations,
            camera_entity,
        )
    )

    iteration = 0
    while True:
        if max_iterations > 0 and iteration >= max_iterations:
            break

        iteration += 1
        print("\n=== Iteration {} ===".format(iteration))

        try:
            response = requests.get(url, headers=headers, timeout=request_timeout)
        except requests.RequestException as err:
            print("Failed to fetch camera image: {}".format(err))
            time.sleep(scan_interval)
            continue

        if response.status_code != 200:
            print("Camera request failed: status={}".format(response.status_code))
            time.sleep(scan_interval)
            continue

        try:
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
        except Exception as err:
            print("Failed to decode image: {}".format(err))
            time.sleep(scan_interval)
            continue

        oekoboiler.processImage(image)

        print("Time {}".format(oekoboiler.time))
        print("Mode {}".format(oekoboiler.mode))
        print("State {}".format(oekoboiler.state))
        print("Water Temp {}".format(oekoboiler.waterTemperature))
        print("Set Temp {}".format(oekoboiler.setTemperature))
        print("High Temp {}".format(oekoboiler.indicator["highTemp"]))
        print("Level {}".format(oekoboiler.level))

        print("Quality:")
        for quality_key in [
            "time",
            "set_temperature",
            "water_temperature",
            "mode",
            "state",
            "level",
        ]:
            quality = oekoboiler.get_quality(quality_key)
            print(
                "  {} -> status={}, confidence={}, frame={}".format(
                    quality_key,
                    quality.get("status"),
                    quality.get("confidence"),
                    quality.get("frame"),
                )
            )

        alignment = oekoboiler.get_alignment()
        print(
            "Alignment -> raw_shift_x={}, raw_shift_y={}, shift_x={}, shift_y={}, error={}, frame={}".format(
                alignment.get("raw_shift_x"),
                alignment.get("raw_shift_y"),
                alignment.get("shift_x"),
                alignment.get("shift_y"),
                alignment.get("error"),
                alignment.get("frame"),
            )
        )

        processed_image_bytes = oekoboiler.imageByteArray
        if processed_image_bytes is not None:
            processed_image = Image.open(io.BytesIO(processed_image_bytes))
            processed_image.save("test.png")

        time.sleep(scan_interval)