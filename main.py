import os
import memory
import time
from control import Control
from roblox import Roblox
import config
if config.port == 0000:
    import config_personal as config

try:
    import memory_search
except ImportError:
    os.system("python setup.py build_ext --inplace")
    import memory_search

roblox_controller = Roblox()
pids = roblox_controller.start_all_accounts()
print(pids)
input("Press enter to continue")
roblox_controller.all_enter_story()

# pid = pids[0]
# print(pid)
# addresses = memory.search_init_pos(pid, initial_pos, initial_tolerance)
# print(f"Found {len(addresses)} addresses")
# input("Press enter to continue")
# final_addresses = memory.search_final_pos(pid, addresses, final_pos, final_tolerance)
# print(f"Found {len(final_addresses)} addresses")
# final_address = None
# for address in final_addresses:
#     rot = memory.get_current_rot(pid, address)
#     if rot[1] == 270.0 and abs(rot[0] + 0.6) < 0.1:
#         final_address = address
#         break
# if final_address is None:
#     print("Could not find final address")
#     exit()
#
# print(f"Found final address: {hex(final_address)}")
# input("Press enter to continue")
#
# control = Control()
# while True:
#     time.sleep(3)
#     control.wake_up()
#     time.sleep(0.5)
#     control.go_to_pos(pid, final_address, 15.234, -428.432, 2)
#     input("Arrived at destination. Press enter to go again")
# while True:
#     current_info = memory.get_current_info(pid, final_address)
#     print(current_info)
#     time.sleep(1)

# 15.234, -428.432
