from utils.roblox_types.roblox_infinite import RobloxInfinite

import time

from config_loader import load_config
config = load_config()
import coords
from utils.exceptions import *


class RobloxStory(RobloxInfinite):
    def __init__(self, *args):
        super().__init__(*args)

    def enter(self, depth=0):
        self.logger.info(f"Entering story for {self.username}")
        self.set_foreground()
        if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance):
            if depth > 2:
                raise StartupException("Could not go to story enter position")
            self.teleport()
            return self.enter(depth + 1)
        if self.username == config.usernames[0]:
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            self.click_nav_rect(self.world_sequence, "Could not find world button")
            time.sleep(0.5)
            self.click_nav_rect("d"*10 + "w"*10 + "s" * (self.level - 1), "Could not find selected chapter", chapter=True)
            time.sleep(0.5)
            self.click_text("confirm")
        return True

    def set_world(self, world, level):
        self.world = world
        self.level = level
        self.set_coords()
