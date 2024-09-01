from utils.roblox_types.roblox_base import RobloxBase

import time
import keyboard

try:
    import config_personal as config
except ImportError:
    import config
import coords
from utils import memory
from utils.exceptions import *


class RobloxRealmBase(RobloxBase):
    def __init__(self, *args):
        super().__init__(*args)

    def set_coords(self):
        world_map = {
            1: 'ruined',
            2: 'aether',
            3: 'pantheon',
            4: 'abyssal',
            5: 'soulweaver',
            6: 'cyber'
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

    def teleport(self, room=1):
        pass

    def enter_realm(self, depth=0):
        self.set_foreground()
        time.sleep(0.5)
        self.wait_game_load("main")
        self.close_menu()
        if depth > 2:
            raise StartupException("Could not travel to Athenyx Realm")
        try:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            if pos[1] <= -100:
                return True
            attempts = 0
            while self.controller.calculate_distance(pos[0], pos[2], coords.realm_travel_pos[0], coords.realm_travel_pos[1]) > 135:
                if attempts > 2:
                    raise StartupException("Could not travel to Athenyx Realm")
                time.sleep(0.25)
                if not self.fast_travel("afk"):
                    self.controller.jump()
                    time.sleep(0.5)
                    self.controller.look_down(1.0)
                    time.sleep(1)
                    self.controller.reset_look()
                    if not self.fast_travel("afk"):
                        raise StartupException("Could not fast travel to afk")
                time.sleep(0.25)
                pos = memory.get_current_pos(self.pid, self.y_addrs)
                attempts += 1
            time.sleep(0.25)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.realm_travel_pos[0], coords.realm_travel_pos[1], coords.realm_travel_pos_tolerance):
                return self.enter_realm(depth + 1)
        except MemoryException:
            raise StartupException("Could not travel to Athenyx Realm")
        time.sleep(0.1)
        keyboard.send("e")
        time.sleep(0.1)
        keyboard.send("e")
        time.sleep(0.2)
        if not self.click_text("traveltoatheynx"):  # why did they misspell it here x_x
            return self.enter_realm(depth + 1)
        time.sleep(0.2)
        if self.username == config.usernames[0]:
            if not self.click_text("teleport"):
                return self.enter_realm(depth + 1)
            return True
        else:
            if not self.click_text("joinfriend"):
                return self.enter_realm(depth + 1)
            time.sleep(0.1)
            if not self.click_text("typehere"):
                return self.enter_realm(depth + 1)
            time.sleep(0.1)
            keyboard.write(config.usernames[0])
            time.sleep(0.1)
            if not self.click_text("teleport"):
                return self.enter_realm(depth + 1)
            time.sleep(2)
            if self.find_text("traveltoatheynx"):
                raise StartupException("Main account not in Athenyx Realm")
            return True

    def leave_realm(self):
        self.set_foreground()
        time.sleep(0.5)
        self.wait_game_load("main")
        self.close_menu()
        try:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            if pos[1] <= -100:
                self.controller.move_forward(-1)
                time.sleep(1)
                self.controller.reset()
                time.sleep(0.1)
                keyboard.send("e")
                time.sleep(0.1)
                keyboard.send("e")
                time.sleep(0.1)
                if not self.click_text("leave"):
                    if not self.fast_travel("summon"):
                        raise StartupException("Could not fast travel to summon")
                    self.controller.go_to_pos(self.pid, self.y_addrs, coords.realm_leave_pos[0], coords.realm_leave_pos[1], coords.realm_leave_pos_tolerance)
                    time.sleep(0.1)
                    keyboard.send("e")
                    time.sleep(0.1)
                    keyboard.send("e")
                    if not self.click_text("leave"):
                        raise StartupException("Could not leave realm")
        except MemoryException:
            raise StartupException("Could not travel to Athenyx Realm")

    def enter(self, depth=0):
        pass

    def start(self):
        self.set_foreground()
        time.sleep(0.5)
        self.click_text("start")
