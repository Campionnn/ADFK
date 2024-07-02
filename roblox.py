import keyboard
import requests
import time
import mouse
import autoit
import pyautogui
from pywinauto import Application

import memory
import coords
import config
from control import Control
if config.port == 0000:
    import config_personal as config
from memory import get_pids_by_name

place_id = "17017769292"
roblox_exe = "RobloxPlayerBeta.exe"


class Roblox:
    def __init__(self):
        self.roblox_pids = {}
        self.controller = Control()

    def set_foreground_window(self, pid):
        app = Application().connect(process=pid)
        app.top_window().set_focus()

    def start_all_accounts(self):
        for i, username in enumerate(config.usernames):
            if self.start_account(username) != 200:
                print(f"Failed to start account {username}")
                continue
            while True:
                pids = get_pids_by_name(roblox_exe)
                for pid in pids:
                    if pid in self.roblox_pids.keys():
                        pids.remove(pid)
                if len(pids) != 0:
                    address = self.get_address(pids[0], username)
                    if address is not None:
                        break
                time.sleep(1)
            self.roblox_pids[pids[0]] = address
        return self.roblox_pids

    def start_account(self, username):
        # params = {
        #     "Account": username,
        #     "PlaceId": place_id,
        #     # "JobId": config.private_server_code,
        # }
        # if config.password != "":
        #     params["Password"] = config.password
        # result = requests.get(f"http://localhost:{config.port}/LaunchAccount", params=params)
        # return result.status_code
        print(f"Join private server with account {username} from Roblox Account Manager")
        return 200

    def get_address(self, pid, username):
        input("Press enter once fully loaded")
        self.set_foreground_window(pid)
        time.sleep(0.5)
        self.click(config.intro_close_coords[0], config.intro_close_coords[1])
        time.sleep(0.5)
        self.click(config.fast_travel_coords[0], config.fast_travel_coords[1])
        time.sleep(0.5)
        self.click(config.leaderboard_coords[0], config.leaderboard_coords[1])
        time.sleep(0.5)
        init_addresses = memory.search_init_pos(pid, coords.init_pos1, coords.init_tolerance1)
        self.click(config.fast_travel_coords[0], config.fast_travel_coords[1])
        time.sleep(0.5)
        self.click(config.afk_coords[0], config.afk_coords[1])
        input("Go into the AFK zone and press enter once fully loaded")
        final_addresses = memory.search_final_pos(pid, init_addresses, coords.init_pos2, coords.init_tolerance2)
        final_address = None
        for address in final_addresses:
            rot = memory.get_current_rot(pid, address)
            if rot[1] == 270.0 and abs(rot[0] + 0.6) < 0.1:
                final_address = address
                break
        if final_address is None:
            print("Could not find final address")
            self.start_account(username)
            return None
        self.set_foreground_window(pid)
        keyboard.press_and_release("esc")
        time.sleep(0.1)
        keyboard.press_and_release("l")
        time.sleep(0.1)
        keyboard.press_and_release("enter")
        input("Rejoin the private server from the Roblox home app under the Servers tab then press enter when fully loaded")
        self.set_foreground_window(pid)
        time.sleep(0.5)
        self.click(config.intro_close_coords[0], config.intro_close_coords[1])
        return final_address

    def click(self, x, y):
        autoit.mouse_click("left", x, y)

    def wait_pixel(self, x, y, color="0xFFFFFF", interval=0.1, timeout=1, inverse=False):
        time_exit = time.time() + timeout
        if inverse:
            while pyautogui.pixel(x, y) == color:
                if time.time() > time_exit:
                    return False
                time.sleep(interval)
        else:
            while pyautogui.pixel(x, y) != color:
                if time.time() > time_exit:
                    return False
                time.sleep(interval)
        return True

    def all_enter_story(self):
        for i, pid in enumerate(self.roblox_pids.keys()):
            self.enter_story(pid, self.roblox_pids[pid])
            if i == 0:
                time.sleep(0.5)
                self.click(config.world_coords[0], config.world_coords[1])
                time.sleep(0.5)
                self.click(config.infinite_coords[0], config.infinite_coords[1])
                time.sleep(0.5)
                self.click(config.confirm_coords[0], config.confirm_coords[1])
                time.sleep(0.5)
        time.sleep(0.5)
        self.set_foreground_window(self.roblox_pids[0])
        time.sleep(0.5)
        self.click(config.start_coords[0], config.start_coords[1])

    def enter_story(self, pid, y_address):
        self.set_foreground_window(pid)
        time.sleep(0.5)
        self.click(config.fast_travel_coords[0], config.fast_travel_coords[1])
        time.sleep(0.5)
        self.click(config.story_coords[0], config.story_coords[1])
        time.sleep(0.5)
        # self.controller.go_to_pos(pid, y_address, coords.story_mid_pos[0], coords.story_mid_pos[1], coords.story_mid_pos_tolerance)
        self.controller.go_to_pos(pid, y_address, coords.story_play_pos[0], coords.story_play_pos[1], coords.story_play_pos_tolerance)
        self.controller.go_to_pos(pid, y_address, coords.story_enter_pos[0], coords.story_enter_pos[1], coords.story_enter_pos_tolerance)
