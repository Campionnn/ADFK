import os
import time
import cv2
import numpy as np
import logging
import autoit
import keyboard
import pyautogui
from pywinauto import Application

import coords
from utils import memory
from utils import control
from utils.memory import get_pids_by_name


class Roblox:
    def __init__(self, logger: logging.Logger, controller: control.Control, username, pid=None, y_addrs=None):
        self.logger = logger
        self.controller = controller
        self.pid = pid
        self.username = username
        self.y_addrs = y_addrs

        self.roblox_exe = "RobloxPlayerBeta.exe"
        self.place_id = "17017769292"

        self.start_account()

    def start_account(self):
        # params = {
        #     "Account": self.username,
        #     "PlaceId": self.place_id,
        #     # "JobId": config.private_server_code,
        # }
        # if config.password != "":
        #     params["Password"] = config.password
        # result = requests.get(f"http://localhost:{config.port}/LaunchAccount", params=params)
        # return result.status_code
        self.logger.info(f"Join private server with account {self.username} from Roblox Account Manager")
        self.logger.info(f"This will automatically start once I fix the bug with RAM")
        return 200

    def close_instance(self):
        self.logger.debug(f"Closing Roblox instance for {self.username}")
        try:
            os.kill(self.pid, 15)
        except Exception as e:
            self.logger.warning(f"Failed to close Roblox instance: {e}")
        while True:
            if self.pid not in get_pids_by_name(self.roblox_exe):
                break
            time.sleep(1)
        return True

    def set_foreground(self):
        app = Application().connect(process=self.pid)
        app.top_window().set_focus()
        self.logger.debug(f"Set foreground window to {self.pid}")

    def get_address(self):
        self.set_foreground()
        if not self.wait_game_load():
            return None
        time.sleep(1)
        if not self.click_nav_rect(coords.intro_sequence, "Could not find intro close button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.fast_travel_sequence, "Could not find fast travel button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.leaderboard_sequence, "Could not find leaderboard fast travel"):
            return None
        time.sleep(1.0)

        self.logger.debug(f"Searching for initial addresses for {self.username}...")
        init_addresses = memory.search_init_pos(self.pid, coords.init_pos1, coords.init_tolerance1)
        self.logger.debug(f"Initial addresses found: {len(init_addresses)}")
        if len(init_addresses) < 1000 or len(init_addresses) > 7000:
            # TODO: addresses should be somewhere in this range. if not teleport again and try again
            pass

        if not self.click_nav_rect(coords.fast_travel_sequence, "Could not find fast travel button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.afk_sequence, "Could not find afk fast travel button"):
            return None

        self.logger.info(f"Go into the AFK zone for {self.username}. Type 'crash' and press enter if the game crashes or is frozen")
        self.logger.info(f"This will be done automatically once devs fix fast travel locations")
        response = input()
        if response == "crash":
            self.close_instance()
            time.sleep(3)
            self.start_account()
            return None

        self.set_foreground()
        if not self.wait_game_load():
            return None
        time.sleep(2)
        self.logger.debug(f"Refining addresses to find final address for {self.username}...")
        final_addresses = memory.search_final_pos(self.pid, init_addresses, coords.init_pos2, coords.init_tolerance2)
        for address in final_addresses:
            rot = memory.get_current_rot(self.pid, address)
            if rot[1] == 270.0 and abs(rot[0] + 0.6) < 0.1:
                self.y_addrs = address
                break
        if self.y_addrs is None:
            self.logger.warning("Could not find final address")
            self.logger.warning(f"Restarting account {self.username}")
            self.close_instance()
            time.sleep(3)
            self.start_account()
            return None
        self.logger.debug(f"Final address found: {hex(self.y_addrs)}")

        self.set_foreground()
        if not self.click_nav_rect(coords.leave_afk_sequence, "Could not find AFK leave button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.claim_afk_sequence, "Could not find claim afk button"):
            return None
        time.sleep(3)

        if not self.wait_game_load():
            return None
        time.sleep(2)
        if not self.click_nav_rect(coords.intro_sequence, "Could not find intro close button"):
            return None

        return self.y_addrs

    def enter_story(self):
        self.logger.debug(f"Entering story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        if not self.click_nav_rect(coords.fast_travel_sequence, "Could not find fast travel button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.story_sequence, "Could not find story fast travel button"):
            return None
        time.sleep(1)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1], coords.story_play_pos_tolerance)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance)

    def select_story(self):
        if not self.click_nav_rect(coords.world_sequence, "Could not find world button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.infinite_sequence, "Could not find infinite button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.confirm_sequence, "Could not find confirm button"):
            return None

    def start_story(self):
        self.set_foreground()
        time.sleep(0.5)
        if not self.click_nav_rect(coords.start_sequence, "Could not find start button"):
            return None

    def wait_game_load(self):
        self.logger.debug(f"Waiting for game to load for {self.username}")
        rect = None
        for i in range(30):
            keyboard.press_and_release("\\")
            time.sleep(0.5)
            rect = self.find_nav_rect("")
            if rect is not False:
                keyboard.press_and_release("\\")
                break
            time.sleep(1)
        if rect is None:
            self.logger.warning("Could not detect game start")
            self.logger.warning(f"Restarting account {self.username}")
            self.close_instance()
            time.sleep(3)
            self.start_account()
            return False
        return True

    def click_nav_rect(self, sequence, error_message):
        self.logger.debug(f"Clicking button with sequence {sequence} for {self.username}")
        keyboard.press_and_release("\\")
        time.sleep(0.1)
        rect = self.find_nav_rect(sequence)
        keyboard.press_and_release("\\")
        if rect is None:
            self.logger.warning(error_message)
            self.logger.warning(f"Restarting account {self.username}")
            self.close_instance()
            time.sleep(3)
            self.start_account()
            return False
        autoit.mouse_click("left", rect[0], rect[1])
        return True

    @staticmethod
    def find_nav_rect(sequence):
        for key in list(sequence):
            time.sleep(0.05)
            keyboard.press_and_release(key)
        time.sleep(0.5)
        screen = pyautogui.screenshot()
        screen_np = np.array(screen)
        image = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                if 0.8 * (w * h) <= area <= 1.2 * (w * h):
                    return x+w//2, y+h//2
        return None

    def play_story(self):
        pid = list(self.roblox_pids.keys())[0]
        y_address = self.roblox_pids[pid]
        username = config.usernames[0]
        self.set_foreground_window(pid)
        time.sleep(1)
        self.wait_game_load(username)
