from utils.roblox_infinite import RobloxInfinite

import time

try:
    import config_personal as config
except ImportError:
    import config
import coords
from utils.exceptions import *


class RobloxStory(RobloxInfinite):
    def __init__(self, *args):
        super().__init__(*args)

    def enter(self, depth=0):
        self.logger.debug(f"Entering story for {self.username}")
        self.set_foreground()
        time.sleep(1)
        if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance, 20):
            if depth > 2:
                raise StartupException("Could not go to story enter position")
            self.teleport()
            return self.enter(depth + 1)
        if self.username == config.usernames[0]:
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            self.click_nav_rect(self.world_sequence, "Could not find world button")
            time.sleep(0.5)
            self.click_nav_rect("d"*10 + "a"*4 + "s" * (self.level-1) * 2, "Could not find selected chapter", restart=False, chapter=True)
            time.sleep(0.5)
            self.click_text("confirm")
        return True

    def set_world(self, world, level):
        self.world = world
        self.level = level
