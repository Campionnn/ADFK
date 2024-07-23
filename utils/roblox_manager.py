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
from utils.memory import get_pids_by_name
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManager:
    def __init__(self, roblox_type: Type[RobloxBase], logger: logging.Logger, roblox_pids=None, mode=1, world=1, level=None, custom_sequence=None):
        self.roblox_type = roblox_type
        self.logger = logger
        self.controller = Control(self.logger)
        self.mode = mode
        self.world = world
        self.level = level
        self.custom_sequence = custom_sequence

        self.place_id = "17017769292"
        self.roblox_exe = "RobloxPlayerBeta.exe"

        self.main_instance = None
        self.roblox_instances = []
        if roblox_pids is not None:
            for pid, y_addrs in roblox_pids.items():
                username = config.usernames[list(roblox_pids.keys()).index(pid)]
                instance = roblox_type(self.roblox_instances, self.logger, self.controller, username, self.world, self.level, self.custom_sequence, pid, y_addrs)
                self.roblox_instances.append(instance)
            pids = {instance.pid: instance.y_addrs for instance in self.roblox_instances}
            self.logger.info(f"Roblox PIDs: {pids}")
            self.main_instance = [instance for instance in self.roblox_instances if instance.username == config.usernames[0]][0]
        else:
            if issubclass(roblox_type, (RobloxInfinite, RobloxStory, RobloxPortal)):
                self.all_start_instance()
            elif issubclass(roblox_type, RobloxTower):
                self.all_start_instance([config.usernames[0]])
            else:
                raise StartupException("Invalid roblox type")

        while True:
            if self.all_enter():
                break

    def all_start_instance(self, usernames=None):
        if usernames is None:
            usernames = config.usernames
        try:
            for username in usernames:
                self.start_instance(username)
        except PlayException:
            self.logger.warning(f"Closing all Roblox instances and retrying")
            for pid in get_pids_by_name(self.roblox_exe):
                try:
                    os.kill(pid, 15)
                except OSError:
                    pass
            self.all_start_instance()
        time.sleep(5)
        self.ensure_all_instance()

    def start_instance(self, username):
        self.logger.debug(f"Creating instance for {username}")
        instance = self.roblox_type(self.roblox_instances, self.logger, self.controller, username, self.world, self.level, self.custom_sequence)
        while True:
            try:
                instance.start_account()
                self.roblox_instances.append(instance)
                break
            except StartupException:
                self.logger.warning(f"Failed to start {username} instance")
                instance.close_instance()
                time.sleep(3)
            self.roblox_instances.append(instance)

    def ensure_all_instance(self):
        while True:
            if self.check_all_crash():
                break
            time.sleep(5)

        roblox_instances = []
        for username in config.usernames:
            for instance in self.roblox_instances:
                if instance.username == username:
                    roblox_instances.append(instance)
                    break
        self.roblox_instances = roblox_instances

        pids = {instance.pid: instance.y_addrs for instance in self.roblox_instances}
        self.logger.info(f"Roblox PIDs: {pids}")
        self.main_instance = [instance for instance in self.roblox_instances if instance.username == config.usernames[0]][0]
        time.sleep(5)

        if not self.check_all_crash():
            self.ensure_all_instance()

    def check_all_crash(self):
        for instance in self.roblox_instances:
            try:
                instance.check_crash()
            except StartupException:
                self.logger.warning(f"Instance for {instance.username} crashed")
                instance.close_instance()
                self.roblox_instances.remove(instance)
                username = instance.username
                del instance
                try:
                    self.start_instance(username)
                except PlayException:
                    self.logger.warning(f"Closing all Roblox instances and retrying")
                    for pid in get_pids_by_name(self.roblox_exe):
                        try:
                            os.kill(pid, 15)
                        except OSError:
                            pass
                    self.all_start_instance()
                return False
        return True

    def all_enter(self):
        if isinstance(self.main_instance, RobloxInfinite):
            return self.all_enter_infinite()
        elif isinstance(self.main_instance, RobloxStory):
            return self.all_enter_story()
        elif isinstance(self.main_instance, RobloxTower):
            return self.enter_tower()
        elif isinstance(self.main_instance, RobloxPortal):
            return self.all_enter_portal()
        else:
            raise StartupException("Invalid roblox type")

    def all_enter_infinite(self):
        assert isinstance(self.main_instance, RobloxInfinite)
        self.logger.debug(f"Entering infinite for all accounts. World: {self.world} Level: {self.level}")
        for instance in self.roblox_instances:
            try:
                instance.teleport()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                return
        for instance in self.roblox_instances:
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
        try:
            self.main_instance.play()
        except (PlayException, StartupException):
            self.all_leave_story_wave()
            return
        if self.main_instance.custom_sequence is not None:
            if not self.main_instance.do_custom_sequence():
                if self.main_instance.current_wave[0] >= config.wave_stop:
                    self.all_leave_story_wave()
                    return
                else:
                    self.all_leave_story_death()
                    return
        else:
            if not self.main_instance.place_all_towers(config.tower_hotkey, config.tower_cap, config.tower_cost):
                if self.main_instance.current_wave[0] >= config.wave_stop:
                    self.all_leave_story_wave()
                    return
                else:
                    self.all_leave_story_death()
                    return
            self.logger.debug(f"Finished placing towers")
            self.logger.debug(f"Upgrading towers")
            if not self.main_instance.upgrade_all_towers(config.tower_cap):
                if self.main_instance.current_wave[0] >= config.wave_stop:
                    self.all_leave_story_wave()
                    return
                else:
                    self.all_leave_story_death()
                    return

    def all_enter_story(self):
        assert isinstance(self.main_instance, RobloxStory)
        for world in range(self.world, 9):
            self.world = world
            self.main_instance.set_world(self.world, self.level)
            self.logger.debug(f"Entering story for all accounts. World: {self.world} Level: {self.level}")
            self.level = 1
            for instance in self.roblox_instances:
                try:
                    instance.teleport()
                except StartupException:
                    instance.close_instance()
                    self.ensure_all_instance()
                    self.all_enter_story()
            for instance in self.roblox_instances:
                try:
                    instance.enter()
                except (StartupException, MemoryException):
                    instance.close_instance()
                    self.ensure_all_instance()
                    self.all_click_leave()
                    self.all_enter_story()
            self.logger.debug(f"Starting story")
            self.main_instance.start()
            time.sleep(2)
            while True:
                try:
                    self.main_instance.play()
                except (PlayException, StartupException):
                    self.all_leave_story_wave()
                    self.all_enter_story()

                if self.main_instance.custom_sequence is not None:
                    if not self.main_instance.do_custom_sequence():
                        time.sleep(0.5)
                        if self.main_instance.find_text("victory") is not None:
                            if self.main_instance.find_text("playnext"):
                                self.all_play_next()
                                continue
                            else:
                                self.all_leave_story_death()
                                break
                        elif self.main_instance.find_text("defeat") is not None:
                            self.all_play_again()
                            continue
                else:
                    if not self.main_instance.place_all_towers(config.tower_hotkey, config.tower_cap, config.tower_cost):
                        time.sleep(0.5)
                        if self.main_instance.find_text("victory") is not None:
                            if self.main_instance.find_text("playnext"):
                                self.all_play_next()
                                continue
                            else:
                                self.all_leave_story_death()
                                break
                        elif self.main_instance.find_text("defeat") is not None:
                            self.all_play_again()
                            continue
                    self.logger.debug(f"Finished placing towers")
                    self.logger.debug(f"Upgrading towers")
                    if not self.main_instance.upgrade_all_towers(config.tower_cap):
                        time.sleep(0.5)
                        if self.main_instance.find_text("victory") is not None:
                            if self.main_instance.find_text("playnext"):
                                self.all_play_next()
                                continue
                            else:
                                self.all_leave_story_death()
                                break
                        elif self.main_instance.find_text("defeat") is not None:
                            self.all_play_again()
                            continue
        return True

    def enter_tower(self):
        assert isinstance(self.main_instance, RobloxTower)
        self.logger.debug(f"Entering Tower of Eternity for main account")
        try:
            self.main_instance.teleport()
        except StartupException:
            self.main_instance.close_instance()
            self.ensure_all_instance()
            self.enter_tower()
        self.logger.debug(f"Starting tower")
        self.main_instance.start()
        time.sleep(2)
        while True:
            try:
                self.main_instance.play()
            except (PlayException, StartupException):
                self.all_leave_story_wave()
                return

            if self.main_instance.custom_sequence is not None:
                if not self.main_instance.do_custom_sequence():
                    if self.main_instance.find_text("victory") is not None:
                        if self.main_instance.find_text("playnext"):
                            self.all_play_next()
                            continue
                        else:
                            self.logger.debug("Won but couldn't find play next button")
                            self.all_leave_story_death()
                            break
                    elif self.main_instance.find_text("defeat") is not None:
                        self.logger.debug("Lost")
                        self.all_leave_story_death()
                        break
            else:
                if not self.main_instance.place_all_towers(config.tower_hotkey, config.tower_cap, config.tower_cost):
                    if self.main_instance.find_text("victory") is not None:
                        if self.main_instance.find_text("playnext"):
                            self.all_play_next()
                            continue
                        else:
                            self.logger.debug("Won but couldn't find play next button")
                            self.all_leave_story_death()
                            break
                    elif self.main_instance.find_text("defeat") is not None:
                        self.logger.debug("Lost")
                        self.all_leave_story_death()
                        break
                self.logger.debug(f"Finished placing towers")
                self.logger.debug(f"Upgrading towers")
                if not self.main_instance.upgrade_all_towers(config.tower_cap):
                    if self.main_instance.find_text("victory") is not None:
                        if self.main_instance.find_text("playnext"):
                            self.all_play_next()
                            continue
                        else:
                            self.logger.debug("Won but couldn't find play next button")
                            self.all_leave_story_death()
                            break
                    elif self.main_instance.find_text("defeat") is not None:
                        self.logger.debug("Lost")
                        self.all_leave_story_death()
                        break

    def all_enter_portal(self):
        assert isinstance(self.main_instance, RobloxPortal)
        self.logger.debug(f"Entering portal for all accounts")
        for instance in self.roblox_instances:
            try:
                instance.teleport()
            except StartupException:
                instance.close_instance()
                self.ensure_all_instance()
                self.all_enter_portal()
        for instance in self.roblox_instances:
            try:
                instance.enter()
            except (StartupException, MemoryException):
                instance.close_instance()
                self.ensure_all_instance()
                self.all_click_leave()
                self.all_enter_portal()
        self.logger.debug(f"Starting portal")
        self.main_instance.start()
        time.sleep(2)
        try:
            self.main_instance.play()
        except (PlayException, StartupException):
            self.all_leave_story_wave()
            return
        if self.main_instance.custom_sequence is not None:
            if not self.main_instance.do_custom_sequence():
                self.all_leave_story_death()
                return
        else:
            if not self.main_instance.place_all_towers(config.tower_hotkey, config.tower_cap, config.tower_cost):
                self.all_leave_story_death()
                return
            self.logger.debug(f"Finished placing towers")
            self.logger.debug(f"Upgrading towers")
            if not self.main_instance.upgrade_all_towers(config.tower_cap):
                self.all_leave_story_death()
                return

    def all_click_leave(self):
        for instance in self.roblox_instances:
            try:
                instance.set_foreground()
                time.sleep(0.5)
                instance.click_text("leave")
                time.sleep(0.5)
            except StartupException:
                pass

    def all_leave_story_death(self):
        for instance in self.roblox_instances:
            if not instance.leave_death():
                instance.leave_wave()

    def all_leave_story_wave(self):
        for instance in self.roblox_instances:
            instance.leave_wave()

    def all_play_next(self):
        for instance in self.roblox_instances:
            instance.play_next()

    def all_play_again(self):
        for instance in self.roblox_instances:
            instance.play_again()
