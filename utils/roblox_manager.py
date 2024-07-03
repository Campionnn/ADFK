import time
import logging

import config
from utils.control import Control
from utils.roblox import Roblox
if config.port == 0000:
    import config_personal as config
from utils.memory import get_pids_by_name


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
                instance = Roblox(self.logger, self.controller, username, pid, y_addrs)
                self.roblox_instances.append(instance)

    def all_start_instance(self):
        for i, username in enumerate(config.usernames):
            instance = Roblox(self.logger, self.controller, username)
            if instance.start_account() != 200:
                self.logger.error(f"Failed to start Roblox instance for {username}")
                continue
            self.logger.debug(f"Waiting for Roblox instance for {username} to start")
            while True:
                pids = get_pids_by_name(self.roblox_exe)
                for pid in pids:
                    if pid in [instance.pid for instance in self.roblox_instances]:
                        pids.remove(pid)
                if len(pids) != 0:
                    instance.pid = pids[0]
                    self.logger.debug(f"Roblox instance for {username} started. Waiting for window to appear")
                    while True:
                        try:
                            instance.set_foreground()
                            break
                        except RuntimeError:
                            time.sleep(1)
                    time.sleep(2)
                    self.logger.debug(f"Getting memory address for {username}")
                    address = instance.get_address()
                    if address is not None:
                        self.roblox_instances.append(instance)
                        self.logger.debug(f"Memory address for {username} is {hex(address)}")
                        break
                time.sleep(1)

    def all_enter_story(self):
        self.logger.debug("Entering story for all accounts")
        for instance in self.roblox_instances:
            instance.teleport_story()
        for i, instance in enumerate(self.roblox_instances):
            instance.enter_story()
            if i == 0:
                self.controller.zoom_in()
                self.controller.zoom_out(0.5)
                instance.select_story()
        self.logger.debug(f"Starting story")
        roblox_main = self.roblox_instances[0]
        time.sleep(0.5)
        roblox_main.start_story()
        time.sleep(2)
        roblox_main.play_story()
        roblox_main.place_towers(config.tower_hotkey, config.tower_cap, config.tower_wait)
        self.logger.debug(f"Finished placing towers")
