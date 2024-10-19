from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time

from utils.exceptions import *
from utils.roblox_types.roblox_realm_infinite import RobloxRealmInfinite
from config_loader import load_config
config = load_config()


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
                self.all_leave()
                self.ensure_all_instance()
                return
        time.sleep(0.1)
        self.logger.info(f"Starting realm infinite")
        try:
            if not self.main_instance.start():
                self.all_leave()
                self.ensure_all_instance()
                return
        except StartupException:
            self.all_leave()
            self.ensure_all_instance()
            return
        time.sleep(2)
        new_world = True
        while True:
            self.logger.info("Going to play position")
            try:
                self.main_instance.play(new_world=new_world)
            except (PlayException, StartupException):
                self.all_back_to_lobby(True)
                self.ensure_all_instance()
                return
            self.logger.info("Performing custom sequence")
            try:
                if not self.main_instance.do_custom_sequence():
                    new_world = False
                    self.logger.info("Playing again")
                    self.all_play_again()
            except (PlayException, StartupException, MemoryException):
                self.all_back_to_lobby(True)
                self.ensure_all_instance()
                return
            self.main_instance.wave_checker.stop()
