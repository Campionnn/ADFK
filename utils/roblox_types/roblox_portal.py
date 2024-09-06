from utils.roblox_types.roblox_base import RobloxBase

import time
import autoit
import difflib
import keyboard

try:
    import config_personal as config
except ImportError:
    import config
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
            while self.controller.calculate_distance(pos[0], pos[2], coords.portal_play_pos[0], coords.portal_play_pos[1]) > 15:
                if attempts > 2:
                    raise StartupException("Could not find portal")
                time.sleep(0.25)
                if not self.fast_travel("trading"):
                    self.controller.jump()
                    time.sleep(0.5)
                    self.controller.look_down(1.0)
                    time.sleep(1)
                    self.controller.reset_look()
                    if not self.fast_travel("trading"):
                        raise StartupException("Could not fast travel to trading")
                time.sleep(0.25)
                pos = memory.get_current_pos(self.pid, self.y_addrs)
                attempts += 1
            time.sleep(0.25)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.portal_play_pos[0], coords.portal_play_pos[1], coords.portal_play_pos_tolerance):
                return self.teleport()
            self.controller.turn_towards_yaw(self.pid, self.y_addrs, coords.portal_play_rot, coords.portal_play_rot_tolerance)
        except MemoryException:
            raise StartupException("Could not find portal")

    def enter(self, depth=0):
        host = ""
        if self.username == config.usernames[0]:
            if self.level > 10:
                self.logger.info(f"Looking for best {self.portal_names.get(self.world)} to open")
                host = self.open_best_portal()
                if host == "":
                    raise StartupException("Could not find portal to open")
            else:
                self.logger.info(f"Looking for {self.rarity_names.get(self.level)} {self.portal_names.get(self.world)} to open")
                found = False
                attempts = 0
                while not found:
                    if attempts > 3:
                        raise StartupException("Could not find portal to open")
                    for username in config.usernames:
                        if self.roblox_instances[username].open_portal():
                            host = username
                            found = True
                            break
                    attempts += 1
        if host != self.username:
            self.set_foreground()
            self.close_menu()
            self.controller.move_forward(0.4)
            time.sleep(0.25)
            self.controller.reset()
            time.sleep(0.1)
            keyboard.press("e")
            time.sleep(0.1)
            keyboard.release("e")
            time.sleep(0.1)
            keyboard.press("e")
            time.sleep(2.5)
            keyboard.release("e")
        return host

    def open_inventory(self, search=None):
        self.set_foreground()
        self.close_menu()
        self.click_text("items")
        time.sleep(0.5)
        if search is not None:
            self.click_text("search")
            time.sleep(0.1)
            keyboard.write(search)
            time.sleep(0.1)
        rect = self.get_window_rect()
        # move mouse to scrollbar area so doesn't hover over items. might not be reliable
        self.mouse_move(int(rect[2]//8*4.8), rect[3]//2)

    def open_portal(self, level=None):
        if level is None:
            level = self.level
        self.open_inventory(self.portal_names.get(self.world))
        rect = self.get_window_rect()
        portal_coords = ocr.find_portal(self.screenshot(), level)
        if portal_coords is not None:
            self.mouse_click(portal_coords[0], portal_coords[1])
            time.sleep(0.1)
            self.mouse_move(int(rect[2]//8*4.8), rect[3]//2)
            time.sleep(0.5)
            if not self.click_text("use"):
                self.close_menu()
                return False
            time.sleep(0.5)
            if not self.click_text("openportal"):
                self.click_text("back")
                time.sleep(0.5)
                self.close_menu()
                return False
            return True
        self.logger.info(f"Could not find portal for {self.username}")
        self.close_menu()
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
        self.open_inventory(self.portal_names.get(self.world))
        best_portal = 0
        rarity = ocr.find_best_portal(self.screenshot(), self.level - 11)
        if rarity is not None:
            if self.level - 11 >= rarity > best_portal:
                best_portal = rarity
        if best_portal == 0:
            self.logger.info(f"Could not find portal for {self.username}")
        else:
            self.logger.info(f"Best portal for {self.username} is {self.rarity_names.get(best_portal)}")
        self.close_menu()
        return best_portal

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
