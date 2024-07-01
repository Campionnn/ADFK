import os
import struct
import time
from control import Control
from PyMemoryEditor import OpenProcess

try:
    import memory_search
except ImportError:
    os.system("python setup.py build_ext --inplace")
    import memory_search

initial_pos = 13.1508
final_pos = -2.3425
tolerance = 0.0005

process_name = "RobloxPlayerBeta.exe"
with OpenProcess(process_name=process_name) as process:
    print(f"Process ID: {process.pid}")
    addresses = memory_search.search_memory_for_float(process.pid, 13.1508, tolerance)
    # for address in addresses:
    #     print(f"Found address: {address}")
    print(len(addresses))
    input("Press enter once in afk...")
    addresses2 = memory_search.search_memory_for_float_in_addresses(process.pid, addresses, -2.3425, tolerance)
    for address in addresses2:
        print(f"Found address: {hex(address)}")

    if len(addresses2) == 1:
        y_addrs = addresses2[0]
    elif len(addresses2) == 2:
        y_addrs = addresses2[1]
    else:
        print("Could not find one address")
        exit()
    x_addrs = y_addrs - 0x4
    z_addrs = y_addrs + 0x4
    pitch_addrs = y_addrs + 0x18C
    yaw_addrs = y_addrs + 0x188
    addrs = [x_addrs, y_addrs, z_addrs, pitch_addrs, yaw_addrs]
    while True:
        player_pos = {}
        for address, value in process.search_by_addresses(bytes, 4, addrs):
            if address == x_addrs:
                player_pos['x'] = struct.unpack('f', value)[0]
            elif address == y_addrs:
                player_pos['y'] = struct.unpack('f', value)[0]
            elif address == z_addrs:
                player_pos['z'] = struct.unpack('f', value)[0]
            elif address == pitch_addrs:
                player_pos['pitch'] = struct.unpack('f', value)[0]
            elif address == yaw_addrs:
                player_pos['yaw'] = struct.unpack('f', value)[0]
        pos_order = ['x', 'y', 'z', 'pitch', 'yaw']
        print(' '.join(f"{pos}: {player_pos[pos]}" for pos in pos_order))
        time.sleep(1)
    else:
        print("Could not find one address")
