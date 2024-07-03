import keyboard
import requests
import time
import os
import cv2
import autoit
import pyautogui
import logging
import numpy as np
from pywinauto import Application

import memory
import coords
import config
from control import Control
if config.port == 0000:
    import config_personal as config
from memory import get_pids_by_name


class Roblox:
    def __init__(self, logger: logging.Logger, roblox_pids=None):
        self.place_id = "17017769292"
        self.roblox_exe = "RobloxPlayerBeta.exe"

        self.logger = logger
        self.roblox_pids = {}
        if roblox_pids is not None:
            self.roblox_pids = roblox_pids
        self.controller = Control(self.logger)

    def set_foreground_window(self, pid):
        app = Application().connect(process=pid)
        app.top_window().set_focus()
        self.logger.debug(f"Set foreground window to {pid}")

    def start_all_accounts(self):
        for i, username in enumerate(config.usernames):
            if self.start_account(username) != 200:
                self.logger.error(f"Failed to start Roblox instance for {username}")
                continue
            self.logger.debug(f"Waiting for Roblox instance for {username} to start")
            while True:
                pids = get_pids_by_name(self.roblox_exe)
                for pid in pids:
                    if pid in self.roblox_pids.keys():
                        pids.remove(pid)
                if len(pids) != 0:
                    self.logger.debug(f"Roblox instance for {username} started")
                    time.sleep(15)
                    self.logger.debug(f"Getting memory address for {username}")
                    address = self.get_address(pids[0], username)
                    if address is not None:
                        self.logger.debug(f"Memory address for {username} is {hex(address)}")
                        break
                time.sleep(1)
            self.roblox_pids[pids[0]] = address
        return self.roblox_pids

    def start_account(self, username):
        # params = {
        #     "Account": username,
        #     "PlaceId": self.place_id,
        #     # "JobId": config.private_server_code,
        # }
        # if config.password != "":
        #     params["Password"] = config.password
        # result = requests.get(f"http://localhost:{config.port}/LaunchAccount", params=params)
        # return result.status_code
        self.logger.info(f"Join private server with account {username} from Roblox Account Manager")
        self.logger.info(f"This will automatically start once I fix the bug with RAM")
        return 200

    def get_address(self, pid, username):
        self.set_foreground_window(pid)
        if not self.wait_game_load(username):
            return None
        time.sleep(1)
        if not self.click_nav_rect(coords.intro_sequence, username, "Could not find intro close button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.fast_travel_sequence, username, "Could not find fast travel button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.leaderboard_sequence, username, "Could not find leaderboard fast travel"):
            return None
        time.sleep(1.0)

        self.logger.debug(f"Searching for initial addresses for {username}...")
        init_addresses = memory.search_init_pos(pid, coords.init_pos1, coords.init_tolerance1)
        self.logger.debug(f"Initial addresses found: {len(init_addresses)}")
        if len(init_addresses) < 1000 or len(init_addresses) > 7000:
            # TODO: addresses should be somewhere in this range. if not teleport again and try again
            pass

        if not self.click_nav_rect(coords.fast_travel_sequence, username, "Could not find fast travel button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.afk_sequence, username, "Could not find afk fast travel button"):
            return None

        self.logger.info(f"Go into the AFK zone for {username}. Type 'crash' and press enter if the game crashes or is frozen")
        self.logger.info(f"This will be done automatically once devs fix fast travel locations")
        response = input()
        if response == "crash":
            self.close_by_username(username)
            time.sleep(3)
            self.start_account(username)
            return None

        self.set_foreground_window(pid)
        if not self.wait_game_load(username):
            return None
        time.sleep(2)
        self.logger.debug(f"Refining addresses to find final address for {username}...")
        final_addresses = memory.search_final_pos(pid, init_addresses, coords.init_pos2, coords.init_tolerance2)
        final_address = None
        for address in final_addresses:
            rot = memory.get_current_rot(pid, address)
            if rot[1] == 270.0 and abs(rot[0] + 0.6) < 0.1:
                final_address = address
                break
        if final_address is None:
            self.logger.warning("Could not find final address")
            self.logger.warning(f"Restarting account {username}")
            self.close_by_username(username)
            time.sleep(3)
            self.start_account(username)
            return None
        self.logger.debug(f"Final address found: {hex(final_address)}")

        self.set_foreground_window(pid)
        if not self.click_nav_rect(coords.leave_afk_sequence, username, "Could not find AFK leave button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.claim_afk_sequence, username, "Could not find claim afk button"):
            return None
        time.sleep(3)

        if not self.wait_game_load(username):
            return None
        time.sleep(2)
        if not self.click_nav_rect(coords.intro_sequence, username, "Could not find intro close button"):
            return None

        return final_address

    def all_enter_story(self):
        self.logger.debug("Entering story for all accounts")
        for i, pid in enumerate(self.roblox_pids.keys()):
            username = config.usernames[i]
            self.enter_story(pid, self.roblox_pids[pid], username)
            if i == 0:
                if not self.click_nav_rect(coords.world_sequence, username, "Could not find world button"):
                    return None
                time.sleep(0.5)
                if not self.click_nav_rect(coords.infinite_sequence, username, "Could not find infinite button"):
                    return None
                time.sleep(0.5)
                if not self.click_nav_rect(coords.confirm_sequence, username, "Could not find confirm button"):
                    return None
        self.logger.debug(f"Starting story")
        time.sleep(0.5)
        self.set_foreground_window(list(self.roblox_pids.keys())[0])
        time.sleep(0.5)
        if not self.click_nav_rect(coords.start_sequence, config.usernames[0], "Could not find start button"):
            return None

    def enter_story(self, pid, y_address, username):
        self.logger.debug(f"Entering story for {username}")
        self.set_foreground_window(pid)
        time.sleep(1)
        if not self.click_nav_rect(coords.fast_travel_sequence, username, "Could not find fast travel button"):
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.story_sequence, username, "Could not find story fast travel button"):
            return None
        time.sleep(1)
        self.controller.go_to_pos(pid, y_address, coords.story_play_pos[0], coords.story_play_pos[1], coords.story_play_pos_tolerance)
        self.controller.go_to_pos(pid, y_address, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance)

    def wait_game_load(self, username):
        self.logger.debug(f"Waiting for game to load for {username}")
        rect = None
        for i in range(30):
            rect = self.detect_game_start()
            if rect is not False:
                break
            time.sleep(1)
        if rect is None:
            self.logger.warning("Could not detect game start")
            self.logger.warning(f"Restarting account {username}")
            self.close_by_username(username)
            time.sleep(3)
            self.start_account(username)
            return False
        return True

    def detect_game_start(self):
        keyboard.press_and_release("\\")
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
                    keyboard.press_and_release("\\")
                    return x + w // 2, y + h // 2
        return False

    def find_nav_rect(self, sequence):
        keyboard.press_and_release("\\")
        time.sleep(0.1)
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
                    keyboard.press_and_release("\\")
                    return x+w//2, y+h//2
        keyboard.press_and_release("\\")
        return None

    def click_nav_rect(self, sequence, username, error_message):
        self.logger.debug(f"Clicking button with sequence {sequence} for {username}")
        rect = self.find_nav_rect(sequence)
        if rect is None:
            self.logger.warning(error_message)
            self.logger.warning(f"Restarting account {username}")
            self.close_by_username(username)
            time.sleep(3)
            self.start_account(username)
            return False
        autoit.mouse_click("left", rect[0], rect[1])
        return True

    def close_by_username(self, username):
        self.logger.debug(f"Closing Roblox instance for {username}")
        for pid in self.roblox_pids.keys():
            if self.roblox_pids[pid] == username:
                try:
                    os.kill(pid, 15)
                except:
                    pass
                while True:
                    if not pid in get_pids_by_name(self.roblox_exe):
                        break
                    time.sleep(1)
                return True
        return False
