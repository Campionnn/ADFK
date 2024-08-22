from utils.roblox_types.roblox_base import RobloxBase

import time

try:
    import config_personal as config
except ImportError:
    import config
import coords
from utils import memory
from utils.exceptions import *


class RobloxInfinite(RobloxBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.set_coords()

    def set_coords(self):
        match self.world:
            case 1:
                self.world_sequence = coords.windmill_sequence
                self.place_pos = coords.windmill_place_pos
                self.place_pos_tolerance = coords.windmill_place_pos_tolerance
                self.place_rot = coords.windmill_place_rot
                self.place_rot_tolerance = coords.windmill_place_rot_tolerance
                self.place_color = coords.windmill_place_color
                self.place_color_tolerance = coords.windmill_place_color_tolerance
            case 2:
                self.world_sequence = coords.haunted_sequence
                self.place_pos = coords.haunted_place_pos
                self.place_pos_tolerance = coords.haunted_place_pos_tolerance
                self.place_rot = coords.haunted_place_rot
                self.place_rot_tolerance = coords.haunted_place_rot_tolerance
                self.place_color = coords.haunted_place_color
                self.place_color_tolerance = coords.haunted_place_color_tolerance
            case 3:
                self.world_sequence = coords.cursed_sequence
                self.place_pos = coords.cursed_place_pos
                self.place_pos_tolerance = coords.cursed_place_pos_tolerance
                self.place_rot = coords.cursed_place_rot
                self.place_rot_tolerance = coords.cursed_place_rot_tolerance
                self.place_color = coords.cursed_place_color
                self.place_color_tolerance = coords.cursed_place_color_tolerance
            case 4:
                self.world_sequence = coords.blue_sequence
                self.place_pos = coords.blue_place_pos
                self.place_pos_tolerance = coords.blue_place_pos_tolerance
                self.place_rot = coords.blue_place_rot
                self.place_rot_tolerance = coords.blue_place_rot_tolerance
                self.place_color = coords.blue_place_color
                self.place_color_tolerance = coords.blue_place_color_tolerance
            case 5:
                self.world_sequence = coords.underwater_sequence
                self.place_pos = coords.underwater_place_pos
                self.place_pos_tolerance = coords.underwater_place_pos_tolerance
                self.place_rot = coords.underwater_place_rot
                self.place_rot_tolerance = coords.underwater_place_rot_tolerance
                self.place_color = coords.underwater_place_color
                self.place_color_tolerance = coords.underwater_place_color_tolerance
            case 6:
                self.world_sequence = coords.swordsman_sequence
                self.place_pos = coords.swordsman_place_pos
                self.place_pos_tolerance = coords.swordsman_place_pos_tolerance
                self.place_rot = coords.swordsman_place_rot
                self.place_rot_tolerance = coords.swordsman_place_rot_tolerance
                self.place_color = coords.swordsman_place_color
                self.place_color_tolerance = coords.swordsman_place_color_tolerance
            case 7:
                self.world_sequence = coords.snowy_sequence
                self.place_pos = coords.snowy_place_pos
                self.place_pos_tolerance = coords.snowy_place_pos_tolerance
                self.place_rot = coords.snowy_place_rot
                self.place_rot_tolerance = coords.snowy_place_rot_tolerance
                self.place_color = coords.snowy_place_color
                self.place_color_tolerance = coords.snowy_place_color_tolerance
            case 8:
                self.world_sequence = coords.crystal_sequence
                self.place_pos = coords.crystal_place_pos
                self.place_pos_tolerance = coords.crystal_place_pos_tolerance
                self.place_rot = coords.crystal_place_rot
                self.place_rot_tolerance = coords.crystal_place_rot_tolerance
                self.place_color = coords.crystal_place_color
                self.place_color_tolerance = coords.crystal_place_color_tolerance
            case _:
                raise ValueError("Invalid world choice")

    def teleport(self):
        self.set_foreground()
        time.sleep(0.5)
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
                    time.sleep(0.5)
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
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_play_pos[0], coords.story_play_pos[1], coords.story_play_pos_tolerance, 10, precise=True):
                return self.teleport()
            return True
        except MemoryException:
            raise StartupException("Could not teleport to story")

    def enter(self, depth=0):
        self.logger.info(f"Entering infinite for {self.username}")
        self.set_foreground()
        time.sleep(1)
        if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance, 20):
            if depth > 2:
                raise StartupException("Could not go to infinite enter position")
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

    def start(self):
        self.set_foreground()
        time.sleep(0.5)
        self.click_text("start")

    def check_over(self):
        if super().check_over():
            return True
        if self.current_wave[0] >= config.wave_stop and type(self) is RobloxInfinite:
            self.wave_checker.stop()
            time.sleep(3)
            return True
