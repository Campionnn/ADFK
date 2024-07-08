import time
import logging

import config
from utils.control import Control
from utils.roblox import Roblox
if config.port == 0000:
    import config_personal as config


class RobloxManager:
    def __init__(self, logger: logging.Logger, roblox_pids=None):
        self.place_id = "17017769292"
        self.roblox_exe = "RobloxPlayerBeta.exe"

        self.logger = logger
        self.controller = Control(self.logger)

        self.roblox_instances = []
        if roblox_pids is not None:
            for pid, y_addrs in roblox_pids.items():
                username = config.usernames[list(roblox_pids.keys()).index(pid)]
                instance = Roblox(self.roblox_instances, self.logger, self.controller, username, pid, y_addrs)
                self.roblox_instances.append(instance)

    def all_start_instance(self):
        for i, username in enumerate(config.usernames):
            self.logger.debug(f"Creating instance object for {username}")
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
                    instance.start_account()

    def all_enter_story(self):
        self.logger.debug("Entering story for all accounts")

        roblox_instances = []
        for username in config.usernames:
            for instance in self.roblox_instances:
                if instance.username == username:
                    roblox_instances.append(instance)
                    break
        self.roblox_instances = roblox_instances

        for instance in self.roblox_instances:
            while not instance.teleport_story():
                time.sleep(0.5)
        for i, instance in enumerate(self.roblox_instances):
            instance.enter_story()
        self.logger.debug(f"Starting story")
        roblox_main = [instance for instance in self.roblox_instances if instance.username == config.usernames[0]][0]
        time.sleep(0.5)
        roblox_main.start_story()
        time.sleep(2)
        roblox_main.play_story()
        if not roblox_main.place_towers(config.tower_hotkey, config.tower_cap, config.tower_cost, config.wave_stop):
            if roblox_main.current_wave[0] >= config.wave_stop:
                self.all_leave_story_wave()
                return
            else:
                self.all_leave_story_death()
                return
        self.logger.debug(f"Finished placing towers")
        self.logger.debug(f"Upgrading towers")
        if not roblox_main.upgrade_towers(config.wave_stop):
            if roblox_main.current_wave[0] >= config.wave_stop:
                self.all_leave_story_wave()
                return
            else:
                self.all_leave_story_death()
                return

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
