import os
import time
import cv2
import numpy as np
import logging
import autoit
import keyboard
import psutil
import pywinauto
import requests
import threading
import win32ui
import win32gui
import win32process
from abc import ABC, abstractmethod

from config_loader import load_config
config = load_config()
import coords
from utils.exceptions import *
from utils import ocr
from utils import memory
from utils import control
from utils.memory import get_pids
from utils.repeated_timer import RepeatedTimer


ROBLOX_EXE = "RobloxPlayerBeta.exe"
PLACE_ID = "17017769292"


class RobloxBase(ABC):
    last_screenshot = 0
    screenshot_lock = threading.Lock()

    def __init__(self, roblox_instances, controller: control.Control, username, world, level, custom_sequence, pid=None, y_addrs=None):
        self.roblox_instances = roblox_instances
        self.logger = logging.getLogger("ADFK")
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
        self.current_wave = [0, 0.0, 0]
        self.afk_time = 0.0
        self.wave_checker = None
        self.sell_flag = False
        self.over_flag = False
        self.over_lock = threading.Lock()
        self.speed_up_attempts = 0
        self.host = ""

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

        self.logger.debug(f"Sending request to http://localhost:{config.port}/LaunchAccount?Account={self.username}&PlaceId={PLACE_ID}&JobId={config.private_server_link}" + (f"&Password={config.password}" if config.password != "" else ""))
        try:
            result = requests.get(f"http://localhost:{config.port}/LaunchAccount", params=params)
        except requests.exceptions.ConnectionError:
            self.logger.critical("Could not connect to Roblox Account Manager. Make sure it is running and all settings are correct")
            os._exit(0)
            return
        if result.status_code != 200 or "Launched" not in result.text:
            if result.text == "":
                self.logger.critical("Make sure you are using my fork of Roblox Account Manager")
                self.logger.critical("The official one has a bug with the webserver causing it to not launch correctly")
                self.logger.critical("My fork can be found at https://github.com/Campionnn/Roblox-Account-Manager/releases/latest")
                input("Press enter to exit")
                os._exit(0)
            if result.text == "Invalid Password":
                self.logger.critical("Invalid webserver password in config")
                self.logger.critical("If you get this error and you did not set a password")
                self.logger.critical("Make sure you are using my fork of Roblox Account Manager")
                self.logger.critical("The official one has a bug with the webserver causing it to not launch correctly")
                self.logger.critical("My fork can be found at https://github.com/Campionnn/Roblox-Account-Manager/releases/latest")
                input("Press enter to exit")
                os._exit(0)
            raise StartupException(f"Invalid webserver response for {self.username}: {result.status_code} - {result.text}")

        self.logger.info(f"Waiting for Roblox instance for {self.username} to start")
        time.sleep(3)
        unique_pids = []
        start = time.time()
        while len(unique_pids) == 0:
            if time.time() - start > 120:
                raise StartupException(f"Timed out looking for Roblox instance for {self.username}")
            current_pids = [instance.pid for instance in self.roblox_instances.values()]
            unique_pids = [pid for pid in get_pids() if pid not in current_pids]
            time.sleep(1)
        if len(unique_pids) > 1:
            start2 = time.time()
            while len(unique_pids) > 1:
                if time.time() - start2 > 10:
                    raise PlayException(f"Too many Roblox instances found")
                current_pids = [instance.pid for instance in self.roblox_instances.values()]
                unique_pids = [pid for pid in get_pids() if pid not in current_pids]
                time.sleep(1)
        self.pid = unique_pids[0]
        self.logger.info(f"Roblox instance for {self.username} started. Waiting for window to appear")
        start = time.time()
        while time.time() - start < 60:
            self.check_crash()
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
        self.close_menu()
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
        time.sleep(0.5)
        self.logger.info(f"Searching for memory address for {self.username}")
        try:
            self.y_addrs = memory.search(self.pid)
        except MemoryException:
            self.y_addrs = None
        if self.y_addrs is None or self.y_addrs == 0:
            self.logger.warning(f"Could not find memory address for {self.username}")
            self.logger.warning(f"If this happens repeatedly, there was likely a Roblox update")
            raise StartupException("Could not find memory address")
        self.logger.info(f"Memory address found for {self.username}. {self.pid}: {self.y_addrs}")
        return

    def close_instance(self):
        self.logger.warning(f"Killing Roblox instance for {self.username}")
        try:
            os.kill(self.pid, 15)
            try:
                self.wave_checker.stop()
            except AttributeError:
                pass
        except OSError:
            pass
        self.logger.debug("Waiting for Roblox instance to close")
        while True:
            if self.pid not in get_pids():
                break
            time.sleep(1)
        time.sleep(5)
        return True

    def set_foreground(self):
        try:
            app = pywinauto.Application().connect(process=self.pid)
            app.top_window().set_focus()
            self.logger.debug(f"Switched foreground window to {self.pid} for {self.username}")
            return True
        except (pywinauto.application.ProcessNotFoundError, OSError, RuntimeError):
            raise StartupException(f"Could not set foreground window: {self.pid}")

    def get_window_rect(self):
        app = pywinauto.Application().connect(process=self.pid)
        client_rect = app.top_window().rectangle()
        return client_rect.left, client_rect.top, client_rect.width(), client_rect.height()
    
    def mouse_click(self, x, y):
        autoit.mouse_click("left", x, y, speed=2)
    
    def mouse_move(self, x, y):
        autoit.mouse_move(x, y, speed=2)

    def get_hwnd(self):
        def callback(hwnd, pids_):
            _, current_pid = win32process.GetWindowThreadProcessId(hwnd)
            if current_pid == self.pid:
                pids_.append(hwnd)
            return True

        pids = []
        win32gui.EnumWindows(callback, pids)
        return pids[0] if pids else None

    def background_screenshot(self):
        hwnd = self.get_hwnd()
        if hwnd is None:
            raise StartupException("Could not find hwnd")
        img = None
        dc_obj = None
        compatible_dc = None
        window_dc = None
        data_bit_map = None
        with RobloxBase.screenshot_lock:
            try:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                width = right - left
                height = bottom - top
                window_dc = win32gui.GetWindowDC(hwnd)
                dc_obj = win32ui.CreateDCFromHandle(window_dc)
                compatible_dc = dc_obj.CreateCompatibleDC()
                data_bit_map = win32ui.CreateBitmap()
                data_bit_map.CreateCompatibleBitmap(dc_obj, width, height)
                compatible_dc.SelectObject(data_bit_map)
                compatible_dc.BitBlt((0, 0), (width, height), dc_obj, (0, 0), 13369376)  # win32con.SRCCOPY
                bmp_str = data_bit_map.GetBitmapBits(True)
                img = np.frombuffer(bmp_str, dtype='uint8')
                img.shape = (height, width, 4)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            except Exception as e:
                raise StartupException(f"Could not take background screenshot: {e}")
            finally:
                try:
                    dc_obj.DeleteDC()
                    compatible_dc.DeleteDC()
                    win32gui.ReleaseDC(hwnd, window_dc)
                    win32gui.DeleteObject(data_bit_map.GetHandle())
                except:
                    pass
        return img

    def screenshot(self):
        screen = self.background_screenshot()
        if config.discord_webhook != "":
            current_time = time.time()
            if current_time - RobloxBase.last_screenshot >= 30:
                RobloxBase.last_screenshot = current_time
                threading.Thread(target=self.screenshot_webhook, args=(screen,)).start()
        return screen

    def screenshot_webhook(self, screen_np):
        try:
            _, compressed_image = cv2.imencode(".jpg", screen_np, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            compressed_image = compressed_image.tobytes()
            requests.post(config.discord_webhook, files={"file": ("image.jpg", compressed_image, "image/jpeg")})
        except (requests.exceptions.SSLError, requests.exceptions.RequestException):
            pass

    def wait_game_load(self, during):
        self.logger.debug(f"Waiting for game to load for {self.username}")
        start = time.time()
        while time.time() - start < 60:
            self.check_crash()
            screen = self.screenshot()
            match during:
                case "main":
                    if ocr.find_game_load(screen):
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

    def find_text(self, text):
        match text:
            case "start":
                return ocr.find_start(self.screenshot())
            case "x":
                return ocr.find_close_menu(self.screenshot())
            case "$":
                return ocr.find_sell(self.screenshot())
            case "search":
                return ocr.find_search(self.screenshot())
            case "typehere":
                return ocr.find_type_here(self.screenshot())
            case "openportal":
                return ocr.find_open_portal(self.screenshot())
            case "playagain":
                return ocr.find_play_again(self.screenshot())
            case "backtolobby":
                return ocr.find_back_to_lobby(self.screenshot())
            case "teleport":
                return ocr.find_teleport(self.screenshot())
            case "joinfriend":
                return ocr.find_join_friend(self.screenshot())
            case "panicleave":
                return ocr.find_panic_leave(self.screenshot())
            case "friendsonly":
                return ocr.find_friends_only(self.screenshot())
            case "items":
                return ocr.find_inventory(self.screenshot())
            case "units":
                return ocr.find_unit_manager(self.screenshot())
            case _:
                return ocr.find_text(self.screenshot(), text)

    def click_text(self, text, log=True):
        if log:
            self.logger.info(f"Clicking text \"{text}\" for {self.username}")
        text_coords = self.find_text(text)
        if text_coords is None:
            return False
        self.mouse_click(text_coords[0], text_coords[1])
        return True

    def click_nav_rect(self, sequence, error_message="", chapter=False):
        self.logger.info(f"Clicking button with sequence \"{sequence}\" for {self.username}")
        self.set_foreground()
        keyboard.send("\\")
        time.sleep(0.1)
        rect = self.find_nav_rect(sequence, chapter)
        self.set_foreground()
        keyboard.send("\\")
        if rect is None:
            if error_message != "":
                self.logger.warning(error_message)
            return None
        x = rect[0] + rect[2] // 2
        y = rect[1] + rect[3] // 2
        self.mouse_click(x, y)
        return rect

    def find_nav_rect(self, sequence, chapter=False):
        for key in list(sequence):
            time.sleep(0.1)
            keyboard.send(key)
        if sequence != "":
            time.sleep(0.2)
        screen = self.screenshot()
        gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        if chapter:
            crop = gray[:, screen.shape[1] // 3:]
        else:
            crop = gray[:int(screen.shape[0] * 0.9), :]
        _, thresh = cv2.threshold(crop, 254, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            epsilon = 0.001 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) in [4, 6, 8]:
                x, y, w, h = cv2.boundingRect(contour)
                bounding_box_area = w * h
                contour_area = cv2.contourArea(contour)
                if contour_area < bounding_box_area:
                    inner_crop = thresh[y:y + h, x:x + w]
                    inner_contours, _ = cv2.findContours(inner_crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    for inner_contour in inner_contours:
                        inner_bounding_box = cv2.boundingRect(inner_contour)
                        inner_bounding_box_area = inner_bounding_box[2] * inner_bounding_box[3]
                        if inner_bounding_box_area < bounding_box_area:
                            epsilon = 0.01 * cv2.arcLength(inner_contour, True)
                            inner_approx = cv2.approxPolyDP(inner_contour, epsilon, True)
                            if len(inner_approx) == 4:
                                if chapter:
                                    return x + screen.shape[1] // 3, y, w, h
                                return x, y, w, h
        return None

    def close_menu(self):
        self.logger.info(f"Closing menu for {self.username}")
        return self.click_text("x", log=False)

    def close_unit_manager(self):
        self.logger.info(f"Closing unit manager for {self.username}")
        return self.click_text("units", log=False)

    def check_placement(self, image=None):
        if image is None:
            image = self.screenshot()

        blue_channel = image[:, :, 0]
        green_channel = image[:, :, 1]
        red_channel = image[:, :, 2]
        mask = (blue_channel < self.place_color[0]) & (green_channel < self.place_color[1]) & (red_channel > self.place_color[2])

        total_pixels = image.shape[0] * image.shape[1]
        matching_pixels = np.sum(mask)
        matching_percentage = (matching_pixels / total_pixels) * 100

        return matching_percentage > self.place_color_tolerance

    def check_crash(self):
        if self.pid is None:
            raise StartupException("Roblox pid does not exist")
        if self.pid not in memory.get_pids():
            raise StartupException("Roblox instance crashed")

    def fast_travel(self, location):
        self.logger.info(f"Fast traveling to {location} for {self.username}")
        rect = self.click_nav_rect(coords.fast_travel_sequence)
        time.sleep(0.1)
        attempts = 0
        while rect is None or not self.check_fast_travel(self.screenshot()):
            if attempts > 2:
                return False
            self.check_crash()
            rect = self.click_nav_rect(coords.fast_travel_sequence)
            attempts += 1
            time.sleep(0.1)
        time.sleep(0.25)
        screen = self.screenshot()
        fast_travel_coords = None
        for i in range(2, 5):
            fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=i)
            if fast_travel_coords is None:
                fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=i, use_mask=True)
                if fast_travel_coords is not None:
                    break
            else:
                break
        if fast_travel_coords is None:
            self.controller.jump()
            time.sleep(0.5)
            self.controller.look_down(1.0)
            time.sleep(1)
            self.controller.reset_look()
            time.sleep(0.25)
            screen = self.screenshot()
            for i in range(2, 5):
                fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=i)
                if fast_travel_coords is None:
                    fast_travel_coords = ocr.find_fast_travel(screen, location, ratio=i, use_mask=True)
        if fast_travel_coords is None:
            self.logger.warning(f"Could not find fast travel location: {location}")
            return False
        self.mouse_click(fast_travel_coords[0], fast_travel_coords[1])
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

    def enter_realm(self, depth=0):
        pass

    def leave_realm(self):
        pass

    @abstractmethod
    def enter(self, depth=0):
        pass

    def start(self):
        self.set_foreground()
        return self.click_text("start")

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

    def check_afk(self):
        if time.time() - self.afk_time > 300:
            self.anti_afk()
            self.afk_time = time.time()

    def play(self, new_world=True, host=None):
        self.placed_towers = {}
        self.invalid_towers = []
        self.current_wave = [0, 0.0, 0]
        self.sell_flag = False
        self.over_flag = False
        self.speed_up_attempts = 0
        self.host = host or self.username
        self.set_foreground()
        self.wait_game_load("story")
        for username in config.usernames:
            self.roblox_instances[username].set_foreground()
            time.sleep(0.05)
        self.set_foreground()
        self.spiral()
        self.go_to_play()
        self.controller.turn_towards_yaw(self.pid, self.y_addrs, self.place_rot, self.place_rot_tolerance)
        self.controller.look_down(1.0)
        time.sleep(1)
        self.controller.reset_look()
        self.controller.zoom_out(1)
        if new_world:
            self.close_unit_manager()

    def go_to_play(self):
        self.cont_go_to_pos(self.place_pos[0], self.place_pos[1], self.place_pos_tolerance, jump=True, timeout=15)
        self.controller.reset()
        time.sleep(0.1)
        self.cont_go_to_pos(self.place_pos[0], self.place_pos[1], self.place_pos_tolerance/10, slow=True)
        self.controller.reset()

    def cont_go_to_pos(self, x, z, tolerance, jump=False, dash=False, slow=False, timeout=10):
        attempts = 0
        while True:
            if attempts > 2:
                raise PlayException("Failed to go to position")
            if not self.controller.go_to_pos(self.pid, self.y_addrs, x, z, tolerance, jump, dash, slow, timeout):
                self.controller.unstuck(self.pid, self.y_addrs)
                attempts += 1
            else:
                break

    def do_custom_sequence(self):
        self.set_foreground()
        self.wave_checker = RepeatedTimer(1, self.check_wave)
        self.afk_time = time.time()
        for action in self.custom_sequence.get('actions'):
            if self.sell_flag:
                self.logger.info("Selling all towers")
                for tower_id in list(self.placed_towers.keys()):
                    self.sell_tower(tower_id)
                self.sell_flag = False
                break
            if action.get('type') == 'place':
                for tower_id in action.get("ids"):
                    self.check_afk()
                    if not self.place_tower(tower_id, tower_id[0], action.get('location'), int(self.custom_sequence.get('costs').get(tower_id[0]))):
                        return False
            elif action.get('type') == 'upgrade':
                if int(action.get('amount')) == 0:
                    self.logger.info(f"Upgrading towers with id {action.get('ids')} continuously")
                    while True:
                        for tower_id in action.get("ids"):
                            if self.sell_flag:
                                break
                            self.check_afk()
                            if not self.upgrade_tower(tower_id, True):
                                return False
                            if self.check_placement():
                                keyboard.send("c")
                for _ in range(int(action.get('amount'))):
                    for tower_id in action.get("ids"):
                        self.check_afk()
                        if not self.upgrade_tower(tower_id):
                            return False
            elif action.get('type') == 'auto_use':
                for tower_id in action.get("ids"):
                    self.check_afk()
                    if not self.auto_use_tower(tower_id):
                        return False
            elif action.get('type') == 'wait_money':
                if not self.wait_money(int(action.get('amount'))):
                    return False
            elif action.get('type') == 'wait_time':
                if not self.wait_time(int(action.get('amount'))):
                    return False
            elif action.get('type') == 'wait_wave':
                if not self.wait_wave(int(action.get('amount'))):
                    return False
            elif action.get('type') == 'sell':
                for tower_id in action.get("ids"):
                    self.check_afk()
                    if not self.sell_tower(tower_id):
                        return False
            if self.check_placement():
                keyboard.send("c")
            time.sleep(0.2)
        while True:
            self.check_afk()
            if self.check_over():
                return False
            if self.sell_flag:
                self.logger.info("Selling all towers")
                for tower_id in list(self.placed_towers.keys()):
                    self.sell_tower(tower_id)
                self.sell_flag = False
                break
            time.sleep(0.5)
        while True:
            self.check_afk()
            if self.check_over():
                return False
            time.sleep(0.5)

    def place_tower(self, tower_id, hotkey, location, cost, depth=0):
        self.logger.info(f"Placing tower with id {tower_id} at {location}")
        if location == "center":
            spiral_coords = self.spiral_coords
        else:
            spiral_coords = self.spiral_coords[::-1]
        cost = cost * getattr(self, "cost_multiplier", 1)
        cost = int(cost) + (cost % 1 > 0)
        self.logger.debug(f"Waiting for {cost} money to place tower")
        current_money = ocr.read_current_money(self.screenshot())
        start = time.time()
        count = 0
        while current_money is None or current_money < cost:
            time.sleep(0.1)
            if self.sell_flag:
                return True
            self.check_afk()
            if time.time() - start > 60:
                self.logger.warning(f"Timed out waiting for money to placing tower: {tower_id}")
                return True
            if count % 5 == 0 and self.check_over():
                return False
            current_money = ocr.read_current_money(self.screenshot())
            count += 1

        if not self.check_placement():
            keyboard.send(hotkey)
        count = 0
        placed_towers = list(self.placed_towers.values())
        invalid_towers = []
        for x, y in spiral_coords:
            if self.sell_flag:
                return True
            if count != 0 and count % 3 == 0:
                if self.check_over():
                    return False
                current_money = ocr.read_current_money(self.screenshot())
                if current_money is not None and current_money < cost:
                    if depth > 2:
                        break
                    return self.place_tower(tower_id, hotkey, location, cost, depth + 1)
            if (x, y) not in placed_towers:
                if depth == 0 and (x, y) in self.invalid_towers:
                    continue
                self.mouse_move(x, y)
                time.sleep(0.15)
                self.mouse_click(x, y)
                time.sleep(0.15)
                if not self.check_placement():
                    self.logger.info(f"Placed tower {tower_id} at {x}, {y}")
                    self.placed_towers[tower_id] = (x, y)
                    self.invalid_towers.extend(invalid_towers)
                    keyboard.send("c")
                    return True
                invalid_towers.append((x, y))
                count += 1
        self.logger.warning("Could not place tower")
        keyboard.send("c")
        return False

    def upgrade_tower(self, tower_id, skip=False):
        if not skip:
            self.logger.info(f"Upgrading tower with id {tower_id}")
        tower_coords = self.placed_towers.get(tower_id)
        if tower_coords is None:
            self.logger.warning(f"Failed to find tower with id: {tower_id}")
            return False
        self.mouse_click(tower_coords[0], tower_coords[1])
        time.sleep(0.1)
        start = time.time()
        count = 0
        while True:
            if self.sell_flag:
                return True
            self.check_afk()
            if time.time() - start > 150:
                self.logger.warning(f"Timed out upgrading tower: {tower_id}")
                return True
            if skip and time.time() - start > 5:
                return True
            if count != 0 and count % 10 == 0 and self.check_over():
                return False
            screen = self.screenshot()
            upgrade_info = ocr.read_upgrade_cost(screen)
            if upgrade_info is not None:
                self.mouse_click(upgrade_info[1], upgrade_info[2])
                if not skip:
                    self.logger.info(f"Upgraded tower with id {tower_id}")
                return True
            else:
                if count != 0 and count % 10 == 0:
                    self.mouse_click(tower_coords[0], tower_coords[1])
            time.sleep(0.1)
            count += 1

    def auto_use_tower(self, tower_id):
        self.logger.info(f"Toggling auto use for tower with id {tower_id}")
        tower_coords = self.placed_towers.get(tower_id)
        if tower_coords is None:
            self.logger.warning(f"Failed to find tower with id: {tower_id}")
            return False
        self.mouse_click(tower_coords[0], tower_coords[1])
        time.sleep(0.1)
        start = time.time()
        count = 0
        while True:
            if time.time() - start > 3:
                self.logger.warning(f"Timed out toggling auto use for tower: {tower_id}")
                return True
            if self.click_text("autouse", log=False):
                self.logger.info(f"Toggled auto use for tower with id {tower_id}")
                return True
            else:
                if count % 3 == 0:
                    self.mouse_click(tower_coords[0], tower_coords[1])
            count += 1

    def wait_money(self, amount):
        amount = amount * getattr(self, "cost_multiplier", 1)
        amount = int(amount) + (amount % 1 > 0)
        self.logger.info(f"Waiting for {amount} money")
        count = 0
        while True:
            if self.sell_flag:
                return True
            self.check_afk()
            if count % 10 == 0 and self.check_over():
                return False
            current_money = ocr.read_current_money(self.screenshot())
            if current_money is not None and current_money >= amount:
                self.logger.info(f"Detected {current_money} money")
                return True
            time.sleep(0.1)
            count += 1

    def wait_time(self, seconds):
        self.logger.info(f"Waiting for {seconds} seconds")
        count = 0
        start = time.time()
        while time.time() - start < seconds:
            if self.sell_flag:
                return True
            self.check_afk()
            if count % 10 == 0 and self.check_over():
                return False
            time.sleep(0.1)
            count += 1
        self.logger.info(f"Finished waiting {seconds} seconds")
        return True

    def wait_wave(self, wave):
        self.logger.info(f"Waiting for wave {wave}")
        count = 0
        while True:
            if self.sell_flag:
                return True
            self.check_afk()
            if count % 10 == 0 and self.check_over():
                return False
            if self.current_wave[0] >= wave:
                self.logger.info(f"Finished waiting for wave {wave}")
                return True
            time.sleep(0.1)
            count += 1

    def sell_tower(self, tower_id):
        self.logger.info(f"Selling tower with id {tower_id}")
        tower_coords = self.placed_towers.get(tower_id)
        if tower_coords is None:
            self.logger.warning(f"Failed to find tower with id: {tower_id}")
            return False
        self.mouse_click(tower_coords[0], tower_coords[1])
        time.sleep(0.1)
        start = time.time()
        while True:
            if time.time() - start > 3:
                self.logger.warning(f"Timed out selling tower: {tower_id}")
                return True
            if self.click_text("$"):
                time.sleep(0.5)
                if self.click_text("sell"):
                    self.logger.info(f"Sold tower with id {tower_id}")
                    self.placed_towers.pop(tower_id)
                    return True

    def speed_up(self):
        speed = config.speed_main if self.host == config.usernames[0] else config.speed_default
        self.logger.info(f"Setting speed to {speed}x")
        host = self.roblox_instances.get(self.host)
        speed_rect = ocr.find_speed_up(host.screenshot(), speed)
        if self.host != self.username:
            host.set_foreground()
        if speed_rect is not None:
            self.mouse_click(speed_rect[0], speed_rect[1])
            self.speed_up_attempts += 10
        if self.host != self.username:
            self.set_foreground()

    def check_over(self):
        if not config.auto_max_speed and self.speed_up_attempts <= 50:
            if self.speed_up_attempts % 5 == 0:
                self.speed_up()
            self.speed_up_attempts += 1
        if self.over_flag:
            self.over_flag = False
            return True
        threading.Thread(target=self.check_over_thread).start()
        if self.current_wave[1] != 0 and time.time() - self.current_wave[1] > 300:
            self.logger.warning("Wave lasted for over 5 minutes and money hasn't changed. Manually leaving")
            return True

    def check_over_thread(self):
        with self.over_lock:
            if self.over_flag:
                return
            if self.find_text("backtolobby") is not None:
                self.over_flag = True

    def check_wave(self):
        screen = self.screenshot()
        wave = ocr.read_current_wave(screen)
        money = ocr.read_current_money(screen)
        if wave is not None and wave != self.current_wave[0]:
            self.current_wave[0] = wave
            self.current_wave[1] = time.time()
            self.logger.debug(f"Detected wave: {wave}")
        if money is not None and money != self.current_wave[2]:
            self.current_wave[2] = money
            self.current_wave[1] = time.time()

    def anti_afk(self):
        self.logger.info("Anti-AFKing")
        for username in config.usernames:
            instance = self.roblox_instances.get(username)
            try:
                instance.set_foreground()
                for i in range(5):
                    instance.controller.jump()
            except StartupException:
                pass
        self.set_foreground()

    def leave_wave(self):
        self.set_foreground()
        if self.username == config.usernames[0]:
            if len(self.invalid_towers) > 0:
                self.mouse_click(self.invalid_towers[0][0], self.invalid_towers[0][1])
            else:
                rect = self.get_window_rect()
                self.mouse_click(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
            time.sleep(0.5)
        self.click_nav_rect(coords.settings_sequence, "Could not find settings button")
        time.sleep(0.25)
        text = "leavegame"
        screen = self.screenshot()
        fast_travel_coords = ocr.find_fast_travel(screen, text)
        if fast_travel_coords is None:
            fast_travel_coords = ocr.find_fast_travel(screen, text, ratio=4)
            if fast_travel_coords is None:
                self.logger.warning(f"Could not find leavegame button")
                return False
        self.mouse_click(fast_travel_coords[0], fast_travel_coords[1])
        time.sleep(0.5)
        self.click_text("leave")
        return True
