from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time

from utils.exceptions import *
from utils.roblox_types.roblox_realm_infinite import RobloxRealmInfinite
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManagerRealmInfinite(RobloxManagerBase):
    def __init__(self, **kwargs):
        self.roblox_type = RobloxRealmInfinite
        super().__init__(**kwargs)

    def all_enter(self):
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
                self.all_leave()
                return
        self.logger.info(f"Starting realm infinite")
        self.main_instance.start()
        time.sleep(2)
        while True:
            self.logger.info("Going to play position")
            try:
                self.main_instance.play()
            except (PlayException, StartupException):
                self.all_back_to_lobby()
                return
            self.logger.info("Performing custom sequence")
            try:
                if not self.main_instance.do_custom_sequence():
                    self.logger.info("Playing again")
                    self.all_play_again()
            except (PlayException, StartupException, MemoryException):
                self.all_back_to_lobby()
                self.ensure_all_instance()
                return
            self.main_instance.wave_checker.stop()