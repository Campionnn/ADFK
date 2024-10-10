from utils.roblox_types.roblox_base import RobloxBase

import time

from config_loader import load_config
config = load_config()
import coords
from utils import memory
from utils.exceptions import *


class RobloxInfinite(RobloxBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.set_coords()

    def set_coords(self):
        world_map = {
            1: 'windmill',
            2: 'haunted',
            3: 'cursed',
            4: 'blue',
            5: 'underwater',
            6: 'swordsman',
            7: 'snowy',
            8: 'crystal'
        }

        world_prefix = world_map.get(self.world)
        if world_prefix:
            self.world_sequence = getattr(coords, f"{world_prefix}_sequence")
            self.place_pos = getattr(coords, f"{world_prefix}_place_pos")
            self.place_pos_tolerance = getattr(coords, f"{world_prefix}_place_pos_tolerance")
            self.place_rot = getattr(coords, f"{world_prefix}_place_rot")
            self.place_rot_tolerance = getattr(coords, f"{world_prefix}_place_rot_tolerance")
            self.place_color = getattr(coords, f"{world_prefix}_place_color")
            self.place_color_tolerance = getattr(coords, f"{world_prefix}_place_color_tolerance")

    def teleport(self):
        self.set_foreground()
        self.wait_game_load("main")
        self.close_menu()
        try:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            attempts = 0
            while self.controller.calculate_distance(pos[0], pos[2], coords.story_play_pos[0], coords.story_play_pos[1]) > 50:
                if attempts > 2:
                    raise StartupException("Could not teleport to story")
                time.sleep(0.25)
                if not self.fast_travel("story"):
                    self.controller.jump()
                    time.sleep(0.1)
                    self.controller.look_down(1.0)
                    time.sleep(1)
                    self.controller.reset_look()
                    if not self.fast_travel("story"):
                        raise StartupException("Could not fast travel to story")
                time.sleep(0.5)
                if self.click_text("leave"):
                    time.sleep(0.1)
                    pos = memory.get_current_pos(self.pid, self.y_addrs)
                    continue
                time.sleep(0.25)
                pos = memory.get_current_pos(self.pid, self.y_addrs)
                attempts += 1
            time.sleep(0.25)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1], coords.story_play_pos_tolerance):
                return self.teleport()
            return True
        except MemoryException:
            raise StartupException("Could not teleport to story")

    def enter(self, depth=0):
        if depth > 2:
            raise StartupException("Could not go to infinite enter position")
        self.logger.info(f"Entering infinite for {self.username}")
        self.set_foreground()
        if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance):
            self.teleport()
            return self.enter(depth + 1)
        if self.username == config.usernames[0]:
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            if not self.click_nav_rect(self.world_sequence, "Could not find world button"):
                raise StartupException("Could not find world button")
            time.sleep(0.5)
            self.click_text("infinitemode")
            time.sleep(0.5)
            self.click_text("confirm")
        return True

    def check_over(self):
        if super().check_over():
            return True
        if config.wave_stop != -1 and self.current_wave[0] >= config.wave_stop and type(self) is RobloxInfinite:
            self.wave_checker.stop()
            time.sleep(3)
            return True
