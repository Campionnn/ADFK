from utils.roblox_types.roblox_base import RobloxBase

import time
import keyboard

try:
    import config_personal as config
except ImportError:
    import config
import coords
from utils.exceptions import *


class RobloxTower(RobloxBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.set_coords()

    def set_coords(self):
        self.place_pos = coords.tower_place_pos
        self.place_pos_tolerance = coords.tower_place_pos_tolerance
        self.place_rot = coords.tower_place_rot
        self.place_rot_tolerance = coords.tower_place_rot_tolerance
        self.place_color = coords.tower_place_color
        self.place_color_tolerance = coords.tower_place_color_tolerance

    def teleport(self):
        self.set_foreground()
        time.sleep(0.5)
        self.wait_game_load("main")
        self.click_text("x")
        try:
            if not self.fast_travel("trading"):
                self.controller.jump()
                time.sleep(0.5)
                self.controller.look_down(1.0)
                time.sleep(1)
                self.controller.reset_look()
                if not self.fast_travel("trading"):
                    raise StartupException("Could not fast travel to tower")
                time.sleep(0.5)
            time.sleep(0.25)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.tower_enter_pos[0], coords.tower_enter_pos[1], coords.tower_enter_pos_tolerance, 10, precise=True):
                return self.teleport()
            return True
        except MemoryException:
            raise StartupException("Could not teleport to tower")

    def enter(self, depth=0):
        pass

    def start(self):
        self.set_foreground()
        time.sleep(0.5)
        keyboard.send('e')
        time.sleep(1)
        self.click_text("play")
        time.sleep(2)
        self.click_text("start")

    def spiral(self):
        super().spiral()
        self.spiral_coords = self.spiral_coords[9:]
