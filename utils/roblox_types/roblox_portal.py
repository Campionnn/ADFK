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
from utils.exceptions import *


class RobloxPortal(RobloxBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.portal_names = {
            1: "Demon Portal",
            2: "Cursed Kingdom Portal",
            3: "Ancient Dragon Portal",
            4: "Solar Temple Portal",
            5: "Lunar Temple Portal"
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
        match self.world:
            case 1:
                self.place_pos = coords.demon_portal_place_pos
                self.place_pos_tolerance = coords.demon_portal_place_pos_tolerance
                self.place_rot = coords.demon_portal_place_rot
                self.place_rot_tolerance = coords.demon_portal_place_rot_tolerance
                self.place_color = coords.demon_portal_place_color
                self.place_color_tolerance = coords.demon_portal_place_color_tolerance
            case 2:
                self.place_pos = coords.cursed_portal_place_pos
                self.place_pos_tolerance = coords.cursed_portal_place_pos_tolerance
                self.place_rot = coords.cursed_portal_place_rot
                self.place_rot_tolerance = coords.cursed_portal_place_rot_tolerance
                self.place_color = coords.cursed_portal_place_color
                self.place_color_tolerance = coords.cursed_portal_place_color_tolerance
            case 3:
                self.place_pos = coords.ancient_portal_place_pos
                self.place_pos_tolerance = coords.ancient_portal_place_pos_tolerance
                self.place_rot = coords.ancient_portal_place_rot
                self.place_rot_tolerance = coords.ancient_portal_place_rot_tolerance
                self.place_color = coords.ancient_portal_place_color
                self.place_color_tolerance = coords.ancient_portal_place_color_tolerance
            case 4:
                self.place_pos = coords.solar_portal_place_pos
                self.place_pos_tolerance = coords.solar_portal_place_pos_tolerance
                self.place_rot = coords.solar_portal_place_rot
                self.place_rot_tolerance = coords.solar_portal_place_rot_tolerance
                self.place_color = coords.solar_portal_place_color
                self.place_color_tolerance = coords.solar_portal_place_color_tolerance
            # case 5:
            #     self.place_pos = coords.lunar_portal_place_pos
            #     self.place_pos_tolerance = coords.lunar_portal_place_pos_tolerance
            #     self.place_rot = coords.lunar_portal_place_rot
            #     self.place_rot_tolerance = coords.lunar_portal_place_rot_tolerance
            #     self.place_color = coords.lunar_portal_place_color
            #     self.place_color_tolerance = coords.lunar_portal_place_color_tolerance
            case _:
                raise ValueError("Invalid portal choice")

    def teleport(self):
        self.set_foreground()
        time.sleep(0.5)
        self.wait_game_load("main")
        self.click_text("x")
        try:
            time.sleep(0.25)
            if not self.fast_travel("trading"):
                self.controller.jump()
                time.sleep(0.5)
                self.controller.look_down(1.0)
                time.sleep(1)
                self.controller.reset_look()
                if not self.fast_travel("trading"):
                    raise StartupException("Could not fast travel to trading")
            time.sleep(0.5)
            if not self.controller.go_to_pos(self.pid, self.y_addrs, coords.portal_play_pos[0], coords.portal_play_pos[1], coords.portal_play_pos_tolerance, 10, precise=True):
                return self.teleport()
        except MemoryException:
            raise StartupException("Could not find portal")

    def enter(self, depth=0):
        if self.username == config.usernames[0]:
            self.logger.debug(f"Looking for {self.rarity_names.get(self.level)} {self.portal_names.get(self.world)} portal to open")
            found = False
            for instance in self.roblox_instances:
                if instance.open_portal():
                    found = True
                    break
            if not found:
                raise StartupException("Could not find portal")
        self.set_foreground()
        time.sleep(0.5)
        self.controller.move_forward(0.2)
        time.sleep(0.5)
        self.controller.reset()
        keyboard.press("e")
        time.sleep(1.5)
        keyboard.release("e")


    def open_portal(self):
        self.set_foreground()
        time.sleep(0.5)
        self.controller.zoom_in()
        self.controller.zoom_out(0.25)
        time.sleep(0.5)
        self.click_text("items")
        time.sleep(1)
        rect = self.get_window_rect()
        autoit.mouse_move(int(rect[2]//8*4.8), rect[3]//2)
        previous_text = ""
        new_text = "o.o"
        while difflib.SequenceMatcher(None, previous_text, new_text).ratio() < 0.9:
            previous_text = new_text
            portal_coords = ocr.find_portal(self.screenshot(), self.world, self.level)
            if portal_coords is not None:
                autoit.mouse_click("left", portal_coords[0], portal_coords[1])
                time.sleep(0.5)
                self.click_text("use")
                time.sleep(0.5)
                self.click_text("open")
                return True
            autoit.mouse_wheel("down", 4)
            new_text = ocr.find_all_text(self.screenshot())
        self.logger.debug(f"Could not find portal for {self.username}")
        return False

    def start(self):
        self.set_foreground()
        time.sleep(0.5)
        self.click_text("start")
