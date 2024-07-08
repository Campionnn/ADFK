import pytesseract
import cv2
import numpy as np
import difflib
import re

import coords
import config

if config.port == 0000:
    import config_personal as config

pytesseract.pytesseract.tesseract_cmd = config.tesseract_path


def find_text(image_input: np.ndarray, text):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    result = pytesseract.image_to_data(thresh, config=f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, text, line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
    return None


def find_fast_travel(image_input: np.ndarray, location, tolerance=50, ratio=3):
    image = image_input.copy()
    crop = image[:image.shape[0] // ratio, :image.shape[1] // ratio]
    color = (255, 255, 255)
    lower = np.array([color[0] - tolerance, color[1] - tolerance, color[2] - tolerance])
    upper = np.array([color[0], color[1], color[2]])
    mask = cv2.inRange(crop, lower, upper)
    crop[mask == 255] = [255, 255, 255]
    crop[mask != 255] = [0, 0, 0]
    result = pytesseract.image_to_data(crop, config=f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ').lower()
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, location, line[11].lower()).ratio() > 0.6:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
    cv2.imwrite("crop.png", crop)
    return None


def read_upgrade_cost(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    x, y, w, h = 0, 0, 0, 0
    for contour in contours:
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        area = cv2.contourArea(contour)
        if len(approx) == 3 and area > max_area:
            x, y, w, h = cv2.boundingRect(contour)
            max_area = area
    if max_area == 0:
        return None
    try:
        crop = thresh[y - h:y + h * 2, x + round(w * 1.5):x + w * 9]
        text = str(pytesseract.image_to_string(crop, config=f'--psm 8 -c tessedit_char_whitelist=0123456789')).strip()
        if text == "":
            return None
        return [int(text), x + w // 2, y + h // 2]
    except SystemError:
        return None


def read_current_money(image_input: np.ndarray):
    image = image_input.copy()
    lower = np.array(
        [coords.money_color[0] - coords.money_tolerance,
         coords.money_color[1] - coords.money_tolerance,
         coords.money_color[2] - coords.money_tolerance])
    upper = np.array(
        [coords.money_color[0] + coords.money_tolerance,
         coords.money_color[1] + coords.money_tolerance,
         coords.money_color[2] + coords.money_tolerance])
    mask = cv2.inRange(image, lower, upper)
    image[mask != 255] = [0, 0, 0]
    image[mask == 255] = [255, 255, 255]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dilate = cv2.dilate(gray, np.ones((3, 3), np.uint8), iterations=5)
    contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    x, y, w, h = 0, 0, 0, 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            x, y, w, h = cv2.boundingRect(contour)
            max_area = area
    if max_area == 0:
        return None
    try:
        crop = gray[y:y + h, x:x + w]
        text = str(
            pytesseract.image_to_string(crop, config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789')).strip()
        if text == "":
            return None
        return int(text)
    except SystemError:
        return None


def read_current_wave(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    result = pytesseract.image_to_string(thresh, config=f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    result = result.split('\n')
    for line in result:
        line = line.lower()
        if line.startswith("wave"):
            try:
                number = int(re.search(r'wave(\d+)', line).group(1))
                if "completed" in line:
                    return number + 1
                elif "started" in line:
                    return number
            except AttributeError:
                return None
    return None