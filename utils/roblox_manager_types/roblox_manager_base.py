import os
import time
import keyboard
import logging
import concurrent.futures
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

from utils.exceptions import *
from utils.control import Control
from utils.roblox_types.roblox_base import RobloxBase
from utils.roblox_types.roblox_infinite import RobloxInfinite
from utils.roblox_types.roblox_story import RobloxStory
from utils.roblox_types.roblox_tower import RobloxTower
from utils.roblox_types.roblox_portal import RobloxPortal
from utils.roblox_types.roblox_realm_infinite import RobloxRealmInfinite
from utils.memory import get_pids
from config_loader import load_config
config = load_config()


class RobloxManagerBase(ABC):
    def __init__(self, roblox_pids=None, world=1, level=None, custom_sequence=None):
        self.roblox_type = getattr(self, "roblox_type", RobloxBase)
        self.logger = logging.getLogger("ADFK")
        self.controller = Control()
        self.roblox_pids = roblox_pids
        self.world = world
        self.level = level
        self.custom_sequence = custom_sequence
        if self.custom_sequence is None:
            self.default_sequence()

        self.main_instance = None
        self.roblox_instances = {}

    def start(self):
        self.set_roblox_settings()
        self.init_instances()

        while True:
            if self.all_enter():
                break
            try:
                self.main_instance.wave_checker.stop()
            except AttributeError:
                pass

    def set_roblox_settings(self):
        self.logger.info("Changing Roblox settings")
        setting_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Roblox', 'GlobalBasicSettings_13.xml')
        tree = ET.parse(setting_path)
        root = tree.getroot()

        settings_changed = False

        for item in root.findall(".//Item[@class='UserGameSettings']"):
            properties = item.find("Properties")
            settings_to_change = {
                "CameraMode": "0",
                "CameraYInverted": "false",
                "ChatVisible": "false",
                "ComputerCameraMovementChanged": "true",
                "ComputerCameraMovementMode": "0",
                "ComputerMovementChanged": "true",
                "ComputerMovementMode": "0",
                "ControlMode": "0",
                "Fullscreen": "true",
                "GamepadCameraSensitivity": "0.200159997",
                "GraphicsOptimizationMode": "1",
                "GraphicsQualityLevel": "3",
                "MaxQualityEnabled": "false",
                "MouseSensitivity": "0.200159997",
                "SavedQualityLevel": "1",
                "StartMaximized": "true",
                "UiNavigationKeyBindEnabled": "true",
            }
            for key, new_value in settings_to_change.items():
                element = properties.find(f"./*[@name='{key}']")
                if element is not None:
                    current_value = element.text
                    if current_value != new_value:
                        element.text = new_value
                        settings_changed = True

        if settings_changed:
            try:
                tree.write(setting_path, encoding="utf-8", xml_declaration=True)
            except OSError:
                self.logger.warning("Failed to automatically change Roblox settings")
                self.logger.warning("Please change the settings manually according to https://github.com/Campionnn/ADFK?tab=readme-ov-file#roblox")
                self.logger.warning("After changing the settings, close Roblox to save settings")
                input("Press enter once finished")

    def init_instances(self):
        if self.roblox_pids is not None:
            self.logger.info("Initializing Roblox instances from given PIDs and Memory Addresses")
            for pid, y_addrs in self.roblox_pids.items():
                username = config.usernames[list(self.roblox_pids.keys()).index(pid)]
                instance = self.roblox_type(self.roblox_instances, self.controller, username, self.world, self.level, self.custom_sequence, pid, y_addrs)
                self.roblox_instances[username] = instance
            try:
                pids = {self.roblox_instances[username].pid: self.roblox_instances[username].y_addrs for username in config.usernames}
            except KeyError:
                self.logger.critical("Invalid Roblox PIDs for usernames")
                return
            self.logger.info(f"Roblox PIDs: {pids}")
            self.main_instance = self.roblox_instances[config.usernames[0]]
        else:
            if self.roblox_type in [RobloxInfinite, RobloxStory, RobloxPortal, RobloxRealmInfinite]:
                self.all_start_instance()
            elif self.roblox_type is RobloxTower:
                self.all_start_instance([config.usernames[0]])
            else:
                self.logger.critical("Invalid roblox type")
                raise StartupException("Invalid roblox type")

    def all_start_instance(self, usernames=None):
        self.roblox_instances = {}
        if usernames is None:
            usernames = config.usernames
        self.logger.info(f"Creating new Roblox instances for {usernames}")
        try:
            for username in usernames:
                self.start_instance(username)
        except PlayException:
            self.kill_all_roblox()
            self.all_start_instance()
        self.ensure_all_instance()

    def start_instance(self, username):
        self.logger.info(f"Creating instance for {username}")
        instance = self.roblox_type(self.roblox_instances, self.controller, username, self.world, self.level, self.custom_sequence)
        while True:
            try:
                instance.start_account()
                self.roblox_instances[username] = instance
                break
            except StartupException:
                self.logger.warning(f"Failed to start instance for {username}")
                try:
                    instance.close_instance()
                except TypeError:
                    self.logger.warning(f"Failed to close instance for {username}")
                    raise PlayException(f"Failed to close instance for {username}")

    def ensure_all_instance(self):
        self.logger.debug("Ensuring all Roblox instances are running")

        while True:
            if self.check_all_crash():
                time.sleep(10)
                if self.check_all_crash():
                    break
            time.sleep(1)

        pids = {self.roblox_instances[username].pid: self.roblox_instances[username].y_addrs for username in config.usernames}
        self.logger.info(f"Roblox PIDs: {pids}")
        self.main_instance = self.roblox_instances[config.usernames[0]]

        if not self.check_all_crash():
            self.ensure_all_instance()

    def check_all_crash(self):
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.check_crash()
            except StartupException:
                self.logger.warning(f"Instance for {instance.username} crashed")
                instance.close_instance()
                self.roblox_instances.pop(instance.username)
                username = instance.username
                del instance
                try:
                    self.start_instance(username)
                except PlayException:
                    self.kill_all_roblox()
                    self.all_start_instance()
                return False
        return True

    def kill_all_roblox(self):
        self.logger.warning("Killing all bad Roblox instances")
        pids = get_pids()
        count = 0
        while len(pids) > 0:
            if count > 5:
                break
            for pid in pids:
                if pid not in [instance.pid for instance in self.roblox_instances.values()]:
                    try:
                        os.kill(pid, 15)
                    except OSError:
                        pass
            count += 1
            time.sleep(1)
            pids = get_pids()
        time.sleep(5)

    def default_sequence(self):
        self.logger.debug("Creating default custom sequence using config")
        self.custom_sequence = {
            "name": "default sequence",
            "description": "auto generated sequence",
            "actions": [],
            "costs": {str(config.tower_hotkey): str(config.tower_cost)},
        }
        self.custom_sequence["actions"].append({
            "type": "place",
            "ids": [str(config.tower_hotkey) + chr(ord("a") + i) for i in range(config.tower_cap)],
            "location": "center",
        })
        self.custom_sequence["actions"].append({
            "type": "upgrade",
            "ids": [str(config.tower_hotkey) + chr(ord("a") + i) for i in range(config.tower_cap)],
            "amount": "0",
        })
        self.logger.debug(f"Default custom sequence: {self.custom_sequence}")

    @abstractmethod
    def all_enter(self):
        pass

    def all_leave(self):
        self.logger.info("Clicking leave for all accounts")
        try:
            self.all_click_text("leave", skip=True)
        except StartupException:
            pass

    def all_back_to_lobby(self, skip=False):
        self.logger.info("Going back to lobby for all accounts")
        failed = self.all_click_text("backtolobby", skip=skip)
        for username in failed:
            instance = self.roblox_instances[username]
            try:
                if not instance.leave_wave():
                    instance.close_instance()
            except StartupException:
                instance.close_instance()

    def all_play_again(self):
        self.logger.info("Clicking play again for all accounts")
        self.all_click_text("playagain")

    def all_play_next(self):
        self.logger.info("Clicking play next for all accounts")
        self.all_click_text("playnext")

    def all_close_menu(self):
        self.logger.info("Closing menu for all accounts")
        self.all_click_text("x")

    def all_click_text(self, text, skip=False, search=None):
        def find_text(username_):
            return username_, self.roblox_instances[username_].find_text(text)

        failed_users = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_username = {executor.submit(find_text, username): username for username in config.usernames}

            exception = None

            for future in concurrent.futures.as_completed(future_to_username):
                try:
                    username, coords = future.result()
                except StartupException:
                    if not skip:
                        exception = future.exception()
                    failed_users.append(username)
                    continue
                instance = self.roblox_instances[username]
                if coords is not None:
                    try:
                        instance.set_foreground()
                        instance.mouse_click(coords[0], coords[1])
                        if search is not None:
                            time.sleep(0.1)
                            instance.mouse_click(coords[0], coords[1])
                            time.sleep(0.2)
                            keyboard.write(search)
                        time.sleep(0.1)
                    except StartupException:
                        if not skip:
                            exception = future.exception()
                        failed_users.append(username)
                        continue
                else:
                    failed_users.append(username)

        if exception is not None:
            raise exception
        return failed_users
