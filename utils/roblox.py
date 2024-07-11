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

import config
if config.port == 0000:
    import config_personal as config
import coords
from utils.exceptions import *
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

        self.mode = None
        self.level = None
        self.world_sequence = None
        self.story_place_pos = None
        self.story_place_pos_tolerance = None
        self.story_place_rot = None
        self.story_place_rot_tolerance = None

        self.placed_towers = []
        self.invalid_towers = []
        self.current_wave = [0]
        self.wave_checker = None

    def set_mode(self, mode, world, level):
        self.mode = mode
        self.level = level
        if world == 1:
            self.world_sequence = coords.windmill_sequence
            self.story_place_pos = coords.windmill_place_pos
            self.story_place_pos_tolerance = coords.windmill_place_pos_tolerance
            self.story_place_rot = coords.windmill_place_rot
            self.story_place_rot_tolerance = coords.windmill_place_rot_tolerance
        elif world == 2:
            self.world_sequence = coords.haunted_sequence
            self.story_place_pos = coords.haunted_place_pos
            self.story_place_pos_tolerance = coords.haunted_place_pos_tolerance
            self.story_place_rot = coords.haunted_place_rot
            self.story_place_rot_tolerance = coords.haunted_place_rot_tolerance
        elif world == 3:
            self.world_sequence = coords.cursed_sequence
            self.story_place_pos = coords.cursed_place_pos
            self.story_place_pos_tolerance = coords.cursed_place_pos_tolerance
            self.story_place_rot = coords.cursed_place_rot
            self.story_place_rot_tolerance = coords.cursed_place_rot_tolerance
        elif world == 4:
            self.world_sequence = coords.blue_sequence
            self.story_place_pos = coords.blue_place_pos
            self.story_place_pos_tolerance = coords.blue_place_pos_tolerance
            self.story_place_rot = coords.blue_place_rot
            self.story_place_rot_tolerance = coords.blue_place_rot_tolerance
        elif world == 5:
            self.world_sequence = coords.underwater_sequence
            self.story_place_pos = coords.underwater_place_pos
            self.story_place_pos_tolerance = coords.underwater_place_pos_tolerance
            self.story_place_rot = coords.underwater_place_rot
            self.story_place_rot_tolerance = coords.underwater_place_rot_tolerance
        elif world == 6:
            self.world_sequence = coords.swordsman_sequence
            self.story_place_pos = coords.swordsman_place_pos
            self.story_place_pos_tolerance = coords.swordsman_place_pos_tolerance
            self.story_place_rot = coords.swordsman_place_rot
            self.story_place_rot_tolerance = coords.swordsman_place_rot_tolerance
        elif world == 7:
            self.world_sequence = coords.snowy_sequence
            self.story_place_pos = coords.snowy_place_pos
            self.story_place_pos_tolerance = coords.snowy_place_pos_tolerance
            self.story_place_rot = coords.snowy_place_rot
            self.story_place_rot_tolerance = coords.snowy_place_rot_tolerance
        elif world == 8:
            self.world_sequence = coords.crystal_sequence
            self.story_place_pos = coords.crystal_place_pos
            self.story_place_pos_tolerance = coords.crystal_place_pos_tolerance
            self.story_place_rot = coords.crystal_place_rot
            self.story_place_rot_tolerance = coords.crystal_place_rot_tolerance

    def start_account(self):
        self.pid = None
        self.y_addrs = None

        params = {
            "Account": self.username,
            "PlaceId": self.place_id,
            "JobId": config.private_server_link,
        }
        if config.password != "":
            params["Password"] = config.password
        result = requests.get(f"http://localhost:{config.port}/LaunchAccount", params=params)
        if result.status_code != 200:
            raise StartupException(f"Failed to launch Roblox instance for {self.username}")

        self.logger.debug(f"Waiting for Roblox instance for {self.username} to start")
        unique_pids = []
        while len(unique_pids) == 0:
            pids = get_pids_by_name(self.roblox_exe)
            current_pids = [instance.pid for instance in self.roblox_instances]
            unique_pids = [pid for pid in pids if pid not in current_pids]
            time.sleep(1)
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
            raise StartupException("Could not set foreground window")
        time.sleep(3)

        if not self.wait_game_load("main"):
            return
        time.sleep(0.5)
        self.click_text("x")
        if not self.fast_travel("leaderboards"):
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
        return

    def close_instance(self):
        self.logger.debug(f"Killing Roblox instance for {self.username}")
        try:
            os.kill(self.pid, 15)
        except OSError:
            pass
        while True:
            self.logger.debug("Waiting for Roblox instance to close")
            if self.pid not in get_pids_by_name(self.roblox_exe):
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
        except pywinauto.application.ProcessNotFoundError or OSError or RuntimeError:
            raise StartupException("Could not set foreground window")

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
        while time.time() - start < 45:
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
            time.sleep(0.05)
            keyboard.send(key)
        time.sleep(0.5)
        screen = pyautogui.screenshot()
        screen_np = np.array(screen)

        screen_crop = screen_np
        if chapter:
            screen_crop = screen_np[:, screen_np.shape[1] // 3:]

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
        mask = (red_channel > 160) & (green_channel < 20) & (blue_channel < 20)

        total_pixels = image_np.shape[0] * image_np.shape[1]
        matching_pixels = np.sum(mask)
        matching_percentage = (matching_pixels / total_pixels) * 100

        return matching_percentage > 10

    def check_crash(self, responsive=True):
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

    def teleport_story(self):
        self.set_foreground()
        time.sleep(0.5)
        self.click_text("x")
        try:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            attempts = 0
            while self.controller.calculate_distance(pos[0], pos[2], coords.story_play_pos[0], coords.story_play_pos[1]) > 50 and attempts < 5:
                time.sleep(0.25)
                if not self.fast_travel("story"):
                    self.controller.look_down(1.0)
                    time.sleep(1)
                    self.controller.reset_look()
                    if not self.fast_travel("story"):
                        raise StartupException("Could not fast travel to story")
                time.sleep(0.25)
                if self.click_text("leave"):
                    time.sleep(0.1)
                    pos = memory.get_current_pos(self.pid, self.y_addrs)
                    continue
                time.sleep(0.25)
                pos = memory.get_current_pos(self.pid, self.y_addrs)
                attempts += 1
            if attempts >= 5:
                raise StartupException("Could not teleport to story")
            time.sleep(0.25)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1], coords.story_play_pos_tolerance, 10, precise=True):
                return self.teleport_story()
            return True
        except MemoryException:
            raise StartupException("Could not teleport to story")

    def enter_story(self):
        self.logger.debug(f"Entering story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance, 20):
            self.teleport_story()
            return self.enter_story()
        if self.username == config.usernames[0]:
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            self.click_nav_rect(self.world_sequence, "Could not find world button")
            time.sleep(0.5)
            if self.mode == 1:
                self.click_text("infinitemode")
            elif self.mode == 2:
                self.click_nav_rect("d"*10 + "a"*4 + "s" * (self.level-1) * 2, "Could not find selected chapter", restart=False, chapter=True)
            time.sleep(0.5)
            self.click_text("confirm")
        return True

    def start_story(self):
        self.set_foreground()
        time.sleep(0.5)
        self.click_text("start")

    def play_story(self):
        self.placed_towers = []
        self.invalid_towers = []
        self.current_wave = [0]
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load("story")
        attempts = 0
        while attempts < 5:
            if not self.controller.go_to_pos(self.pid, self.y_addrs, self.story_place_pos[0], self.story_place_pos[1], self.story_place_pos_tolerance, 10, True):
                self.controller.unstuck(self.pid, self.y_addrs)
                attempts += 1
            else:
                break
        if attempts >= 5:
            raise PlayException("Could not go to place position")
        self.controller.reset()
        time.sleep(0.1)
        attempts = 0
        while attempts < 5:
            if not self.controller.go_to_pos(self.pid, self.y_addrs, self.story_place_pos[0], self.story_place_pos[1], self.story_place_pos_tolerance/10, 10, min_speed=0.2, max_speed=0.3, min_turn=0.5, precise=True):
                self.controller.unstuck(self.pid, self.y_addrs)
                attempts += 1
            else:
                break
        if attempts >= 5:
            raise PlayException("Could not go to place position")
        self.controller.reset()
        self.controller.turn_towards_yaw(self.pid, self.y_addrs, self.story_place_rot, self.story_place_rot_tolerance, 0.2)
        self.controller.look_down(1.0)
        time.sleep(1)
        self.controller.reset_look()
        self.controller.zoom_out()

    def place_towers(self, tower_key, tower_cap, tower_cost, wave_stop):
        self.set_foreground()
        self.wave_checker = RepeatedTimer(1, self.check_wave)
        for i in range(tower_cap):
            if self.find_text("backtolobby") is not None:
                self.wave_checker.stop()
                return False
            if self.mode == 1 and self.current_wave[0] >= wave_stop:
                self.wave_checker.stop()
                time.sleep(3)
                return False

            current_money = 0
            while current_money is None or current_money < tower_cost:
                screen = self.screenshot()
                current_money = ocr.read_current_money(screen)
                time.sleep(0.1)

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
                if self.find_text("backtolobby") is not None:
                    self.wave_checker.stop()
                    return False
                if self.mode == 1 and self.current_wave[0] >= wave_stop:
                    self.wave_checker.stop()
                    time.sleep(3)
                    return False

                if not self.check_placement():
                    keyboard.send(tower_key)
                if (x, y) not in self.placed_towers and (x, y) not in self.invalid_towers:
                    autoit.mouse_move(x + rect[0], y + rect[1])
                    time.sleep(0.1)
                    autoit.mouse_click("left", x + rect[0], y + rect[1])
                    time.sleep(0.15)
                    if not self.check_placement():
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

    def upgrade_towers(self, wave_stop, tower_cap):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while True:
            if time.time() - start > 300:
                self.anti_afk()
                start = time.time()

            if tower_cap == 0:
                if self.find_text("backtolobby") is not None:
                    self.wave_checker.stop()
                    return False
                time.sleep(0.5)

            for x, y in self.placed_towers:
                if self.find_text("backtolobby") is not None:
                    self.wave_checker.stop()
                    return False
                if self.mode == 1 and self.current_wave[0] >= wave_stop:
                    self.wave_checker.stop()
                    time.sleep(3)
                    return False

                autoit.mouse_click("left", x, y)
                time.sleep(0.1)
                screen = self.screenshot()
                upgrade_info = ocr.read_upgrade_cost(screen)
                start2 = time.time()
                while time.time() - start2 < 0.5:
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
            self.logger.debug(f"Detected wave: {wave}")

    def anti_afk(self):
        for instance in self.roblox_instances:
            instance.set_foreground()
            time.sleep(1)
            for i in range(5):
                instance.controller.jump()
            time.sleep(0.5)
        self.set_foreground()

    def find_text(self, text):
        return ocr.find_text(self.screenshot(), text)

    def leave_story_death(self):
        self.set_foreground()
        time.sleep(1)
        text_coords = self.find_text("backtolobby")
        if text_coords is None:
            self.leave_story_wave()
        autoit.mouse_click("left", text_coords[0], text_coords[1])

    def play_next(self):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while not self.click_text("playnext") and time.time() - start < 5:
            time.sleep(0.5)

    def play_again(self):
        self.set_foreground()
        time.sleep(1)
        start = time.time()
        while not self.click_text("playagain") and time.time() - start < 5:
            time.sleep(0.5)

    def leave_story_wave(self):
        self.set_foreground()
        time.sleep(1)
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

    def close_announcement(self):
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load("main")
        time.sleep(0.5)
        self.click_text("x")
