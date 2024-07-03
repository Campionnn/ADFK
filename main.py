import os
import logging
import time
from pathlib import Path

from roblox import Roblox
import config
if config.port == 0000:
    import config_personal as config

try:
    import memory_search
except ImportError:
    os.system("python setup.py build_ext --inplace")
    import memory_search

Path("./logs/").mkdir(parents=True, exist_ok=True)
if config.logging_level == "debug":
    level = logging.DEBUG
else:
    level = logging.INFO
logging.basicConfig(filename='ADFK.log', level=level)
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
logging.getLogger().addHandler(consoleHandler)

roblox_controller = Roblox(logger)
pids = roblox_controller.start_all_accounts()
print(pids)
roblox_controller.all_enter_story()
