from utils.roblox_manager_types.roblox_manager_base import RobloxManagerBase

import time

from utils.exceptions import *
from utils.roblox_types.roblox_story import RobloxStory
try:
    import config_personal as config
except ImportError:
    import config


class RobloxManagerStory(RobloxManagerBase):
    def __init__(self, **kwargs):
        self.roblox_type = RobloxStory
        super().__init__(**kwargs)

    def all_enter(self):
        assert type(self.main_instance) is RobloxStory
        self.main_instance: RobloxStory  # type hint to suppress warnings
        while self.world <= 9:
            self.main_instance.set_world(self.world, self.level)
            self.logger.info(f"Entering story for all accounts. World: {self.world} Level: {self.level}")
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
            time.sleep(0.1)
            self.logger.debug(f"Starting story")
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
                        time.sleep(0.5)
                        if self.main_instance.find_text("victory") is not None:
                            self.logger.debug("Detected victory screen")
                            if self.main_instance.find_text("playnext"):
                                self.logger.debug("Clicking play next")
                                self.all_play_next()
                                self.level += 1
                                continue
                            else:
                                self.logger.debug("Finished world. Going back to lobby")
                                self.all_back_to_lobby()
                                self.world += 1
                                self.level = 1
                                break
                        elif self.main_instance.find_text("defeat") is not None:
                            self.logger.warning("Detected defeat screen. Trying again")
                            self.all_play_again()
                            continue
                        else:
                            self.all_back_to_lobby()
                            break
                except (PlayException, StartupException, MemoryException):
                    self.all_back_to_lobby()
                    self.ensure_all_instance()
                    break
        return True
