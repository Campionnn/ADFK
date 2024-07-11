import time
import logging

import config
from utils.control import Control
from utils.roblox import Roblox
if config.port == 0000:
    import config_personal as config


class RobloxManager:
    def __init__(self, logger: logging.Logger, roblox_pids=None, mode=1, world=1, level=None):
        self.logger = logger
        self.controller = Control(self.logger)
        self.mode = mode
        self.world = world
        self.level = level

        self.place_id = "17017769292"
        self.roblox_exe = "RobloxPlayerBeta.exe"

        self.main_instance = None
        self.roblox_instances = []
        if roblox_pids is not None:
            for pid, y_addrs in roblox_pids.items():
                username = config.usernames[list(roblox_pids.keys()).index(pid)]
                instance = Roblox(self.roblox_instances, self.logger, self.controller, username, pid, y_addrs)
                self.roblox_instances.append(instance)
            pids = {instance.pid: instance.y_addrs for instance in self.roblox_instances}
            self.logger.info(f"Roblox PIDs: {pids}")
            self.main_instance = [instance for instance in self.roblox_instances if instance.username == config.usernames[0]][0]

    def all_start_instance(self):
        for username in config.usernames:
            self.logger.debug(f"Creating instance for {username}")
            instance = Roblox(self.roblox_instances, self.logger, self.controller, username)
            while instance.y_addrs is None:
                instance.start_account()
                if instance.y_addrs is None:
                    self.logger.warning(f"Failed to start {username} instance")
                    instance.close_instance()
                    time.sleep(3)
            for instance in self.roblox_instances:
                if instance.check_crash():
                    self.roblox_instances.remove(instance)
                    self.logger.warning(f"Instance for {instance.username} crashed")
                    instance.pid = None
                    instance.y_addrs = None
                    while instance.y_addrs is None:
                        instance.start_account()
                        if instance.y_addrs is None:
                            self.logger.warning(f"Failed to start {username} instance")
                            instance.close_instance()
                            time.sleep(3)
        pids = {instance.pid: instance.y_addrs for instance in self.roblox_instances}
        self.logger.info(f"Roblox PIDs: {pids}")
        roblox_instances = []
        for username in config.usernames:
            for instance in self.roblox_instances:
                if instance.username == username:
                    roblox_instances.append(instance)
                    break
        self.roblox_instances = roblox_instances
        self.main_instance = [instance for instance in self.roblox_instances if instance.username == config.usernames[0]][0]

    def all_enter_infinite(self):
        self.logger.debug(f"Entering infinite for all accounts. World: {self.world} Level: {self.level}")
        self.main_instance.set_mode(self.mode, self.world, self.level)
        for instance in self.roblox_instances:
            if not instance.teleport_story():
                self.logger.warning(f"Failed to teleport {instance.username} to story")
                return
        for instance in self.roblox_instances:
            instance.enter_story()
        self.logger.debug(f"Starting story")
        self.main_instance.start_story()
        time.sleep(2)
        self.main_instance.play_story()
        if not self.main_instance.place_towers(config.tower_hotkey, config.tower_cap, config.tower_cost, config.wave_stop):
            if self.main_instance.current_wave[0] >= config.wave_stop:
                self.all_leave_story_wave()
                return
            else:
                self.all_leave_story_death()
                return
        self.logger.debug(f"Finished placing towers")
        self.logger.debug(f"Upgrading towers")
        if not self.main_instance.upgrade_towers(config.wave_stop, config.tower_cap):
            if self.main_instance.current_wave[0] >= config.wave_stop:
                self.all_leave_story_wave()
                return
            else:
                self.all_leave_story_death()
                return

    def all_enter_story(self):
        for world in range(self.world, 9):
            self.world = world
            self.main_instance.set_mode(self.mode, self.world, self.level)
            self.logger.debug(f"Entering story for all accounts. World: {self.world} Level: {self.level}")
            self.level = 1
            for instance in self.roblox_instances:
                if not instance.teleport_story():
                    self.logger.warning(f"Failed to teleport {instance.username} to story")
                    return
            for instance in self.roblox_instances:
                instance.enter_story()
            self.logger.debug(f"Starting story")
            self.main_instance.start_story()
            time.sleep(2)
            while True:
                self.main_instance.play_story()
                if not self.main_instance.place_towers(config.tower_hotkey, config.tower_cap, config.tower_cost, 0):
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
                if not self.main_instance.upgrade_towers(0, config.tower_cap):
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

    def all_leave_story_death(self):
        for instance in self.roblox_instances:
            instance.leave_story_death()
        for instance in self.roblox_instances:
            instance.close_announcement()

    def all_leave_story_wave(self):
        for instance in self.roblox_instances:
            instance.leave_story_wave()
        for instance in self.roblox_instances:
            instance.close_announcement()

    def all_play_next(self):
        for instance in self.roblox_instances:
            instance.play_next()

    def all_play_again(self):
        for instance in self.roblox_instances:
            instance.play_again()
