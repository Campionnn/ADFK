import os
import time
import cv2
import numpy as np
import logging
import autoit
import keyboard
import pyautogui
import psutil
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

        self.placed_towers = []
        self.invalid_towers = []

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
        if not self.wait_game_load():
            return None
        time.sleep(1)
        if not self.click_nav_rect(coords.intro_sequence, "Could not find intro close button"):
            return None

        init_addresses = []
        attempts = 0
        while len(init_addresses) < 1000 or len(init_addresses) > 7000:
            time.sleep(0.5)
            if not self.click_nav_rect(coords.fast_travel_sequence, "Could not find fast travel button"):
                return None
            time.sleep(0.5)
            if not self.click_nav_rect(coords.leaderboard_sequence, "Could not find leaderboard fast travel"):
                return None
            time.sleep(1.0)

            self.logger.debug(f"Searching for initial addresses for {self.username}")
            init_addresses = memory.search_init_pos(self.pid, coords.init_pos1, coords.init_tolerance1)
            self.logger.debug(f"Initial addresses found: {len(init_addresses)}")
            if attempts > 5:
                self.logger.warning("Could not find initial addresses")
                self.logger.warning(f"Restarting account {self.username}")
                self.close_instance()
                time.sleep(3)
                self.start_account()
                return None
            if len(init_addresses) < 1000 or len(init_addresses) > 7000:
                self.logger.warning("Initial addresses not in desired range. Trying again")
                attempts += 1

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

    def teleport_story(self):
        self.logger.debug(f"Teleporting to story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        self.click_nav_rect(coords.fast_travel_sequence, "Could not find fast travel button")
        time.sleep(0.5)
        self.click_nav_rect(coords.story_sequence, "Could not find story fast travel button")
        time.sleep(0.5)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1],coords.story_play_pos_tolerance, 10)

    def enter_story(self):
        self.logger.debug(f"Entering story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance, 20)

    def select_story(self):
        self.click_nav_rect(coords.world_sequence, "Could not find world button")
        time.sleep(0.5)
        self.click_nav_rect(coords.infinite_sequence, "Could not find infinite button")
        time.sleep(0.5)
        self.click_nav_rect(coords.confirm_sequence, "Could not find confirm button")

    def start_story(self):
        self.set_foreground()
        time.sleep(0.5)
        self.click_nav_rect(coords.start_sequence, "Could not find start button")

    def wait_game_load(self):
        self.logger.debug(f"Waiting for game to load for {self.username}")
        rect = None
        for i in range(30):
            if self.check_crash():
                self.logger.warning("Roblox instance crashed")
                break
            keyboard.send("\\")
            time.sleep(0.25)
            rect = self.find_nav_rect("")
            if rect is not None:
                keyboard.send("\\")
                break
        if rect is None:
            self.logger.warning("Could not detect game start")
            self.logger.warning(f"Restarting account {self.username}")
            self.close_instance()
            time.sleep(3)
            self.start_account()
            return False
        return True

    def click_nav_rect(self, sequence, error_message, click=True, restart=True):
        self.logger.debug(f"Clicking button with sequence {sequence} for {self.username}")
        keyboard.send("\\")
        time.sleep(0.1)
        rect = self.find_nav_rect(sequence)
        keyboard.send("\\")
        if rect is None:
            self.logger.warning(error_message)
            if restart:
                self.logger.warning(f"Restarting account {self.username}")
                self.close_instance()
                time.sleep(3)
                self.start_account()
            return False
        if click:
            x = rect[0] + rect[2] // 2
            y = rect[1] + rect[3] // 2
            autoit.mouse_click("left", x, y)
        return rect

    def find_nav_rect(self, sequence):
        for key in list(sequence):
            time.sleep(0.05)
            keyboard.send(key)
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
                    return x, y, w, h
        return None

    def check_crash(self):
        return not psutil.pid_exists(self.pid)

    def play_story(self):
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load()
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_place_pos[0], coords.story_place_pos[1], coords.story_place_pos_tolerance, 10, True)
        self.controller.reset()
        self.controller.turn_towards_yaw(self.pid, self.y_addrs, coords.story_place_rot, coords.story_place_rot_tolerance)
        self.controller.look_down(1.0)
        time.sleep(1)
        self.controller.reset_look()
        self.controller.zoom_out()

    def check_if_tower_place(self):
        blue_threshold = 200
        percentage = 90

        rect = self.click_nav_rect(coords.target_sequence, "", False, False)
        if not rect:
            return False
        screen = pyautogui.screenshot(region=rect)
        image = np.array(screen)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        total_pixels = image.shape[0] * image.shape[1]
        blue_channel = image[:, :, 0]
        high_blue_pixels = cv2.inRange(blue_channel, blue_threshold, 255)
        count_high_blue_pixels = cv2.countNonZero(high_blue_pixels)
        high_blue_percentage = (count_high_blue_pixels / total_pixels) * 100
        return high_blue_percentage >= percentage

    def check_if_place_mode(self):
        red_threshold = 200
        percentage = 30

        screen = pyautogui.screenshot()
        image = np.array(screen)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        total_pixels = image.shape[0] * image.shape[1]
        red_channel = image[:, :, 2]
        high_red_pixels = cv2.inRange(red_channel, red_threshold, 255)
        count_high_red_pixels = cv2.countNonZero(high_red_pixels)
        high_red_percentage = (count_high_red_pixels / total_pixels) * 100
        return high_red_percentage >= percentage

    def get_window_rect(self):
        app = Application().connect(process=self.pid)
        rect = app.top_window().rectangle()
        return rect.left, rect.top, rect.width(), rect.height()

    def place_towers(self, tower_key, num_towers, wait_time, distance=0.025):
        self.set_foreground()
        time.sleep(1)
        for i in range(num_towers):
            time.sleep(wait_time)
            rect = self.get_window_rect()
            window_width = rect[2]
            window_height = rect[3]
            step = int(window_width * distance)
            x = (rect[0] + rect[2] // 2) - step
            y = rect[1] + rect[3] // 2

            directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
            direction_index = 0
            steps_in_current_direction = 0
            change_direction_after_steps = 1

            while 0 <= x < window_width and 0 <= y < window_height:
                if not self.check_if_place_mode():
                    keyboard.send(tower_key)
                if (x, y) not in self.placed_towers and (x, y) not in self.invalid_towers:
                    autoit.mouse_click("left", x + rect[0], y + rect[1])
                    time.sleep(0.5)
                    autoit.mouse_click("left", x + rect[0], y + rect[1])
                    time.sleep(0.1)
                    if self.check_if_tower_place():
                        self.logger.debug(f"Placed tower at {x}, {y}")
                        self.placed_towers.append((x, y))
                        break
                    self.invalid_towers.append((x, y))

                steps_in_current_direction += 1
                if steps_in_current_direction == change_direction_after_steps:
                    direction_index = (direction_index + 1) % 4
                    steps_in_current_direction = 0
                    if direction_index == 0 or direction_index == 2:
                        change_direction_after_steps += 1
                dx, dy = directions[direction_index]
                x += dx * step
                y += dy * step
            if 0 > x > window_width and 0 > y > window_height:
                self.logger.warning("Could not place tower")
                continue
        return True
