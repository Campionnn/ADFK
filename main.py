import os
import memory
import time
from control import Control

try:
    import memory_search
except ImportError:
    os.system("python setup.py build_ext --inplace")
    import memory_search

process_name = "RobloxPlayerBeta.exe"

initial_pos = 13.1508
initial_tolerance = 0.0005
final_pos = -10.0
final_tolerance = 8.0

# control = Control()
# input()
# time.sleep(3)
# control.move_forward(1)
# time.sleep(3)
# control.reset()


pids = memory.get_pids_by_name(process_name)
if len(pids) != 1:
    print("not 1 pid will do later")
    exit()

pid = pids[0]
addresses = memory.search_init_pos(pid, initial_pos, initial_tolerance)
print(f"Found {len(addresses)} addresses")
input("Press enter to continue")
final_addresses = memory.search_final_pos(pid, addresses, final_pos, final_tolerance)
print(f"Found {len(final_addresses)} addresses")
final_address = None
for address in final_addresses:
    rot = memory.get_current_rot(pid, address)
    if rot[1] == 270.0 and abs(rot[0] + 0.6) < 0.1:
        final_address = address
        break
if final_address is None:
    print("Could not find final address")
    exit()

print(f"Found final address: {hex(final_address)}")
input("Press enter to continue")

control = Control()
while True:
    time.sleep(3)
    control.wake_up()
    time.sleep(3)
    print("starting movement")
    control.go_to_pos(pid, final_address, 15.234, -428.432, 2)
    input("Arrived at destination. Press enter to go again")
# while True:
#     current_info = memory.get_current_info(pid, final_address)
#     print(current_info)
#     time.sleep(1)

# 15.234, -428.432
