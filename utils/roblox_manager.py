import os
import time
import logging
from typing import Type

from utils.exceptions import *
from utils.control import Control
from utils.roblox_types.roblox_base import RobloxBase
from utils.roblox_types.roblox_infinite import RobloxInfinite
from utils.roblox_types.roblox_story import RobloxStory
from utils.roblox_types.roblox_tower import RobloxTower
from utils.roblox_types.roblox_portal import RobloxPortal
from utils.roblox_types.roblox_realm_infinite import RobloxRealmInfinite
from utils.memory import get_pids_by_name
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManager:
    def __init__(self, roblox_type: Type[RobloxBase], roblox_pids=None, world=1, level=None, custom_sequence=None):
        self.roblox_type = roblox_type
        self.logger = logging.getLogger("ADFK")
        self.controller = Control()
        self.world = world
        self.level = level
        self.custom_sequence = custom_sequence
        if self.custom_sequence is None:
            self.default_sequence()

        self.place_id = "17017769292"
        self.roblox_exe = "RobloxPlayerBeta.exe"

        self.main_instance = None
        self.roblox_instances = {}
        if roblox_pids is not None:
            self.logger.info("Initializing Roblox instances from given PIDs and Memory Addresses")
            for pid, y_addrs in roblox_pids.items():
                username = config.usernames[list(roblox_pids.keys()).index(pid)]
                instance = roblox_type(self.roblox_instances, self.controller, username, self.world, self.level, self.custom_sequence, pid, y_addrs)
                self.roblox_instances[username] = instance
            try:
                pids = {self.roblox_instances[username].pid: self.roblox_instances[username].y_addrs for username in config.usernames}
            except KeyError:
                self.logger.error("Invalid Roblox PIDs for usernames")
                return
            self.logger.info(f"Roblox PIDs: {pids}")
            self.main_instance = self.roblox_instances[config.usernames[0]]
        else:
            if issubclass(roblox_type, (RobloxInfinite, RobloxStory, RobloxPortal, RobloxRealmInfinite)):
                self.all_start_instance()
            elif issubclass(roblox_type, RobloxTower):
                self.all_start_instance([config.usernames[0]])
            else:
                self.logger.error("Invalid roblox type")
                raise StartupException("Invalid roblox type")

    def start(self):
        while True:
            if self.all_enter():
                break
            try:
                self.main_instance.wave_checker.stop()
            except AttributeError:
                pass

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
                time.sleep(5)
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
        pids = get_pids_by_name(self.roblox_exe)
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
            pids = get_pids_by_name(self.roblox_exe)
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

    def all_enter(self):
        if type(self.main_instance) is RobloxInfinite:
            return self.all_enter_infinite()
        elif type(self.main_instance) is RobloxStory:
            return self.all_enter_story()
        elif type(self.main_instance) is RobloxTower:
            return self.enter_tower()
        elif type(self.main_instance) is RobloxPortal:
            return self.all_enter_portal()
        elif type(self.main_instance) is RobloxRealmInfinite:
            return self.all_enter_realm_infinite()
        else:
            raise StartupException("Invalid roblox type")

    def all_enter_infinite(self):
        assert type(self.main_instance) is RobloxInfinite
        self.logger.info(f"Entering infinite for all accounts. World: {self.world}")
        self.logger.info("Teleporting to play position")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.teleport()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                return
        self.logger.info("Entering story select area")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.enter()
            except (StartupException, MemoryException):
                instance.close_instance()
                self.ensure_all_instance()
                self.all_click_leave()
                return
        self.logger.info(f"Starting story")
        self.main_instance.start()
        time.sleep(2)
        self.logger.info("Going to play position")
        try:
            self.main_instance.play()
        except (PlayException, StartupException):
            self.all_leave_death()
            return
        self.logger.info("Performing custom sequence")
        try:
            if not self.main_instance.do_custom_sequence():
                self.logger.info("Leaving infinite")
                self.all_leave_death()
                return
        except (PlayException, StartupException, MemoryException):
            self.all_leave_death()
            self.ensure_all_instance()
            return self.all_enter_infinite()

    def all_enter_story(self):
        assert type(self.main_instance) is RobloxStory
        self.main_instance: RobloxStory  # type hint to suppress warnings
        while self.world <= 9:
            self.main_instance.set_world(self.world, self.level)
            self.logger.info(f"Entering story for all accounts. World: {self.world} Level: {self.level}")
            self.logger.info("Teleporting to play position")
            for username in config.usernames:
                instance = self.roblox_instances[username]
                try:
                    instance.teleport()
                except StartupException:
                    instance.close_instance()
                    self.ensure_all_instance()
                    return
            self.logger.info("Entering story select area")
            for username in config.usernames:
                instance = self.roblox_instances[username]
                try:
                    instance.enter()
                except (StartupException, MemoryException):
                    instance.close_instance()
                    self.ensure_all_instance()
                    self.all_click_leave()
                    return
            self.logger.debug(f"Starting story")
            self.main_instance.start()
            time.sleep(2)
            while True:
                self.logger.info("Going to play position")
                try:
                    self.main_instance.play()
                except (PlayException, StartupException):
                    self.all_leave_death()
                    return
                self.logger.info("Performing custom sequence")
                try:
                    if not self.main_instance.do_custom_sequence():
                        time.sleep(0.5)
                        if self.main_instance.find_text("victory") is not None:
                            self.logger.debug("Detected victory screen")
                            if self.main_instance.find_text("playnext"):
                                self.logger.debug("Clicking play next")
                                self.all_play_next()
                                self.level += 1
                                continue
                            else:
                                self.logger.debug("Finished world. Going back to lobby")
                                self.all_leave_death()
                                self.world += 1
                                self.level = 1
                                break
                        elif self.main_instance.find_text("defeat") is not None:
                            self.logger.warning("Detected defeat screen. Trying again")
                            self.all_play_again()
                            continue
                        else:
                            self.all_leave_death()
                            break
                except (PlayException, StartupException, MemoryException):
                    self.all_leave_death()
                    self.ensure_all_instance()
                    break
        return True

    def enter_tower(self):
        assert type(self.main_instance) is RobloxTower
        self.logger.info(f"Entering Tower of Eternity for main account")
        self.logger.info("Teleporting to tower enter position")
        try:
            self.main_instance.teleport()
        except StartupException:
            self.main_instance.close_instance()
            self.ensure_all_instance()
            return
        self.logger.info(f"Starting tower")
        self.main_instance.start()
        time.sleep(2)
        while True:
            self.logger.info("Going to play position")
            try:
                self.main_instance.play()
            except (PlayException, StartupException):
                self.all_leave_death()
                return
            self.logger.info("Performing custom sequence")
            try:
                if not self.main_instance.do_custom_sequence():
                    if self.main_instance.find_text("victory") is not None:
                        self.logger.debug("Detected victory screen")
                        if self.main_instance.find_text("playnext"):
                            self.logger.debug("Clicking play next")
                            self.all_play_next()
                            continue
                        else:
                            self.logger.debug("Won but couldn't find play next button")
                            self.all_leave_death()
                            break
                    else:
                        self.all_leave_death()
                        break
            except (PlayException, StartupException, MemoryException):
                self.all_leave_death()
                self.ensure_all_instance()
                return self.enter_tower()

    def all_enter_portal(self):
        assert type(self.main_instance) is RobloxPortal
        self.logger.info(f"Entering portal for all accounts")
        self.logger.info("Going to portal open position")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.teleport()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                return
        self.logger.info("Entering portal")
        try:
            host = self.main_instance.enter()
        except (StartupException, MemoryException):
            self.main_instance.close_instance()
            self.ensure_all_instance()
            self.all_click_leave()
            return
        for username in config.usernames[1:]:
            instance = self.roblox_instances[username]
            if instance.username != host:
                try:
                    instance.enter()
                except (StartupException, MemoryException):
                    instance.close_instance()
                    self.ensure_all_instance()
                    self.all_click_leave()
                    return
        self.logger.info(f"Starting portal")
        try:
            if not self.roblox_instances.get(host).start():
                self.logger.warning("Failed to start portal. Retrying")
                self.all_click_leave()
                self.ensure_all_instance()
                return
        except StartupException:
            self.roblox_instances.get(host).close_instance()
            self.ensure_all_instance()
            return
        time.sleep(2)
        self.logger.info("Going to play position")
        try:
            self.main_instance.play(host)
        except (PlayException, StartupException):
            self.all_leave_death()
            return
        self.logger.info("Performing custom sequence")
        try:
            if not self.main_instance.do_custom_sequence():
                self.all_leave_death()
                return
        except (PlayException, StartupException, MemoryException):
            self.all_leave_death()
            self.ensure_all_instance()
            return self.all_enter_portal()

    def all_enter_realm_infinite(self):
        assert type(self.main_instance) is RobloxRealmInfinite
        self.logger.info(f"Entering realm for all accounts")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.enter_realm()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                return
        self.logger.info("Going to realm infinite position")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.teleport()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                return
        self.logger.info("Entering realm infinite select area")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.enter()
            except (StartupException, MemoryException):
                instance.close_instance()
                self.ensure_all_instance()
                self.all_click_leave()
                return
        self.logger.info(f"Starting realm infinite")
        self.main_instance.start()
        time.sleep(2)
        while True:
            self.logger.info("Going to play position")
            try:
                self.main_instance.play()
            except (PlayException, StartupException):
                self.all_leave_death()
                return
            self.logger.info("Performing custom sequence")
            try:
                if not self.main_instance.do_custom_sequence():
                    self.logger.info("Playing again")
                    self.all_play_again()
            except (PlayException, StartupException, MemoryException):
                self.all_leave_death()
                self.ensure_all_instance()
                return self.all_enter_infinite()
            self.main_instance.wave_checker.stop()

    def all_click_leave(self):
        self.logger.info("Clicking leave for all accounts")
        for username in config.usernames:
            instance = self.roblox_instances[username]
            try:
                instance.set_foreground()
                time.sleep(0.5)
                instance.click_text("leave")
                time.sleep(0.5)
            except StartupException:
                pass

    def all_leave_death(self):
        self.logger.info("Leaving for all accounts")
        for username in config.usernames:
            if not self.roblox_instances[username].leave_death():
                self.roblox_instances[username].close_instance()
        self.ensure_all_instance()

    def all_play_next(self):
        self.logger.info("Clicking play next for all accounts")
        for username in config.usernames:
            self.roblox_instances[username].play_next()

    def all_play_again(self):
        self.logger.info("Clicking play again for all accounts")
        for username in config.usernames:
            self.roblox_instances[username].play_again()
