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

process_name = "RobloxPlayerBeta.exe"
with OpenProcess(process_name=process_name) as process:
    print(process.pid)
    # addresses = memory_search.search_memory_for_float(process.pid, 12.680, 0.0005)
    # for address in addresses:
    #     print(f"Found address: {address}")
    # print(len(addresses))
    # input("Press enter once in afk...")
    # addresses2 = memory_search.search_memory_for_float_in_addresses(process.pid, addresses, -2.3425, 0.005)
    # for address in addresses2:
    #     print(f"Found address: {address}")
    # y_addrs = 0x2E5E72195E4
    # x_addrs = y_addrs - 0x4
    # z_addrs = y_addrs + 0x4
    # pitch_addrs = y_addrs + 0x18C
    # yaw_addrs = y_addrs + 0x188
    # addrs = [x_addrs, y_addrs, z_addrs, pitch_addrs, yaw_addrs]
    # print(f"Process ID: {process.pid}")
    # while True:
    #     for address, value in process.search_by_addresses(bytes, 4, addrs):
    #         if address == x_addrs:
    #             print(f"x: {struct.unpack('f', value)[0]}")
    #         elif address == y_addrs:
    #             print(f"y: {struct.unpack('f', value)[0]}")
    #         elif address == z_addrs:
    #             print(f"z: {struct.unpack('f', value)[0]}")
    #         elif address == pitch_addrs:
    #             print(f"pitch: {struct.unpack('f', value)[0]}")
    #         elif address == yaw_addrs:
    #             print(f"yaw: {struct.unpack('f', value)[0]}")
    #     time.sleep(1)
