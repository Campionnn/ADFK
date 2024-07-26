import os
import time
import cv2
import numpy as np
import logging
import subprocess
import autoit
import keyboard
import pyautogui
import psutil
import pywinauto
import requests
from abc import ABC, abstractmethod

try:
    import config_personal as config
except ImportError:
    import config
import coords
from utils.exceptions import *
from utils import ocr
from utils import memory
from utils import control
from utils.memory import get_pids_by_name
from utils.repeated_timer import RepeatedTimer


ROBLOX_EXE = "RobloxPlayerBeta.exe"
PLACE_ID = "17017769292"

class RobloxBase(ABC):
    def __init__(self, roblox_instances, logger: logging.Logger, controller: control.Control, username, world, level, custom_sequence, pid=None, y_addrs=None):
        self.roblox_instances = roblox_instances
        self.logger = logger
        self.controller = controller
        self.username = username
        self.world = world
        self.level = level
        self.custom_sequence = custom_sequence
        self.pid = pid
        self.y_addrs = y_addrs

        self.world_sequence = None
        self.place_pos = None
        self.place_pos_tolerance = None
        self.place_rot = None
        self.place_rot_tolerance = None
        self.place_color = None
        self.place_color_tolerance = None

        self.spiral_coords = []
        self.placed_towers = {}
        self.invalid_towers = []
        self.current_wave = [0]
        self.wave_checker = None

    def start_account(self):
        self.pid = None
        self.y_addrs = None

        params = {
            "Account": self.username,
            "PlaceId": PLACE_ID,
            "JobId": config.private_server_link,
        }
        if config.password != "":
            params["Password"] = config.password
        result = requests.get(f"http://localhost:{config.port}/LaunchAccount", params=params)
        if result.status_code != 200:
            raise StartupException(f"Failed to launch Roblox instance for {self.username}")

        self.logger.debug(f"Waiting for Roblox instance for {self.username} to start")
        time.sleep(3)
        unique_pids = []
        while len(unique_pids) == 0:
            pids = get_pids_by_name(ROBLOX_EXE)
            current_pids = [instance.pid for instance in self.roblox_instances]
            unique_pids = [pid for pid in pids if pid not in current_pids]
            time.sleep(1)
        if len(unique_pids) > 1:
            raise PlayException(f"Too many Roblox instances found")
        self.pid = unique_pids[0]
        self.logger.debug(f"Roblox instance for {self.username} started. Waiting for window to appear")
        start = time.time()
        while time.time() - start < 60:
            self.check_crash(False)
            try:
                self.set_foreground()
                break
            except StartupException:
                time.sleep(1)
        if time.time() - start >= 60:
            raise StartupException(f"Could not set foreground window: {self.pid}")
        time.sleep(3)

        if not self.wait_game_load("main"):
            return
        time.sleep(0.5)
        self.click_text("x")
        if not self.fast_travel("leaderboards"):
            self.controller.jump()
            time.sleep(0.5)
            self.controller.look_down(1.0)
            time.sleep(1)
            self.controller.reset_look()
            if not self.fast_travel("leaderboards"):
                raise StartupException("Could not fast travel to leaderboards")
        time.sleep(0.5)
        self.controller.look_down(1.0)
        time.sleep(1.0)
        self.controller.reset_look()
        self.y_addrs = memory.search_new(self.pid, coords.init_pos_x, coords.init_pos_y, coords.init_pos_z, coords.init_pos_tolerance, coords.init_pitch, coords.init_pitch_tolerance)
        if self.y_addrs is None:
            raise StartupException("Could not find memory address")
        self.logger.debug(f"Memory address found for {self.username}. {self.pid}: {self.y_addrs}")
        return

    def close_instance(self):
        self.logger.debug(f"Killing Roblox instance for {self.username}")
        try:
            os.kill(self.pid, 15)
            try:
                self.wave_checker.stop()
            except AttributeError:
                pass
        except OSError:
            pass
        while True:
            self.logger.debug("Waiting for Roblox instance to close")
            if self.pid not in get_pids_by_name(ROBLOX_EXE):
                break
            time.sleep(1)
        time.sleep(3)
        return True

    def set_foreground(self):
        try:
            app = pywinauto.Application().connect(process=self.pid)
            app.top_window().set_focus()
            self.logger.debug(f"Set foreground window to {self.pid}")
            return True
        except (pywinauto.application.ProcessNotFoundError, OSError, RuntimeError):
            raise StartupException(f"Could not set foreground window: {self.pid}")

    def get_window_rect(self):
        app = pywinauto.Application().connect(process=self.pid)
        client_rect = app.top_window().rectangle()
        return client_rect.left, client_rect.top, client_rect.width(), client_rect.height()

    def screenshot(self):
        screen = pyautogui.screenshot()
        screen_np = np.array(screen)
        return cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

    def wait_game_load(self, during):
        self.logger.debug(f"Waiting for game to load for {self.username}")
        start = time.time()
        while time.time() - start < 60:
            self.check_crash()
            screen = self.screenshot()
            match during:
                case "main":
                    if ocr.find_text(screen, "units") is not None:
                        return True
                case "story":
                    money = ocr.read_current_money(screen)
                    if money is not None and money > 0:
                        return True
        match during:
            case "main":
                raise StartupException("Could not detect main screen load")
            case "story":
                raise StartupException("Could not detect story load")

    def click_nav_rect(self, sequence, error_message, click=True, restart=True, chapter=False):
        if click:
            self.logger.debug(f"Clicking button with sequence {sequence} for {self.username}")
        else:
            self.logger.debug(f"Finding button with sequence {sequence} for {self.username}")
        keyboard.send("\\")
        time.sleep(0.1)
        rect = self.find_nav_rect(sequence, chapter)
        keyboard.send("\\")
        if rect is None:
            if error_message != "":
                self.logger.warning(error_message)
            if restart:
                raise StartupException("Could not find navigation button")
            return False
        if click:
            x = rect[0] + rect[2] // 2
            y = rect[1] + rect[3] // 2
            autoit.mouse_click("left", x, y)
        return rect

    def click_text(self, text, numbers=False):
        self.logger.debug(f"Clicking text {text} for {self.username}")
        text_coords = ocr.find_text(self.screenshot(), text, numbers)
        if text_coords is None:
            return False
        autoit.mouse_click("left", text_coords[0], text_coords[1])
        return True

    def find_nav_rect(self, sequence="", chapter=False):
        for key in list(sequence):
            time.sleep(0.1)
            keyboard.send(key)
        time.sleep(0.5)
        screen = pyautogui.screenshot()
        screen_np = np.array(screen)

        if chapter:
            screen_crop = screen_np[:, screen_np.shape[1] // 3:]
        else:
            screen_crop = screen_np[:int(screen_np.shape[0] * 0.9), :]

        image = cv2.cvtColor(screen_crop, cv2.COLOR_RGB2BGR)
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
                    if chapter:
                        return x + screen_np.shape[1] // 3, y, w, h
                    return x, y, w, h
        return None

    def check_placement(self):
        image = pyautogui.screenshot()
        image_np = np.array(image)
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        blue_channel = image_np[:, :, 0]
        green_channel = image_np[:, :, 1]
        red_channel = image_np[:, :, 2]
        mask = (blue_channel < self.place_color[0]) & (green_channel < self.place_color[1]) & (red_channel > self.place_color[2])

        total_pixels = image_np.shape[0] * image_np.shape[1]
        matching_pixels = np.sum(mask)
        matching_percentage = (matching_pixels / total_pixels) * 100

        return matching_percentage > self.place_color_tolerance

    def check_crash(self, responsive=True):
        if self.pid is None:
            raise StartupException("Roblox pid does not exist")
        if not psutil.pid_exists(self.pid):
            raise StartupException("Roblox instance crashed")
        if responsive:
            cmd = 'tasklist /FI "PID eq %d" /FI "STATUS eq running"' % self.pid
            status = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout.read()
            if not str(self.pid) in str(status):
                raise StartupException("Roblox instance crashed")

    def fast_travel(self, location):
        self.logger.debug(f"Fast traveling to {location} for {self.username}")
        rect = self.click_nav_rect(coords.fast_travel_sequence, "", restart=False)
        time.sleep(0.1)
        attempts = 0
        while rect is None or not self.check_fast_travel(self.screenshot()):
            if attempts > 2:
                return False
            self.check_crash()
            rect = self.click_nav_rect(coords.fast_travel_sequence, "", restart=False)
            attempts += 1
            time.sleep(0.1)
        time.sleep(0.25)
        screen = self.screenshot()
        fast_travel_coords = None
        for i in range(2, 5):
            fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=i)
            if fast_travel_coords is not None:
                break
            else:
                fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=i, use_mask=True)
                if fast_travel_coords is not None:
                    break
        if fast_travel_coords is None:
            self.logger.warning(f"Could not find fast travel location: {location}")
            return False
        autoit.mouse_click("left", fast_travel_coords[0], fast_travel_coords[1])
        return True

    def check_fast_travel(self, screen):
        self.logger.debug(f"Checking if fast travel menu is open for {self.username}")
        location = "challenges"
        fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=4)
        if fast_travel_coords is None:
            fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=4, use_mask=True)
            if fast_travel_coords is None:
                return False
        return True

    @abstractmethod
    def set_coords(self):
        pass

    @abstractmethod
    def teleport(self):
        pass

    @abstractmethod
    def enter(self, depth=0):
        pass

    @abstractmethod
    def start(self):
        pass

    def spiral(self):
        spiral_coords = []
        rect = self.get_window_rect()
        window_width = int(rect[2] * 0.8)
        window_height = int(rect[3] * 0.8)
        step = int(rect[2] * 0.025)
        x = (rect[0] + rect[2] // 2) - step
        y = rect[1] + rect[3] // 2

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        direction_index = 0
        steps_in_current_direction = 0
        change_direction_after_steps = 1

        spiral_coords.append((x + step, y))
        while 0 <= x < window_width and 0 <= y < window_height:
            spiral_coords.append((x, y))
            steps_in_current_direction += 1
            if steps_in_current_direction == change_direction_after_steps:
                direction_index = (direction_index + 1) % 4
                steps_in_current_direction = 0
                if direction_index == 0 or direction_index == 2:
                    change_direction_after_steps += 1
            dx, dy = directions[direction_index]
            x += dx * step
            y += dy * step

        self.spiral_coords = spiral_coords

    def play(self):
        self.placed_towers = {}
        self.invalid_towers = []
        self.current_wave = [0]
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load("story")
        self.spiral()
        attempts = 0
        while True:
            if attempts > 2:
                raise PlayException("Could not go to place position")
            if not self.controller.go_to_pos(self.pid, self.y_addrs, self.place_pos[0], self.place_pos[1], self.place_pos_tolerance, 10, True):
                self.controller.unstuck(self.pid, self.y_addrs)
                attempts += 1
            else:
                break
        self.controller.reset()
        time.sleep(0.1)
        attempts = 0
        while True:
            if attempts > 2:
                raise PlayException("Could not go to place position")
            if not self.controller.go_to_pos(self.pid, self.y_addrs, self.place_pos[0], self.place_pos[1], self.place_pos_tolerance/10, 10, min_speed=0.2, max_speed=0.3, min_turn=0.5, precise=True):
                self.controller.unstuck(self.pid, self.y_addrs)
                attempts += 1
            else:
                break
        self.controller.reset()
        self.controller.turn_towards_yaw(self.pid, self.y_addrs, self.place_rot, self.place_rot_tolerance, 0.2)
        self.controller.look_down(1.0)
        time.sleep(1)
        self.controller.reset_look()
        self.controller.zoom_out(1)

    def do_custom_sequence(self):
        self.set_foreground()
        time.sleep(0.5)
        self.wave_checker = RepeatedTimer(1, self.check_wave)
        start = time.time()
        for action in self.custom_sequence.get('actions'):
            if action.get('type') == 'place':
                for tower_id in action.get("ids"):
                    if time.time() - start > 300:
                        self.anti_afk()
                        start = time.time()
                    if not self.place_tower(tower_id, tower_id[0], action.get('location'), int(self.custom_sequence.get('costs').get(tower_id[0]))):
                        return False
            elif action.get('type') == 'upgrade':
                if int(action.get('amount')) == 0:
                    while True:
                        for tower_id in action.get("ids"):
                            if time.time() - start > 300:
                                self.anti_afk()
                                start = time.time()
                            if not self.upgrade_tower(tower_id, True):
                                return False
                for _ in range(int(action.get('amount'))):
                    for tower_id in action.get("ids"):
                        if time.time() - start > 300:
                            self.anti_afk()
                            start = time.time()
                        if not self.upgrade_tower(tower_id):
                            return False
            time.sleep(0.5)
        while True:
            if self.check_over():
                return False
            time.sleep(0.5)

    def place_tower(self, tower_id, hotkey, location, cost):
        self.logger.debug(f"Placing tower with id {tower_id} at {location}")
        if location == "center":
            spiral_coords = self.spiral_coords
        else:
            spiral_coords = self.spiral_coords[::-1]
        self.logger.debug(f"Waiting for {cost} money to place tower")
        current_money = ocr.read_current_money(self.screenshot())
        start = time.time()
        count = 0
        while current_money is None or current_money < cost:
            time.sleep(0.1)
            if time.time() - start > 60:
                self.logger.debug(f"Timed out placing tower: {tower_id}")
                return True
            if count % 10 == 0 and self.check_over():
                return False
            current_money = ocr.read_current_money(self.screenshot())
            count += 1

        if not self.check_placement():
            keyboard.send(hotkey)
        count = 0
        for x, y in spiral_coords:
            if count % 10 == 0 and self.check_over():
                return False
            if (x, y) not in self.placed_towers.values() and (x, y) not in self.invalid_towers:
                autoit.mouse_move(x, y)
                time.sleep(0.15)
                autoit.mouse_click("left", x, y)
                time.sleep(0.15)
                if not self.check_placement():
                    self.logger.debug(f"Placed tower at {x}, {y}")
                    self.placed_towers[tower_id] = (x, y)
                    return True
                self.invalid_towers.append((x, y))
            count += 1
        self.logger.warning("Could not place tower")
        return False

    def upgrade_tower(self, tower_id, skip=False):
        self.logger.debug(f"Upgrading tower with id {tower_id}")
        tower_coords = self.placed_towers.get(tower_id)
        if tower_coords is None:
            self.logger.warning(f"Failed to find tower with id: {tower_id}")
            return False
        autoit.mouse_click("left", tower_coords[0], tower_coords[1])
        time.sleep(0.1)
        start = time.time()
        count = 0
        while True:
            if time.time() - start > 60:
                return True
            if time.time() - start > 1 and skip:
                return True
            if count % 10 == 0 and self.check_over():
                return False
            screen = self.screenshot()
            upgrade_info = ocr.read_upgrade_cost(screen)
            if upgrade_info is not None:
                current_money = ocr.read_current_money(screen)
                if current_money is not None and current_money >= upgrade_info[0]:
                    autoit.mouse_click("left", upgrade_info[1], upgrade_info[2])
                    return True
            time.sleep(0.1)
            count += 1

    def check_over(self):
        if self.find_text("backtolobby") is not None:
            self.wave_checker.stop()
            return True

    def place_all_towers(self, hotkey, cap, cost):
        self.set_foreground()
        self.wave_checker = RepeatedTimer(1, self.check_wave)
        for i in range(cap):
            if self.check_over():
                return False

            current_money = ocr.read_current_money(self.screenshot())
            count = 0
            while current_money is None or current_money < cost:
                time.sleep(0.1)
                if count % 10 == 0 and self.check_over():
                    return False
                current_money = ocr.read_current_money(self.screenshot())
                count += 1

            if not self.check_placement():
                keyboard.send(hotkey)
            count = 0
            for x, y in self.spiral_coords:
                if count % 10 == 0 and self.check_over():
                    return False
                if (x, y) not in self.placed_towers.values() and (x, y) not in self.invalid_towers:
                    autoit.mouse_move(x, y)
                    time.sleep(0.15)
                    autoit.mouse_click("left", x, y)
                    time.sleep(0.15)
                    if not self.check_placement():
                        self.logger.debug(f"Placed tower at {x}, {y}")
                        self.placed_towers[(x, y)] = (x, y)
                        break
                    self.invalid_towers.append((x, y))
                count += 1
        return True

    def upgrade_all_towers(self, tower_cap):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while True:
            if time.time() - start > 300:
                self.anti_afk()
                start = time.time()

            if tower_cap == 0:
                if self.check_over():
                    return False
                time.sleep(0.5)

            for x, y in self.placed_towers:
                if self.check_over():
                    return False

                autoit.mouse_click("left", x, y)
                time.sleep(0.1)
                start2 = time.time()
                while time.time() - start2 < 0.5:
                    screen = self.screenshot()
                    upgrade_info = ocr.read_upgrade_cost(screen)
                    if upgrade_info is not None:
                        current_money = ocr.read_current_money(screen)
                        if current_money is not None and current_money >= upgrade_info[0]:
                            autoit.mouse_click("left", upgrade_info[1], upgrade_info[2])
                            self.logger.debug(f"Upgraded tower at {x}, {y}")
                            break
                    time.sleep(0.1)

    def check_wave(self):
        screen = self.screenshot()
        wave = ocr.read_current_wave(screen)
        if wave is not None and wave != self.current_wave[0]:
            self.current_wave[0] = wave
            self.logger.debug(f"Detected wave: {wave}")

    def anti_afk(self):
        for instance in self.roblox_instances:
            try:
                instance.set_foreground()
                time.sleep(1)
                for i in range(5):
                    instance.controller.jump()
            except StartupException:
                pass
            time.sleep(0.5)
        self.set_foreground()

    def find_text(self, text):
        return ocr.find_text(self.screenshot(), text)

    def leave_death(self):
        self.set_foreground()
        time.sleep(1)
        text_coords = self.find_text("backtolobby")
        if text_coords is None:
            self.leave_wave()
            return False
        autoit.mouse_click("left", text_coords[0], text_coords[1])
        return True

    def play_next(self):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while not self.click_text("playnext") and time.time() - start < 7:
            time.sleep(0.5)

    def play_again(self):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while not self.click_text("playagain") and time.time() - start < 7:
            time.sleep(0.5)

    def leave_wave(self):
        self.set_foreground()
        time.sleep(1)
        if self.username == config.usernames[0]:
            if len(self.invalid_towers) > 0:
                autoit.mouse_click("left", self.invalid_towers[0][0], self.invalid_towers[0][1])
            else:
                rect = self.get_window_rect()
                autoit.mouse_click("left", rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
            time.sleep(0.5)
        self.click_nav_rect(coords.settings_sequence, "Could not find settings button", restart=False)
        time.sleep(0.25)
        text = "leavegame"
        screen = self.screenshot()
        fast_travel_coords = ocr.find_fast_travel(screen, text)
        if fast_travel_coords is None:
            fast_travel_coords = ocr.find_fast_travel(screen, text, ratio=4)
            if fast_travel_coords is None:
                self.logger.warning(f"Could not find leavegame button")
                return False
        autoit.mouse_click("left", fast_travel_coords[0], fast_travel_coords[1])
        time.sleep(0.5)
        self.click_text("leave")