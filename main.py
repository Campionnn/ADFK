import os
import memory
import time

try:
    import memory_search
except ImportError:
    os.system("python setup.py build_ext --inplace")
    import memory_search

process_name = "RobloxPlayerBeta.exe"

initial_pos = 13.1508
final_pos = -2.3426
tolerance = 0.0005

pids = memory.get_pids_by_name(process_name)
if len(pids) != 1:
    print("more than 1 pid will do later")
    exit()

pid = pids[0]
addresses = memory.search_init_pos(pid, initial_pos, tolerance)
print(f"Found {len(addresses)} addresses")
input("Press enter to continue")
final_address = memory.search_final_pos(pid, addresses, final_pos, tolerance * 100)
if len(final_address) == 0:
    print("Could not find any addresses")
    exit()
if len(final_address) <= 2:
    final_address = final_address[-1]
else:
    print("Could not find any addresses")

print(f"Found final address: {hex(final_address)}")
while True:
    current_pos = memory.get_current_pos(pid, final_address)
    print(current_pos)
    time.sleep(1)
