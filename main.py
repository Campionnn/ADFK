import os
import logging
import time
import json
import ast
import pathlib
import keyboard
import threading

from utils.roblox_manager import RobloxManager
try:
    import config_personal as config
except ImportError:
    import config


def kill_thread():
    keyboard.wait(config.kill_key)
    os._exit(0)


pathlib.Path("./logs/").mkdir(parents=True, exist_ok=True)
pathlib.Path("./custom-place/").mkdir(parents=True, exist_ok=True)
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
print("3: Create a Custom Placement")
while True:
    try:
        choice1 = int(input("Enter choice: "))
        if choice1 in [1, 2, 3]:
            break
    except ValueError:
        pass

roblox_pids = None
custom_place = None
if choice1 in [1, 2]:
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
    custom_placements = [f for f in os.listdir("./custom-place/") if f.endswith(".json")]
    for i, placement in enumerate(custom_placements):
        with open(f"./custom-place/{placement}") as f:
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
        with open(f"./custom-place/{custom_placements[custom_input - 1]}", "r") as f:
            custom_place = json.load(f)
            print(custom_place)


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
    while True:
        try:
            world_input = int(input("Enter choice: "))
            if world_input in [1, 2, 3, 4, 5, 6, 7, 8]:
                break
        except ValueError:
            pass
    threading.Thread(target=kill_thread).start()
    roblox_manager = RobloxManager(logger, roblox_pids=roblox_pids, mode=choice1, world=world_input, custom_place=custom_place)
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
    threading.Thread(target=kill_thread).start()
    roblox_manager = RobloxManager(logger, roblox_pids=roblox_pids, mode=choice1, world=world_input, level=chapter_input, custom_place=custom_place)
    if roblox_pids is None:
        roblox_manager.all_start_instance()
    roblox_manager.all_enter_story()

elif choice1 == 3:
    print("Enter the name for custom placement")
    while True:
        name = input("Enter name: ")
        if name != "":
            break
    print("Enter the description for custom placement")
    while True:
        description = input("Enter description: ")
        if description != "":
            break
    actions = []
    ids = []
    while True:
        next_step = False
        while True:
            print("Choose between placing or upgrading")
            print("Press enter with no text to finish")
            print("1: Place")
            print("2: Upgrade")
            choice5 = input("Enter choice: ")
            if choice5 in ["1", "2"]:
                break
            elif choice5 == "":
                next_step = True
                break
        if next_step:
            break

        if choice5 == "1":
            place_ids = []
            print("Enter the hotkeys for the towers to place separated by spaces")
            hotkeys = input("Enter hotkeys: ")
            hotkeys = hotkeys.split()
            if all(item in ["1", "2", "3", "4", "5", "6"] for item in hotkeys):
                for hotkey in hotkeys:
                    count = 0
                    for id_ in place_ids:
                        if id_[0] == hotkey:
                            count += 1
                    for id_ in ids:
                        if id_[0] == hotkey:
                            count += 1
                    place_ids.append(f"{hotkey}{chr(ord('a') + count)}")
                ids = ids + place_ids
            else:
                print("Invalid hotkeys")
                continue
            while True:
                print("Choose the location of where to place the towers")
                print("1: Center")
                print("2: Edge")
                choice6 = input("Enter choice: ")
                if choice6 in ["1", "2"]:
                    break
            location = ""
            if choice6 == "1":
                location = "center"
            elif choice6 == "2":
                location = "edge"
            actions.append({"type": "place", "ids": place_ids, "location": location})
            print("========================================")
            print(f"Placed towers with ids {place_ids} at {location}")
            print("========================================")
        elif choice5 == "2":
            upgrade_ids = []
            print("Enter the ids of the towers you want to upgrade separated by spaces")
            ids_ = input("Enter ids: ")
            ids_ = ids_.split()
            if all(item in ids for item in ids_):
                upgrade_ids = ids_
            else:
                print("Invalid ids")
                continue
            print("Choose the amount of upgrades to perform")
            print("Enter 0 to continuously upgrade until the end of the game")
            while True:
                try:
                    amount = int(input("Enter amount: "))
                    if amount >= 0:
                        break
                except ValueError:
                    pass
            actions.append({"type": "upgrade", "ids": upgrade_ids, "amount": amount})
            print("========================================")
            print(f"Upgraded towers with ids {upgrade_ids} by {amount}")
            print("========================================")
    hotkeys = list(set([id_[0] for id_ in ids]))
    hotkeys.sort()

    costs = {}
    for hotkey in hotkeys:
        while True:
            try:
                cost = int(input(f"Enter the cost of the tower for hotkey {hotkey}: "))
                if cost > 0:
                    break
            except ValueError:
                pass
        costs[hotkey] = str(cost)

    with open(f"./custom-place/{name.replace(' ', '-').lower()}.json", "w") as f:
        json.dump({"name": name, "description": description, "actions": actions, "costs": costs}, f, indent=4)
    print("========================================")
    print(f"Custom placement saved as {name.replace(' ', '-').lower()}.json")
    print("========================================")
