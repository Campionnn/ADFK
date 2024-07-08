import os
import time
import cv2
import numpy as np
import logging
import autoit
import keyboard
import pyautogui
import psutil
import pywinauto

import config
import coords
from utils import ocr
from utils import memory
from utils import control
from utils.memory import get_pids_by_name
from utils.repeated_timer import RepeatedTimer


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
        self.current_wave = [0]
        self.wave_checker = None

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
            app = pywinauto.Application().connect(process=self.pid)
            app.top_window().set_focus()
            self.logger.debug(f"Set foreground window to {self.pid}")
            return True
        except pywinauto.application.ProcessNotFoundError or OSError:
            if self.check_crash():
                self.logger.warning("Roblox instance crashed")
                if start:
                    self.start_account()
                return False

    def get_window_rect(self):
        app = pywinauto.Application().connect(process=self.pid)
        client_rect = app.top_window().rectangle()
        return client_rect.left, client_rect.top, client_rect.width(), client_rect.height()

    def screenshot(self):
        screen = pyautogui.screenshot()
        screen_np = np.array(screen)
        return cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

    def wait_game_load(self, during, restart=True):
        self.logger.debug(f"Waiting for game to load for {self.username}")
        start = time.time()
        while time.time() - start < 30:
            if self.check_crash():
                self.logger.warning("Roblox instance crashed")
                break
            screen = self.screenshot()
            if during == "main":
                if ocr.find_text(screen, "units") is not None:
                    return True
            elif during == "story":
                if ocr.read_current_money(screen) is not None:
                    return True
            elif during == "afk":
                if ocr.find_text(screen, "leaveclaimreward") is not None:
                    return True
        self.logger.warning("Could not detect game start")
        if restart:
            self.logger.warning(f"Restarting account {self.username}")
            self.close_instance()
            time.sleep(3)
            self.start_account()
        return False

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
            if error_message != "":
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

    def click_text(self, text):
        self.logger.debug(f"Clicking text {text} for {self.username}")
        text_coords = ocr.find_text(self.screenshot(), text)
        if text_coords is None:
            return False
        autoit.mouse_click("left", text_coords[0], text_coords[1])
        return True

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

    def check_crash(self):
        return not psutil.pid_exists(self.pid)

    def fast_travel(self, location):
        self.logger.debug(f"Fast traveling to {location} for {self.username}")
        rect = self.click_nav_rect(coords.fast_travel_sequence, "", restart=False)
        time.sleep(0.1)
        attempts = 0
        while rect is None or not self.check_fast_travel(self.screenshot()):
            if attempts > 5:
                return False
            rect = self.click_nav_rect(coords.fast_travel_sequence, "", restart=False)
            attempts += 1
            time.sleep(0.1)
        time.sleep(0.25)
        screen = self.screenshot()
        fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=2)
        if fast_travel_coords is None:
            fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=3)
            if fast_travel_coords is None:
                fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=4)
                if fast_travel_coords is None:
                    self.logger.warning(f"Could not find fast travel location: {location}")
                    return False
        autoit.mouse_click("left", fast_travel_coords[0], fast_travel_coords[1])
        return True

    def check_fast_travel(self, screen):
        self.logger.debug(f"Checking if afk fast travel on screen for {self.username}")
        location = "afk"
        fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=4)
        if fast_travel_coords is None:
            self.logger.warning(f"Could not find afk fast travel location")
            return False
        return True

    def get_address(self):
        if not self.wait_game_load("main"):
            return
        time.sleep(1)
        self.click_text("x")

        init_addresses = []
        attempts = 0
        min_addresses = 900
        max_addresses = 7000
        while len(init_addresses) < min_addresses or len(init_addresses) > max_addresses:
            time.sleep(0.5)
            if not self.fast_travel("leaderboards"):
                return
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
                return
            if len(init_addresses) < min_addresses or len(init_addresses) > max_addresses:
                self.logger.warning("Initial addresses not in desired range. Trying again")
                attempts += 1

        time.sleep(2)
        if not self.fast_travel("trading"):
            return

        self.logger.info(f"Go into the AFK zone for {self.username}. Type 'crash' and press enter if the game crashes or is frozen")
        self.logger.info(f"This will be done automatically once devs fix fast travel locations")
        response = input()
        if response == "crash":
            self.close_instance()
            time.sleep(3)
            self.start_account()
            return

        self.set_foreground(True)
        if not self.wait_game_load("afk"):
            return
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
            return
        self.logger.debug(f"Final address found: {hex(self.y_addrs)}")

        self.set_foreground(True)
        time.sleep(1)
        self.click_text("leaveclaimreward")
        time.sleep(1)
        self.click_text("claim")
        time.sleep(5)

        if not self.wait_game_load("main"):
            return
        time.sleep(2)
        self.click_text("x")

    def teleport_story(self):
        self.set_foreground()
        pos = memory.get_current_pos(self.pid, self.y_addrs)
        attempts = 0
        while self.controller.calculate_distance(pos[0], pos[2], coords.story_play_pos[0], coords.story_play_pos[1]) > 50 and attempts < 5:
            time.sleep(0.5)
            if not self.fast_travel("story"):
                return False
            time.sleep(0.5)
            pos = memory.get_current_pos(self.pid, self.y_addrs)
        time.sleep(0.5)
        if not self.click_text("leave"):
            time.sleep(0.5)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1],coords.story_play_pos_tolerance, 10)
        return True

    def enter_story(self):
        self.logger.debug(f"Entering story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1],
                                  coords.story_enter_pos_tolerance, 20)
        if self.username == self.roblox_instances[0].username:
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            self.select_story()

    def select_story(self):
        self.click_nav_rect(coords.world_sequence, "Could not find world button")
        time.sleep(0.5)
        self.click_text("infinitemode")
        time.sleep(0.5)
        self.click_text("confirm")

    def start_story(self):
        self.placed_towers = []
        self.invalid_towers = []
        self.current_wave = [0]
        self.set_foreground()
        time.sleep(0.5)
        self.click_text("start")

    def play_story(self):
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load("story")
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_place_pos[0], coords.story_place_pos[1], coords.story_place_pos_tolerance, 10, True)
        self.controller.reset()
        time.sleep(0.1)
        self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_place_pos[0], coords.story_place_pos[1], coords.story_place_pos_tolerance / 10, 10, min_speed=0.2, max_speed=0.3, min_turn=0.5, precise=True)
        self.controller.reset()
        self.controller.turn_towards_yaw(self.pid, self.y_addrs, coords.story_place_rot, coords.story_place_rot_tolerance, 0.2)
        self.controller.look_down(1.0)
        time.sleep(1)
        self.controller.reset_look()
        self.controller.zoom_out()

    def place_towers(self, tower_key, num_towers, tower_cost, wave_stop):
        self.set_foreground()
        self.wave_checker = RepeatedTimer(1, self.check_wave)
        for i in range(num_towers):
            if self.find_death_text() is not None:
                self.wave_checker.stop()
                return False

            if self.current_wave[0] >= wave_stop:
                self.wave_checker.stop()
                time.sleep(3)
                return False

            current_money = 0
            while current_money is None or current_money < tower_cost:
                screen = self.screenshot()
                current_money = ocr.read_current_money(screen)
                time.sleep(0.25)

            rect = self.get_window_rect()
            window_width = rect[2]
            window_height = rect[3]
            step = int(window_width * 0.025)
            x = (rect[0] + rect[2] // 2) - step
            y = rect[1] + rect[3] // 2

            directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
            direction_index = 0
            steps_in_current_direction = 0
            change_direction_after_steps = 1

            while 0 <= x < window_width and 0 <= y < window_height:
                if self.find_death_text() is not None:
                    self.wave_checker.stop()
                    return False

                if self.current_wave[0] >= wave_stop:
                    self.wave_checker.stop()
                    time.sleep(3)
                    return False

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

    def upgrade_towers(self, wave_stop):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while True:
            if time.time() - start > 300:
                self.anti_afk()
                start = time.time()

            if config.tower_cap == 0:
                if self.find_death_text() is not None:
                    self.wave_checker.stop()
                    return False
                time.sleep(0.5)

            for x, y in self.placed_towers:
                if self.find_death_text() is not None:
                    self.wave_checker.stop()
                    return False
                if self.current_wave[0] >= wave_stop:
                    self.wave_checker.stop()
                    time.sleep(3)
                    return False
                autoit.mouse_click("left", x, y)
                screen = self.screenshot()
                upgrade_info = ocr.read_upgrade_cost(screen)
                start2 = time.time()
                while time.time() - start2 < 1:
                    if upgrade_info is not None:
                        current_money = ocr.read_current_money(screen)
                        if current_money is not None and current_money >= upgrade_info[0]:
                            autoit.mouse_click("left", upgrade_info[1], upgrade_info[2])
                            self.logger.debug(f"Upgraded tower at {x}, {y}")
                            break
                    screen = self.screenshot()
                    upgrade_info = ocr.read_upgrade_cost(screen)
                    time.sleep(0.1)

    def check_wave(self):
        screen = self.screenshot()
        wave = ocr.read_current_wave(screen)
        if wave is not None and wave != self.current_wave[0]:
            self.current_wave[0] = wave
            self.logger.info(f"Detected wave: {wave}")

    def anti_afk(self):
        for instance in self.roblox_instances:
            instance.set_foreground()
            time.sleep(1)
            for i in range(5):
                instance.controller.jump()
            time.sleep(0.5)
        self.set_foreground()

    def find_death_text(self):
        return ocr.find_text(self.screenshot(), "backtolobby")

    def leave_story_death(self):
        self.set_foreground()
        time.sleep(1)
        x, y = self.find_death_text()
        autoit.mouse_click("left", x, y)

    def leave_story_wave(self):
        self.set_foreground()
        time.sleep(1)
        self.click_nav_rect(coords.settings_sequence, "Could not find settings button", restart=False)
        time.sleep(0.25)
        text = "leavegame"
        fast_travel_coords = ocr.find_fast_travel(self.screenshot(), text)
        if fast_travel_coords is None:
            fast_travel_coords = ocr.find_fast_travel(self.screenshot(), text, ratio=4)
            if fast_travel_coords is None:
                self.logger.warning(f"Could not find leavegame button")
                return False
        autoit.mouse_click("left", fast_travel_coords[0], fast_travel_coords[1])
        time.sleep(0.5)
        self.click_text("leave")

    def close_announcement(self):
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load("main")
        time.sleep(1)
        self.click_text("x")
