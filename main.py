import os
import logging
import time
import pathlib
import keyboard
import threading

from utils.roblox_manager import RobloxManager
import config
if config.port == 0000:
    import config_personal as config

try:
    import utils.memory_search
except ImportError:
    os.system("python compile.py build_ext --inplace")
    import utils.memory_search

def kill_thread():
    keyboard.wait("esc")
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

roblox_manager = RobloxManager(logger)
roblox_manager.all_start_instance()
pids = {instance.pid: instance.y_addrs for instance in roblox_manager.roblox_instances}
logger.debug(f"Roblox pids: {pids}")
while True:
    roblox_manager.all_enter_story()
