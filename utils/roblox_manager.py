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

    def start_all_accounts(self):
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
                    self.roblox_instances.append(instance)
                    self.logger.debug(f"Roblox instance for {username} started")
                    time.sleep(15)
                    self.logger.debug(f"Getting memory address for {username}")
                    address = instance.get_address()
                    if address is not None:
                        self.logger.debug(f"Memory address for {username} is {hex(address)}")
                        break
                time.sleep(1)

    def all_enter_story(self):
        self.logger.debug("Entering story for all accounts")
        for i, instance in enumerate(self.roblox_instances):
            instance.enter_story()
            if i == 0:
                instance.select_story()
        self.logger.debug(f"Starting story")
        time.sleep(0.5)
        self.roblox_instances[0].start_story()
