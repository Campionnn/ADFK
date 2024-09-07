from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time

from utils.exceptions import *
from utils.roblox_types.roblox_infinite import RobloxInfinite
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManagerInfinite(RobloxManagerBase):
    def __init__(self, **kwargs):
        self.roblox_type = RobloxInfinite
        super().__init__(**kwargs)

    def all_enter(self):
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
                self.all_leave()
                return
        self.logger.info(f"Starting story")
        self.main_instance.start()
        time.sleep(2)
        self.logger.info("Going to play position")
        try:
            self.main_instance.play()
        except (PlayException, StartupException):
            self.all_back_to_lobby()
            return
        self.logger.info("Performing custom sequence")
        try:
            if not self.main_instance.do_custom_sequence():
                self.logger.info("Leaving infinite")
                self.all_back_to_lobby()
                return
        except (PlayException, StartupException, MemoryException):
            self.all_back_to_lobby()
            self.ensure_all_instance()
            return