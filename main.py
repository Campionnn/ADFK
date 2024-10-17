import os
import logging
import time
import json
import ast
import pathlib
import tkinter as tk
import importlib
import subprocess
import multiprocessing
import sys
import traceback
from config_loader import load_config


def check_and_install_modules():
    modules_to_check = {
        "cv2": "opencv-python~=4.10.0.84",
        "pytesseract": "pytesseract~=0.3.13",
        "numpy": "numpy~=2.1.0",
        "psutil": "psutil~=6.0.0",
        "keyboard": "keyboard~=0.13.5",
        "pywinauto": "pywinauto~=0.6.8",
        "pybind11": "pybind11~=2.13.1",
        "setuptools": "setuptools~=73.0.1",
        "vgamepad": "vgamepad~=0.1.0",
        "autoit": "PyAutoIt~=0.6.5",
        "requests": "requests~=2.32.3",
        "win32gui": "pywin32~=306",
        "coloredlogs": "coloredlogs~=15.0.1",
        "colorama": "colorama~=0.4.6"
    }

    modules_to_install = {}
    for module_name, package_name in modules_to_check.items():
        try:
            importlib.import_module(module_name)
        except (ImportError, ModuleNotFoundError):
            modules_to_install[module_name] = package_name

    if modules_to_install:
        print("The following modules are not installed:")
        for module_name, package_name in modules_to_install.items():
            print(f"{module_name} (package: {package_name})")
        print("Would you like to install them? (y/n)")
        user_input = input().strip().lower()
        if user_input == 'y':
            for package_name in modules_to_install.values():
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                except subprocess.CalledProcessError:
                    print(f"Failed to install {package_name}. Please install it manually.")
            text = "All modules have been installed. Please restart the script."
            print("=" * len(text))
            print(text)
            print("=" * len(text))
            sys.exit(0)


def main():
    config = load_config()

    if not getattr(sys, 'frozen', False):
        check_and_install_modules()

    import coloredlogs
    import keyboard

    from utils.sequence_maker import App
    from utils.roblox_manager_types.roblox_manager_infinite import RobloxManagerInfinite
    from utils.roblox_manager_types.roblox_manager_story import RobloxManagerStory
    from utils.roblox_manager_types.roblox_manager_tower import RobloxManagerTower
    from utils.roblox_manager_types.roblox_manager_portal import RobloxManagerPortal
    from utils.roblox_manager_types.roblox_manager_realm_infinite import RobloxManagerRealmInfinite

    keyboard.hook_key(config.kill_key, lambda _: os._exit(0))
    multiprocessing.freeze_support()

    if getattr(sys, 'frozen', False):
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    pathlib.Path("./logs/").mkdir(parents=True, exist_ok=True)
    pathlib.Path("custom-sequence/").mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ADFK")
    coloredlogs.install(logger=logger, level=config.logging_level, fmt=log_format)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(f"./logs/ADFK_{time.strftime('%Y%m%d-%H%M%S')}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    mode_names = {
        1: "Infinite Farming",
        2: "Story Progression",
        3: "Tower of Eternity",
        4: "Auto Complete Portals",
        5: "Athenyx Realm Modes",
        6: "Create or Edit a Custom Placement"
    }

    world_names = {
        1: "Windmill Village",
        2: "Haunted City",
        3: "Cursed Academy",
        4: "Blue Planet",
        5: "Underwater Temple",
        6: "Swordsman Dojo",
        7: "Snowy Woods",
        8: "Crystal Cave"
    }

    portal_names = {
        1: "Demon Portal",
        2: "Cursed Kingdom Portal",
        3: "Ancient Dragon Portal",
        4: "Solar Temple Portal",
        5: "Lunar Temple Portal"
    }

    rarity_names = {
        1: "Rare",
        2: "Epic",
        3: "Legendary",
        4: "Mythic",
        5: "Secret",
        6: "In Descending Order"
    }

    rarity_names2 = {
        12: "Epic",
        13: "Legendary",
        14: "Mythic",
        15: "Secret",
        16: "Do All"
    }

    realm_modes = {
        1: "Realm Infinite Farming",
        2: "Realm Story Progression",
        3: "Realm Story Farming",
        4: "Realm Challenge/Infinite Farming (alternates)"
    }

    realm_names = {
        1: "Ruined City",
        2: "Aether Gateway",
        3: "Pantheon Passage",
        4: "Abyssal Gate",
        5: "Soulweaver Gate",
        6: "Cyber Gate"
    }

    print("Choose between the following modes")
    print("1: Infinite Farming")
    print("2: Story Progression")
    print("3: Tower of Eternity(only 1 account for now)")
    print("4: Auto Complete Portals")
    print("5: Athenyx Realm Modes")
    print("6: Create or Edit a Custom Placement")
    while True:
        try:
            mode_choice = int(input("Enter choice: "))
            if mode_choice in [1, 2, 3, 4, 5, 6]:
                break
        except ValueError:
            pass
    logger.info(f"Mode Choice: {mode_names[mode_choice]}")

    roblox_pids = None
    custom_sequence = None
    if mode_choice in [1, 2, 3, 4, 5]:
        print("Enter Roblox PIDs from running script previously")
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
                    roblox_pids = None
                    break
            except (ValueError, AssertionError, SyntaxError):
                pass
        logger.info(f"Roblox PIDs: {roblox_pids}")

    if mode_choice in [1, 2, 3, 4, 5]:
        print("Choose a custom placement to use")
        print("Leave blank and press enter if you want to use default placement")
        custom_sequences = [f for f in os.listdir("custom-sequence/") if f.endswith(".json")]
        for i, sequence in enumerate(custom_sequences):
            with open(f"custom-sequence/{sequence}") as f:
                data = json.load(f)
                print(f"{i + 1}: {data['name']} - {data['description']}")
        while True:
            try:
                custom_input = input("Enter choice: ")
                if custom_input:
                    custom_input = int(custom_input)
                    assert custom_input in range(1, len(custom_sequences) + 1)
                    break
                else:
                    custom_sequence = None
                    break
            except (ValueError, AssertionError):
                pass
        if custom_input:
            with open(f"custom-sequence/{custom_sequences[custom_input - 1]}", "r") as f:
                custom_sequence = json.load(f)
        logger.info(f"Custom Sequence: {custom_sequence}")

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
        logger.info(f"World Choice: {world_names[world_input]}")

        roblox_manager = RobloxManagerInfinite(roblox_pids=roblox_pids, world=world_input, custom_sequence=custom_sequence)
        roblox_manager.start()

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
        logger.info(f"World Choice: {world_names[world_input]}")

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
        logger.info(f"Chapter Choice: Chapter {chapter_input}")

        roblox_manager = RobloxManagerStory(roblox_pids=roblox_pids, world=world_input, level=chapter_input, custom_sequence=custom_sequence)
        roblox_manager.start()

    elif mode_choice == 3:
        if roblox_pids is not None:
            roblox_pids = {list(roblox_pids.keys())[0]: list(roblox_pids.values())[0]}
        roblox_manager = RobloxManagerTower(roblox_pids=roblox_pids, world=0, custom_sequence=custom_sequence)
        roblox_manager.start()

    elif mode_choice == 4:
        print("Choose which portal to auto complete")
        print("1: Demon Portal")
        print("2: Cursed Kingdom Portal")
        print("3: Ancient Dragon Portal")
        print("4: Solar Temple Portal")
        print("5: Lunar Temple Portal")
        while True:
            try:
                portal_input = int(input("Enter choice: "))
                if portal_input in [1, 2, 3, 4, 5]:
                    break
            except ValueError:
                pass
        logger.info(f"Portal Choice: {portal_names[portal_input]}")

        print("Choose which rarity to auto complete")
        print("1: Rare")
        print("2: Epic")
        print("3: Legendary")
        print("4: Mythic")
        print("5: Secret")
        print("6: In Descending Order")
        while True:
            try:
                rarity_input = int(input("Enter choice: "))
                if rarity_input in [1, 2, 3, 4, 5, 6]:
                    break
            except ValueError:
                pass
        logger.info(f"Rarity Choice: {rarity_names[rarity_input]}")

        if rarity_input == 6:
            print("What rarity to stop at (will not attempt this rarity and higher)")
            print("1: Epic")
            print("2: Legendary")
            print("3: Mythic")
            print("4: Secret")
            print("5: Do All")
            while True:
                try:
                    rarity_input = int(input("Enter choice: "))
                    if rarity_input in [1, 2, 3, 4, 5]:
                        break
                except ValueError:
                    pass
            rarity_input = rarity_input + 11
            logger.info(f"Rarity Stop: {rarity_names2[rarity_input]}")

        roblox_manager = RobloxManagerPortal(roblox_pids=roblox_pids, world=portal_input, level=rarity_input, custom_sequence=custom_sequence)
        roblox_manager.start()

    elif mode_choice == 5:
        print("Choose which mode to do in Athenyx Realm")
        print("1: Realm Infinite Farming")
        print("2: Realm Story Progression")
        print("3: Realm Story Farming")
        print("4: Realm Challenge/Infinite Farming (alternates)")
        while True:
            try:
                realm_input = int(input("Enter choice: "))
                if realm_input in [1, 2, 3, 4]:
                    break
            except ValueError:
                pass
        logger.info(f"Realm Choice: {realm_modes[realm_input]}")

        if realm_input == 1:
            print("Choose which world to farm in")
            print("1: Ruined City")
            print("2: Aether Gateway")
            print("3: Pantheon Passage")
            print("4: Abyssal Gate")
            print("5: Soulweaver Gate")
            print("6: Cyber Gate")
            while True:
                try:
                    world_input = int(input("Enter choice: "))
                    if world_input in [1, 2, 3, 4, 5, 6]:
                        break
                except ValueError:
                    pass
            logger.info(f"World Choice: {realm_names[world_input]}")

            roblox_manager = RobloxManagerRealmInfinite(roblox_pids=roblox_pids, world=world_input, custom_sequence=custom_sequence)
            roblox_manager.start()
        else:
            print("Not implemented yet")

    elif mode_choice == 6:
        keyboard.unhook_all()
        root = tk.Tk()
        root.geometry("400x500")
        App(root)
        root.attributes('-topmost', True)
        root.after(100, lambda: root.attributes('-topmost', False))
        root.lift()
        root.focus_force()
        root.mainloop()
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("An unexpected error occurred")
        print(traceback.format_exc())
        input("Press enter to exit.")
        os._exit(0)
