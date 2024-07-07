import os
import time
import cv2
import numpy as np
import logging
import autoit
import keyboard
import pyautogui
import psutil
import pywinauto.application
from pywinauto import Application

import coords
from utils import memory
from utils import control
from utils.memory import get_pids_by_name


class Roblox:
    def __init__(self, roblox_instances, logger: logging.Logger, controller: control.Control, username, pid=None, y_addrs=None):
        self.roblox_instances = roblox_instances
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
        self.pid = None
        self.y_addrs = None

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
        self.logger.debug(f"Waiting for Roblox instance for {self.username} to start")

        unique_pids = []
        while len(unique_pids) == 0:
            pids = get_pids_by_name(self.roblox_exe)
            current_pids = [instance.pid for instance in self.roblox_instances]
            unique_pids = [pid for pid in pids if pid not in current_pids]
            time.sleep(1)
        self.pid = unique_pids[0]
        self.logger.debug(f"Roblox instance for {self.username} started. Waiting for window to appear")
        while True:
            try:
                self.set_foreground()
                break
            except RuntimeError:
                time.sleep(1)
        time.sleep(2)
        self.logger.debug(f"Getting memory address for {self.username}")
        self.get_address()
        if self.y_addrs is not None:
            for instance in self.roblox_instances:
                if instance.username == self.username:
                    self.roblox_instances.remove(instance)
            self.roblox_instances.append(self)
            self.logger.debug(f"Memory address for {self.username} is {hex(self.y_addrs)}")
        return

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

    def set_foreground(self, start=False):
        try:
            app = Application().connect(process=self.pid)
            app.top_window().set_focus()
            self.logger.debug(f"Set foreground window to {self.pid}")
            return True
        except pywinauto.application.ProcessNotFoundError or OSError:
            if self.check_crash():
                self.logger.warning("Roblox instance crashed")
                if start:
                    self.start_account()
                return False

    def get_address(self):
        if not self.wait_game_load():
            return None
        time.sleep(1)
        if not self.click_nav_rect(coords.intro_sequence, "Could not find intro close button", restart=False):
            return None

        init_addresses = []
        attempts = 0
        min_addresses = 900
        max_addresses = 7000
        while len(init_addresses) < min_addresses or len(init_addresses) > max_addresses:
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
            if len(init_addresses) < min_addresses or len(init_addresses) > max_addresses:
                self.logger.warning("Initial addresses not in desired range. Trying again")
                attempts += 1

        time.sleep(2)
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

        self.set_foreground(True)
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
        # process = psutil.Process(self.pid)
        # memory_maps = process.memory_maps(grouped=False)
        # all_addresses = [int(region.addr.split('-')[0], 16) for region in memory_maps] + [int(region.addr.split('-')[1], 16) for region in memory_maps]
        # first_address = min(all_addresses)
        # last_address = max(all_addresses)
        # self.logger.debug(f"First address: {hex(first_address)}. Difference: {hex(self.y_addrs - first_address)}")
        # self.logger.debug(f"Last address: {hex(last_address)}. Difference: {hex(last_address - self.y_addrs)}")

        self.set_foreground(True)
        time.sleep(1)
        if not self.wait_game_load():
            return None
        time.sleep(0.5)
        if not self.click_nav_rect(coords.leave_afk_sequence, "Could not find AFK leave button"):
            return None
        time.sleep(1)
        if not self.click_nav_rect(coords.claim_afk_sequence, "Could not find claim afk button"):
            return None
        time.sleep(5)

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
        if not self.click_nav_rect(coords.fast_travel_sequence, "Could not find fast travel button", restart=False):
            self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_backup_pos[0], coords.story_backup_pos[1], coords.story_backup_pos_tolerance, 10)
        time.sleep(0.5)
        self.click_nav_rect(coords.story_sequence, "Could not find story fast travel button", restart=False)
        time.sleep(0.5)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1],coords.story_play_pos_tolerance, 10)

    def enter_story(self):
        self.logger.debug(f"Entering story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance, 20)
        if self.username == self.roblox_instances[0].username:
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            self.select_story()

    def select_story(self):
        self.click_nav_rect(coords.world_sequence, "Could not find world button")
        time.sleep(0.5)
        self.click_nav_rect(coords.infinite_sequence, "Could not find infinite button")
        time.sleep(0.5)
        self.click_nav_rect(coords.confirm_sequence, "Could not find confirm button")

    def start_story(self):
        self.placed_towers = []
        self.invalid_towers = []
        self.set_foreground()
        time.sleep(0.5)
        self.click_nav_rect(coords.start_sequence, "Could not find start button")

    def wait_game_load(self):
        self.logger.debug(f"Waiting for game to load for {self.username}")
        rect = None
        start = time.time()
        while time.time() - start < 30:
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
        if click:
            self.logger.debug(f"Clicking button with sequence {sequence} for {self.username}")
        else:
            self.logger.debug(f"Finding button with sequence {sequence} for {self.username}")
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
        # screen = pyautogui.screenshot(region=self.get_window_rect())
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
        time.sleep(1)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_place_pos[0], coords.story_place_pos[1], coords.story_place_pos_tolerance/5, 10, min_speed=0.2)
        self.controller.reset()
        self.controller.turn_towards_yaw(self.pid, self.y_addrs, coords.story_place_rot, coords.story_place_rot_tolerance)
        self.controller.look_down(1.0)
        time.sleep(1)
        self.controller.reset_look()
        self.controller.zoom_out()

    def check_high_color_percentage(self, color_channel, threshold, percentage, sequence=None, click=False):
        if color_channel == "B":
            color_channel = 0
        elif color_channel == "G":
            color_channel = 1
        elif color_channel == "R":
            color_channel = 2

        rect = None
        if sequence:
            rect = self.click_nav_rect(sequence, "", False, False)
            if not rect:
                return False
        if rect:
            screen = pyautogui.screenshot(region=rect)
        else:
            screen = pyautogui.screenshot()
        image = np.array(screen)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        total_pixels = image.shape[0] * image.shape[1]
        channel = image[:, :, color_channel]
        high_pixels = cv2.inRange(channel, threshold, 255)
        count_high_pixels = cv2.countNonZero(high_pixels)
        high_percentage = (count_high_pixels / total_pixels) * 100
        if high_percentage >= percentage and click:
            x = rect[0] + rect[2] // 2
            y = rect[1] + rect[3] // 2
            autoit.mouse_click("left", x, y)
            return True
        return high_percentage >= percentage

    def get_window_rect(self):
        app = Application().connect(process=self.pid)
        client_rect = app.top_window().rectangle()
        return client_rect.left, client_rect.top, client_rect.width(), client_rect.height()

    def place_towers(self, tower_key, num_towers, wait_time, distance=0.025):
        self.set_foreground()
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

            if self.check_if_dead():
                return False

            while 0 <= x < window_width and 0 <= y < window_height:
                if not self.check_high_color_percentage("R", 150, 30):
                    keyboard.send(tower_key)
                if (x, y) not in self.placed_towers and (x, y) not in self.invalid_towers:
                    autoit.mouse_click("left", x + rect[0], y + rect[1])
                    time.sleep(0.25)
                    if not self.check_high_color_percentage("R", 150, 30):
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

    def upgrade_towers(self):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while True:
            if time.time() - start > 300:
                self.anti_afk()
                start = time.time()
            if len(self.placed_towers) == 0:
                if self.check_if_dead():
                    return False
            for x, y in self.placed_towers:
                if self.check_if_dead():
                    return False
                autoit.mouse_click("left", x, y)
                time.sleep(0.5)
                if self.check_high_color_percentage("G", 200, 60, coords.upgrade_sequence, True):
                    self.logger.debug(f"Upgraded tower at {x}, {y}")

    def anti_afk(self):
        for instance in self.roblox_instances:
            instance.set_foreground()
            time.sleep(1)
            for i in range(5):
                instance.controller.jump()
            time.sleep(0.5)
        self.set_foreground()

    def check_if_dead(self):
        dead = self.check_high_color_percentage("R", 200, 60, coords.check_death_sequence)
        return dead

    def leave_story(self):
        self.set_foreground()
        time.sleep(1)
        self.click_nav_rect(coords.check_death_sequence, "Could not find leave button")
        time.sleep(1)
        self.wait_game_load()
        time.sleep(1)
        self.click_nav_rect(coords.intro_sequence, "Could not find intro close button")


