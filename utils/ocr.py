import pytesseract
import cv2
import numpy as np
import difflib
import re

import coords
try:
    import config_personal as config
except ImportError:
    import config

pytesseract.pytesseract.tesseract_cmd = config.tesseract_path


def find_text(image_input: np.ndarray, text, numbers=False, black_text=False):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if black_text:
        _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)
    else:
        _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if numbers:
        tesseract_config += '0123456789'
    result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if text == "units":
            if len(line) == 12:
                keywords = ["units", "items", "quests", "guilds"]
                for keyword in keywords:
                    if difflib.SequenceMatcher(None, keyword, line[11].lower()).ratio() > 0.8:
                        x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
                        return x + w // 2, y + h // 2
        if len(line) == 12 and difflib.SequenceMatcher(None, text, line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            if text == "openportal":
                return x, y+h*2
            return x+w//2, y+h//2
        elif text == "playagain" or text == "backtolobby":
            if len(line) == 12 and difflib.SequenceMatcher(None, "playagainbacktolobby", line[11].lower()).ratio() > 0.8:
                x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
                if text == "playagain":
                    return (x+w//4), y+h//2
                else:
                    return x+(w//4*3), y+h//2
    return None


def find_fast_travel(image_input: np.ndarray, location, tolerance=50, ratio=3, use_mask=False):
    image = image_input.copy()
    crop = image[:image.shape[0] // ratio, :image.shape[1] // ratio]
    color = (255, 255, 255)
    lower = np.array([color[0] - tolerance, color[1] - tolerance, color[2] - tolerance])
    upper = np.array([color[0], color[1], color[2]])
    mask = cv2.inRange(crop, lower, upper)
    crop[mask == 255] = [255, 255, 255]
    crop[mask != 255] = [0, 0, 0]

    if use_mask:
        edges = cv2.Canny(crop, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros_like(crop)
        cv2.drawContours(mask, contours, -1, (255, 255, 255), cv2.FILLED)
        crop = cv2.bitwise_and(crop, mask)

    result = pytesseract.image_to_data(crop, config=f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', timeout=10).lower()
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, location, line[11].lower()).ratio() > 0.6:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
    return None


def read_upgrade_cost(image_input: np.ndarray):
    image = image_input.copy()
    crop = image[image.shape[0] // 2:, :image.shape[1] // 2]

    lower_mask1 = np.array([86, 255, 50])
    upper_mask1 = np.array([86, 255, 170])
    lower_mask2 = np.array([85, 255, 50])
    upper_mask2 = np.array([85, 255, 170])
    mask1 = cv2.inRange(crop, lower_mask1, upper_mask1)
    mask2 = cv2.inRange(crop, lower_mask2, upper_mask2)
    mask = cv2.bitwise_or(mask1, mask2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    x, y, w, h = 0, 0, 0, 0
    for contour in contours:
        rect = cv2.boundingRect(contour)
        area = rect[2] * rect[3]
        if area > max_area:
            x, y, w, h = rect
            max_area = area
    if max_area == 0:
        return None
    try:
        crop = crop[y:y + h, x + w//4:x + w]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
        text = str(pytesseract.image_to_string(thresh, config=f'--psm 8 -c tessedit_char_whitelist=0123456789', timeout=10)).strip()
        if text == "":
            return None
        return [int(text), x + w // 2, (y + h // 2) + (image.shape[0] // 2)]
    except SystemError:
        return None


def read_current_money(image_input: np.ndarray):
    image = image_input.copy()
    image = image[image.shape[0] // 3 * 2:, :]
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
            pytesseract.image_to_string(crop, config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789', timeout=10)).strip()
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
    result = pytesseract.image_to_string(thresh, config=f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', timeout=10)
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


portal_text = {
    "demon": "demonportal",
    "cursed": "cursedkingdomportal",
    "ancient": "ancientdragonportal",
    "solar": "solarportal",
    "lunar": "lunarportal"
}

portal_numbers = {
    1: "demon",
    2: "cursed",
    3: "ancient",
    4: "solar",
    5: "lunar"
}

rarity_numbers = {
    1: "rare",
    2: "epic",
    3: "legendary",
    4: "mythic",
    5: "secret"
}

split_lines = [5.106, 3.609, 2.795, 2.278, 1.922, 1.664]


def word_in_text(word, text, threshold=0.8):
    word_len = len(word)
    for i in range(len(text) - word_len + 1):
        substring = text[i:i + word_len]
        similarity = difflib.SequenceMatcher(None, word, substring).ratio()
        if similarity >= threshold:
            return True
    return False


def find_portal(image_input, portal_type, portal_rarity):
    portal_type = portal_numbers[portal_type]
    portal_rarity = rarity_numbers[portal_rarity]
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    for i in range(5):
        crop = thresh[:, int(thresh.shape[1]//split_lines[i]):int(thresh.shape[1]//split_lines[i+1])]
        tesseract_config = f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        result = pytesseract.image_to_data(crop, config=tesseract_config, timeout=10)
        result = result.split('\n')
        for line in result:
            line = line.split('\t')
            if len(line) == 12 and difflib.SequenceMatcher(None, portal_type, line[11].lower()).ratio() > 0.8:
                x, y, w, h = int(line[6]), int(line[7]), crop.shape[0]//9, crop.shape[0]//9
                crop2 = crop[y:y + h, x:x + w]
                tesseract_config2 = f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890()'
                result2 = pytesseract.image_to_string(crop2, config=tesseract_config2, timeout=10).lower()
                result2 = ''.join(result2.split())
                # if "(" + rarity + ")" in result2:
                #     count = int(re.search(r'\b([1-9]|10)x\b', result2).group(1))
                #     return [count, x + w // 2, y + h // 2]
                if word_in_text(portal_text.get(portal_type), result2) and word_in_text("("+portal_rarity+")", result2):
                    return int((x + w // 2) + thresh.shape[1]//split_lines[i]), y + h // 2


def find_best_portal(image_input, portal_type):
    portal_type = portal_numbers[portal_type]
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    rarity = 0
    for i in range(5):
        crop = thresh[:, int(thresh.shape[1]//split_lines[i]):int(thresh.shape[1]//split_lines[i+1])]
        tesseract_config = f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        result = pytesseract.image_to_data(crop, config=tesseract_config, timeout=10)
        result = result.split('\n')
        for line in result:
            line = line.split('\t')
            if len(line) == 12 and difflib.SequenceMatcher(None, portal_type, line[11].lower()).ratio() > 0.8:
                x, y, w, h = int(line[6]), int(line[7]), crop.shape[0]//9, crop.shape[0]//9
                crop2 = crop[y:y + h, x:x + w]
                tesseract_config2 = f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890()'
                result2 = pytesseract.image_to_string(crop2, config=tesseract_config2, timeout=10).lower()
                result2 = ''.join(result2.split())
                if word_in_text(portal_text.get(portal_type), result2):
                    for rarity_num in rarity_numbers[:-1]:
                        if rarity_num > rarity and word_in_text("("+rarity_numbers.get(rarity_num)+")", result2):
                            rarity = rarity_num
                            if rarity == 4:
                                return rarity
    if rarity > 0:
        return rarity
    return None


def find_all_text(image_input):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return pytesseract.image_to_string(thresh, config=tesseract_config, timeout=10)
