from utils.roblox_types.roblox_base import RobloxBase

import time
import keyboard

from config_loader import load_config
config = load_config()
import coords
from utils import ocr
from utils import memory
from utils.exceptions import *


class RobloxPortal(RobloxBase):
    def __init__(self, *args):
        self.cost_multiplier = 1.25
        super().__init__(*args)

        self.portal_names = {
            1: "Demon Portal",
            2: "Cursed Kingdom Portal",
            3: "Ancient Dragon Portal",
            4: "Solar Portal",
            5: "Lunar Portal"
        }
        self.rarity_names = {
            1: "Rare",
            2: "Epic",
            3: "Legendary",
            4: "Mythic",
            5: "Secret"
        }

        self.set_coords()

    def set_coords(self):
        portal_map = {
            1: 'demon_portal',
            2: 'cursed_portal',
            3: 'ancient_portal',
            4: 'solar_portal',
            5: 'lunar_portal'
        }

        portal_prefix = portal_map.get(self.world)
        if portal_prefix:
            self.place_pos = getattr(coords, f"{portal_prefix}_place_pos")
            self.place_pos_tolerance = getattr(coords, f"{portal_prefix}_place_pos_tolerance")
            self.place_rot = getattr(coords, f"{portal_prefix}_place_rot")
            self.place_rot_tolerance = getattr(coords, f"{portal_prefix}_place_rot_tolerance")
            self.place_color = getattr(coords, f"{portal_prefix}_place_color")
            self.place_color_tolerance = getattr(coords, f"{portal_prefix}_place_color_tolerance")

    def teleport(self):
        self.set_foreground()
        self.wait_game_load("main")
        self.close_menu()
        try:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            attempts = 0
            while self.controller.calculate_distance(pos[0], pos[2], coords.portal_play_pos[0], coords.portal_play_pos[1]) > 25:
                if attempts > 2:
                    raise StartupException("Could not find portal")
                time.sleep(0.1)
                if not self.fast_travel("afk"):
                    self.controller.jump()
                    time.sleep(0.5)
                    self.controller.look_down(1.0)
                    time.sleep(1)
                    self.controller.reset_look()
                    if not self.fast_travel("afk"):
                        raise StartupException("Could not fast travel to trading")
                time.sleep(0.1)
                pos = memory.get_current_pos(self.pid, self.y_addrs)
                attempts += 1
            time.sleep(0.1)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.portal_play_pos[0], coords.portal_play_pos[1], coords.portal_play_pos_tolerance):
                return self.teleport()
            self.controller.turn_towards_yaw(self.pid, self.y_addrs, coords.portal_play_rot, coords.portal_play_rot_tolerance)
        except MemoryException:
            raise StartupException("Could not find portal")

    def enter(self, depth=0):
        self.set_foreground()
        self.close_menu()
        time.sleep(0.1)
        self.controller.move_forward(0.4)
        time.sleep(0.25)
        self.controller.reset()
        time.sleep(0.1)
        keyboard.press("e")
        time.sleep(0.1)
        keyboard.release("e")
        time.sleep(0.1)
        keyboard.press("e")
        start = time.time()
        while time.time() - start < 2.5:
            if self.find_text("leave"):
                break
        keyboard.release("e")

    def open_portal(self, level=None):
        self.set_foreground()
        if level is None:
            level = self.level
        rect = self.get_window_rect()
        portal_coords = ocr.find_portal(self.screenshot(), level)
        if portal_coords is not None:
            self.mouse_click(portal_coords[0], portal_coords[1])
            time.sleep(0.1)
            self.mouse_move(rect[0], rect[3]//2)
            if not self.click_text("use"):
                self.close_menu()
                return False
            time.sleep(0.1)
            if not self.click_text("openportal"):
                self.click_text("back")
                time.sleep(0.1)
                self.close_menu()
                return False
            time.sleep(0.1)
            if self.find_text("back"):
                self.click_text("back")
                time.sleep(0.1)
                self.close_menu()
                return False
            return True
        self.logger.info(f"Could not find portal for {self.username}")
        return False

    def open_best_portal(self):
        best_portal = 0
        best_instance = None
        for username in config.usernames:
            instance = self.roblox_instances[username]
            portal = instance.get_best_portal()
            if portal > best_portal:
                best_portal = portal
                best_instance = instance
                if best_portal == self.level - 11:
                    break
        if best_instance is not None:
            attempts = 0
            while True:
                if attempts > 3:
                    return ""
                if best_instance.open_portal(best_portal):
                    return best_instance.username
                attempts += 1
        return ""

    def get_best_portal(self):
        return ocr.find_best_portal(self.screenshot(), self.level - 11)

    def go_to_play(self):
        if self.world == 4:
            pos = memory.get_current_pos(self.pid, self.y_addrs)
            dist_front = self.controller.calculate_distance(pos[0], pos[2], coords.solar_portal_front_pos[0], coords.solar_portal_front_pos[1])
            dist_back = self.controller.calculate_distance(pos[0], pos[2], coords.solar_portal_place_pos[0], coords.solar_portal_place_pos[1])
            if dist_front < dist_back:
                self.cont_go_to_pos(coords.solar_portal_front_pos[0], coords.solar_portal_front_pos[1], coords.solar_portal_front_pos_tolerance, jump=True)
                self.controller.reset()
                time.sleep(0.1)
                self.cont_go_to_pos(coords.solar_portal_bridge_pos[0], coords.solar_portal_bridge_pos[1], coords.solar_portal_bridge_pos_tolerance, jump=True)
        super().go_to_play()
