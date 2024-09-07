from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time

from utils.exceptions import *
from utils.roblox_types.roblox_portal import RobloxPortal
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManagerPortal(RobloxManagerBase):
    def __init__(self, **kwargs):
        self.roblox_type = RobloxPortal
        super().__init__(**kwargs)

    def all_enter(self):
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
            self.all_leave()
            return
        for username in config.usernames[1:]:
            instance = self.roblox_instances[username]
            if instance.username != host:
                try:
                    instance.enter()
                except (StartupException, MemoryException):
                    instance.close_instance()
                    self.ensure_all_instance()
                    self.all_leave()
                    return
        self.logger.info(f"Starting portal")
        try:
            if not self.roblox_instances.get(host).start():
                self.logger.warning("Failed to start portal. Retrying")
                self.all_leave()
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
            self.all_back_to_lobby()
            return
        self.logger.info("Performing custom sequence")
        try:
            if not self.main_instance.do_custom_sequence():
                self.all_back_to_lobby()
                return
        except (PlayException, StartupException, MemoryException):
            self.all_back_to_lobby()
            self.ensure_all_instance()
            return self.all_enter()
