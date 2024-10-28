import pytesseract
import cv2
import numpy as np
import difflib
import re

import coords
from config_loader import load_config
config = load_config()


pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUMBERS = "0123456789"


def find_text(image_input: np.ndarray, text):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, text, line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x+w//2, y+h//2
    return None


def find_game_load(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[:, :thresh.shape[1] // 5]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12:
            keywords = ["units", "items", "quests", "guilds"]
            for keyword in keywords:
                if difflib.SequenceMatcher(None, keyword, line[11].lower()).ratio() > 0.8:
                    return True


def find_start(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[:, thresh.shape[1] // 4 * 3:]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "start", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return (x + w // 2) + (thresh.shape[1] * 3), y + h // 2


def find_sell(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[thresh.shape[0] // 3 * 2:, :thresh.shape[1] // 3]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}{NUMBERS}$'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and '$' == line[11]:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, (y + h // 2) + (thresh.shape[0] * 2)
        if len(line) == 12 and '$' in line[11]:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w, (y + h // 2) + (thresh.shape[0] * 2)


def find_search(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[:thresh.shape[0] // 4, :thresh.shape[1] // 2]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "all", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x - w * 5, y + h // 2


def find_type_here(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "teleport", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x, y - h * 2


def find_open_portal(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "openportal", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x, y + h * 2


def find_play_again(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "playagain", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
        if len(line) == 12 and difflib.SequenceMatcher(None, "playagainbacktolobby", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 4, y + h // 2


def find_back_to_lobby(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "backtolobby", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
        if len(line) == 12 and difflib.SequenceMatcher(None, "playagainbacktolobby", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 4 * 3, y + h // 2


def find_teleport(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "teleport", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
        if len(line) == 12 and difflib.SequenceMatcher(None, "teleportjoinfriend", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 4, y + h // 2


def find_join_friend(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "joinfriend", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
        if len(line) == 12 and difflib.SequenceMatcher(None, "teleportjoinfriend", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 4 * 3, y + h // 2


def find_panic_leave(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[:, thresh.shape[1] // 6 * 5:]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "leave", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2 + (thresh.shape[1] * 5), y + h // 2


def find_friends_only(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "friendsonly", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x - w // 3, y + h // 2


def find_inventory(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[:, :thresh.shape[1] // 4]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "items", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2


def find_speed_up(image_input: np.ndarray, speed):
    speed_map = {"1x": 1, "2x": 2, "3x": 3}
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)
    thresh = thresh[:thresh.shape[0] // 15, thresh.shape[1] // 3:thresh.shape[1] // 3 * 2]
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda i: cv2.boundingRect(i)[0])
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        contour_crop = thresh[y + int(h * 0.2):y + int(h * 0.8), x + int(w * 0.2):x + int(w * 0.8)]
        tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}{NUMBERS}'
        try:
            result = pytesseract.image_to_data(contour_crop, config=tesseract_config, timeout=10)
        except RuntimeError:
            return None
        except SystemError:
            continue
        result = result.split('\n')
        for line in result:
            line = line.split('\t')
            if len(line) == 12 and line[11].lower() in speed_map:
                found_speed = speed_map.get(line[11].lower())
                diff = speed - found_speed
                return x + w // 2 + (diff * int(w * 0.9)) + (image.shape[1] // 3), y + h // 2
    return None


def find_unit_manager(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 253, 255, cv2.THRESH_BINARY)
    thresh = thresh[:, thresh.shape[1] // 5 * 4:]
    tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}'
    try:
        result = pytesseract.image_to_data(thresh, config=tesseract_config, timeout=10)
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, "units", line[11].lower()).ratio() > 0.8:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2 + (image.shape[1] // 5 * 4), y + h // 2


def find_fast_travel(image_input: np.ndarray, location, ratio=3, use_mask=False):
    image = image_input.copy()
    crop = image[:image.shape[0] // ratio, :image.shape[1] // ratio]
    lower = np.array([205, 205, 205])
    upper = np.array([255, 255, 255])
    mask = cv2.inRange(crop, lower, upper)
    crop[mask == 255] = [255, 255, 255]
    crop[mask != 255] = [0, 0, 0]

    if use_mask:
        edges = cv2.Canny(crop, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros_like(crop)
        cv2.drawContours(mask, contours, -1, (255, 255, 255), cv2.FILLED)
        crop = cv2.bitwise_and(crop, mask)

    try:
        result = pytesseract.image_to_data(crop, config=f'--psm 6 -c tessedit_char_whitelist={LETTERS}', timeout=10).lower()
    except RuntimeError:
        return None
    result = result.split('\n')
    for line in result:
        line = line.split('\t')
        if len(line) == 12 and difflib.SequenceMatcher(None, location, line[11].lower()).ratio() > 0.6:
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            return x + w // 2, y + h // 2
    return None


def find_close_menu(image_input: np.ndarray):
    image = image_input.copy()
    crop = image[:image.shape[0] // 2, (image.shape[1] // 2):]
    blue_channel = crop[:, :, 0]
    green_channel = crop[:, :, 1]
    red_channel = crop[:, :, 2]
    thresh = (blue_channel < 40) & (green_channel < 40) & (red_channel > 120)
    thresh = thresh.astype(np.uint8) * 255
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        contour_crop = crop[y:y + h, x:x + w]
        if 0.8 < w / h < 1.2:
            _, contour_thresh = cv2.threshold(cv2.cvtColor(contour_crop, cv2.COLOR_BGR2GRAY), 253, 255, cv2.THRESH_BINARY)
            if 0.05 < cv2.countNonZero(contour_thresh) / (w * h) < 0.15:
                try:
                    result = pytesseract.image_to_string(contour_thresh, config=f'--psm 6 -c tessedit_char_whitelist={LETTERS}', timeout=10).strip().lower()
                except RuntimeError:
                    return None
                if result == "x":
                    return x + w // 2 + (image.shape[1] // 2), y + h // 2
    return None


def read_upgrade_cost(image_input: np.ndarray):
    image = image_input.copy()
    crop = image[image.shape[0] // 2:, :image.shape[1] // 4]

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
        try:
            result = str(pytesseract.image_to_string(thresh, config=f'--psm 8 -c tessedit_char_whitelist={NUMBERS}', timeout=10)).strip()
        except RuntimeError:
            return None
        if result == "":
            return None
        return [int(result), x + w // 2, (y + h // 2) + (image.shape[0] // 2)]
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
    dilate = cv2.dilate(gray, np.ones((3, 3), np.uint8), iterations=10)
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
        text = str(pytesseract.image_to_string(crop, config=f'--psm 8 --oem 3 -c tessedit_char_whitelist={NUMBERS}', timeout=10)).strip()
        if text == "":
            return None
        return int(text)
    except (SystemError, ValueError, RuntimeError):
        return None


def read_current_wave(image_input: np.ndarray):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    thresh = thresh[:thresh.shape[0]//2, :]
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.erode(thresh, kernel, iterations=1)
    try:
        result = pytesseract.image_to_string(thresh, config=f'--psm 6 -c tessedit_char_whitelist={LETTERS}{NUMBERS}', timeout=10)
    except RuntimeError:
        return None
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


rarity_numbers = {
    1: "rare",
    2: "epic",
    3: "legendary",
    4: "mythic",
    5: "secret"
}

portal_numbers = {
    1: "demon",
    2: "cursed",
    3: "ancient",
    4: "solarportal",
    5: "lunarportal"
}

portal_text = {
    "demon": "demonportal",
    "cursed": "cursedkingdomportal",
    "ancient": "ancientdragonportal",
    "solarportal": "solarportal",
    "lunarportal": "lunarportal"
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


def find_portal(image_input, portal_rarity):
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    for i in range(5):
        crop = thresh[:, int(thresh.shape[1]//split_lines[i]):int(thresh.shape[1]//split_lines[i+1])]
        tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}()'
        try:
            result = pytesseract.image_to_data(crop, config=tesseract_config, timeout=10)
        except RuntimeError:
            return None
        result = result.split('\n')
        for line in result:
            line = line.split('\t')
            if len(line) == 12:
                if word_in_text("("+rarity_numbers[portal_rarity]+")", line[11].lower()):
                    return int((int(line[6]) + int(line[8]) // 2) + thresh.shape[1]//split_lines[i]), int(int(line[7]) + int(line[9]) // 2)


def find_best_portal(image_input, max_rarity):
    all_rarities = list(rarity_numbers.keys())
    all_rarities.reverse()
    image = image_input.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
    thresh = thresh[thresh.shape[0]//4:int(thresh.shape[0]//4*3.1), :]
    max_found = 0
    for i in range(5):
        crop = thresh[:, int(thresh.shape[1]//split_lines[i]):int(thresh.shape[1]//split_lines[i+1])]
        tesseract_config = f'--psm 6 -c tessedit_char_whitelist={LETTERS}()'
        try:
            result = pytesseract.image_to_string(crop, config=tesseract_config, timeout=10)
        except RuntimeError:
            return None
        col_max = 0
        valid_max = 0
        for rarity in all_rarities:
            if word_in_text(f"({rarity_numbers.get(rarity)})", result.lower()):
                col_max = max(col_max, rarity)
                if rarity <= max_rarity:
                    valid_max = rarity
                    break
        if col_max < max_found:
            break
        max_found = max(max_found, valid_max)
        if max_found == max_rarity:
            return max_found
    return max_found
