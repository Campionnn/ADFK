import os
import logging
import time
import json
import ast
import pathlib
import keyboard
import threading
import tkinter as tk

from utils.sequence_maker import App
from utils.roblox_manager import RobloxManager
from utils.roblox_types.roblox_infinite import RobloxInfinite
from utils.roblox_types.roblox_story import RobloxStory
from utils.roblox_types.roblox_tower import RobloxTower
try:
    import config_personal as config
except ImportError:
    import config


def kill_thread():
    keyboard.wait(config.kill_key)
    os._exit(0)
threading.Thread(target=kill_thread).start()


pathlib.Path("./logs/").mkdir(parents=True, exist_ok=True)
pathlib.Path("custom-sequence/").mkdir(parents=True, exist_ok=True)
if config.logging_level == "debug":
    level = logging.DEBUG
else:
    level = logging.INFO
logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
rootLogger = logging.getLogger()
logPath = "./logs"
fileName = f"ADFK_{time.strftime('%Y%m%d-%H%M%S')}"
fileHandler = logging.FileHandler(f"{logPath}/{fileName}.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger = logging.getLogger()
logger.setLevel(level)
logging.getLogger().addHandler(consoleHandler)


print("Choose between infinite farming or story progression")
print("1: Infinite Farming")
print("2: Story Progression")
print("3: Tower of Eternity(only 1 account for now)")
print("4: Auto Complete Portals")
print("5: Create or Edit a Custom Placement")
while True:
    try:
        mode_choice = int(input("Enter choice: "))
        if mode_choice in [1, 2, 3, 4, 5]:
            break
    except ValueError:
        pass

roblox_pids = None
custom_place = None
if mode_choice in [1, 2, 3, 4]:
    print("Enter Roblox PIDs from running macro previously")
    print("Skips the steps for getting memory addresses on each instance")
    print("Can be found in the logs of the previous run")
    print("Roblox PIDs are no longer valid once the game is closed")
    print("Leave blank and press enter if you do not have PIDs")
    while True:
        try:
            pid_input = input("Enter Roblox PIDs: ")
            if pid_input:
                roblox_pids = ast.literal_eval(pid_input)
                assert isinstance(roblox_pids, dict)
                break
            else:
                break
        except (ValueError, AssertionError, SyntaxError):
            pass

    print("Choose a custom placement to use")
    print("Leave blank and press enter if you want to use default placement")
    custom_placements = [f for f in os.listdir("custom-sequence/") if f.endswith(".json")]
    for i, placement in enumerate(custom_placements):
        with open(f"custom-sequence/{placement}") as f:
            data = json.load(f)
            print(f"{i + 1}: {data['name']} - {data['description']}")
    while True:
        try:
            custom_input = input("Enter choice: ")
            if custom_input:
                custom_input = int(custom_input)
                assert custom_input in range(1, len(custom_placements) + 1)
                break
            else:
                break
        except (ValueError, AssertionError):
            pass
    if custom_input:
        with open(f"custom-sequence/{custom_placements[custom_input - 1]}", "r") as f:
            custom_place = json.load(f)
            print(custom_place)


if mode_choice == 1:
    print("Choose which world to farm in")
    print("1: Windmill Village")
    print("2: Haunted City")
    print("3: Cursed Academy")
    print("4: Blue Planet")
    print("5: Underwater Temple")
    print("6: Swordsman Dojo")
    print("7: Snowy Woods")
    print("8: Crystal Cave")
    while True:
        try:
            world_input = int(input("Enter choice: "))
            if world_input in [1, 2, 3, 4, 5, 6, 7, 8]:
                break
        except ValueError:
            pass
    RobloxManager(RobloxInfinite, logger, roblox_pids=roblox_pids, mode=mode_choice, world=world_input, custom_sequence=custom_place)

elif mode_choice == 2:
    print("Choose which world to start story progression in")
    print("1: Windmill Village")
    print("2: Haunted City")
    print("3: Cursed Academy")
    print("4: Blue Planet")
    print("5: Underwater Temple")
    print("6: Swordsman Dojo")
    print("7: Snowy Woods")
    print("8: Crystal Cave")
    while True:
        try:
            world_input = int(input("Enter choice: "))
            if world_input in [1, 2, 3, 4, 5, 6, 7, 8]:
                break
        except ValueError:
            pass
    print("Choose which chapter to start story progression in")
    print("1: Chapter 1")
    print("2: Chapter 2")
    print("3: Chapter 3")
    print("4: Chapter 4")
    print("5: Chapter 5")
    print("6: Chapter 6")
    while True:
        try:
            chapter_input = int(input("Enter choice: "))
            if chapter_input in [1, 2, 3, 4, 5, 6]:
                break
        except ValueError:
            pass
    RobloxManager(RobloxStory, logger, roblox_pids=roblox_pids, mode=mode_choice, world=world_input, level=chapter_input, custom_sequence=custom_place)

elif mode_choice == 3:
    if roblox_pids is not None:
        roblox_pids = {list(roblox_pids.keys())[0]: list(roblox_pids.values())[0]}
    RobloxManager(RobloxTower, logger, roblox_pids=roblox_pids, mode=mode_choice, world=101, custom_sequence=custom_place)

elif mode_choice == 5:
    root = tk.Tk()
    app = App(root)
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    root.lift()
    root.focus_force()
    root.mainloop()
os._exit(0)
