import os
import logging
import time
import ast
import pathlib
import keyboard
import threading

from utils.roblox_manager import RobloxManager
import config
if config.port == 0000:
    import config_personal as config

def kill_thread():
    keyboard.wait(config.kill_key)
    os._exit(0)
threading.Thread(target=kill_thread).start()

pathlib.Path("./logs/").mkdir(parents=True, exist_ok=True)
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
choice1 = int(input("Enter choice: "))
print("Enter Roblox PIDs from running macro previously")
print("Skips the steps for getting memory addresses on each instance")
print("Can be found in the logs of the previous run")
print("Roblox PIDs are no longer valid once the game is closed")
print("Leave blank and press enter if you do not have PIDs")
choice2 = input("Enter Roblox PIDs: ")
if choice2:
    roblox_pids = ast.literal_eval(choice2)
else:
    roblox_pids = None
if choice1 == 1:
    print("Choose which world to farm in")
    print("1: Windmill Village")
    print("2: Haunted City")
    print("3: Cursed Academy")
    print("4: Blue Planet")
    print("5: Underwater Temple")
    print("6: Swordsman Dojo")
    print("7: Snowy Woods")
    print("8: Crystal Cave")
    choice3 = int(input("Enter choice: "))
    roblox_manager = RobloxManager(logger, roblox_pids=roblox_pids, mode=choice1, world=choice3)
    if roblox_pids is None:
        roblox_manager.all_start_instance()
    while True:
        roblox_manager.all_enter_infinite()

elif choice1 == 2:
    print("Choose which world to start story progression in")
    print("1: Windmill Village")
    print("2: Haunted City")
    print("3: Cursed Academy")
    print("4: Blue Planet")
    print("5: Underwater Temple")
    print("6: Swordsman Dojo")
    print("7: Snowy Woods")
    print("8: Crystal Cave")
    choice3 = int(input("Enter choice: "))
    print("Choose which chapter to start story progression in")
    print("1: Chapter 1")
    print("2: Chapter 2")
    print("3: Chapter 3")
    print("4: Chapter 4")
    print("5: Chapter 5")
    print("6: Chapter 6")
    choice4 = int(input("Enter choice: "))
    roblox_manager = RobloxManager(logger, roblox_pids=roblox_pids, mode=choice1, world=choice3, level=choice4)
    if roblox_pids is None:
        roblox_manager.all_start_instance()
    roblox_manager.all_enter_story()
