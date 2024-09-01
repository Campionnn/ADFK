from utils.roblox_types.roblox_realm_base import RobloxRealmBase

import time

try:
    import config_personal as config
except ImportError:
    import config
import coords
from utils import memory
from utils.exceptions import *


class RobloxRealmInfinite(RobloxRealmBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.set_coords()

    def teleport(self, room=1):
        self.set_foreground()
        time.sleep(1)
        self.wait_game_load("main")
        self.close_menu()
        try:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            attempts = 0
            while self.controller.calculate_distance(pos[0], pos[2], coords.realm_story_pos_a[0], coords.realm_story_pos_a[1]) > 100:
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
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.realm_story_pos_a[0], coords.realm_story_pos_a[1], coords.realm_play_pos_tolerance):
                return self.teleport()
            return True
        except MemoryException:
            raise StartupException("Could not teleport to story")
        pass

    def enter(self, depth=0):
        if depth > 2:
            raise StartupException("Could not go to infinite enter position")
        self.logger.info(f"Entering infinite for {self.username}")
        self.set_foreground()
        time.sleep(1)
        if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.realm_story_pos_1[0], coords.realm_story_pos_1[1], coords.realm_enter_pos_tolerance, timeout=5):
            self.click_text("leave")
            self.fast_travel("summon")
            self.teleport()
            return self.enter(depth + 1)
        if self.username == config.usernames[0]:
            start = time.time()
            self.logger.info("Checking if main account joined random")
            while time.time() - start < 2:
                if self.click_text("panicleave", False):
                    time.sleep(10)
                    self.teleport()
                    return self.enter(depth + 1)
            self.controller.zoom_in()
            self.controller.zoom_out(0.25)
            if not self.click_text("friendsonly"):
                raise StartupException("Could not find friends only checkbox")
            time.sleep(0.5)
            if not self.click_nav_rect(self.world_sequence, "Could not find world button"):
                raise StartupException("Could not find world button")
            time.sleep(0.5)
            self.click_text("infinitechallenge")
            time.sleep(0.5)
            self.click_text("confirm")
        return True

    def check_over(self):
        if super().check_over():
            return True
        if self.current_wave[0] >= config.wave_stop and type(self) is RobloxRealmInfinite:
            self.wave_checker.stop()
            self.sell_flag = True
            return False
