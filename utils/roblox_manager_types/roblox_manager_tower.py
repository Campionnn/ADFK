from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time

from utils.exceptions import *
from utils.roblox_types.roblox_tower import RobloxTower
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManagerTower(RobloxManagerBase):
    def __init__(self, **kwargs):
        self.roblox_type = RobloxTower
        super().__init__(**kwargs)

    def all_enter(self):
        assert type(self.main_instance) is RobloxTower
        self.logger.info(f"Entering Tower of Eternity for main account")
        self.logger.info("Teleporting to tower enter position")
        try:
            self.main_instance.teleport()
        except StartupException:
            self.main_instance.close_instance()
            self.ensure_all_instance()
            return
        time.sleep(0.1)
        self.logger.info(f"Starting tower")
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
                    if self.main_instance.find_text("victory") is not None:
                        self.logger.debug("Detected victory screen")
                        if self.main_instance.find_text("playnext"):
                            self.logger.debug("Clicking play next")
                            self.all_play_next()
                            continue
                        else:
                            self.logger.debug("Won but couldn't find play next button")
                            self.all_back_to_lobby()
                            break
                    else:
                        self.all_back_to_lobby()
                        break
            except (PlayException, StartupException, MemoryException):
                self.all_back_to_lobby()
                self.ensure_all_instance()
                return
