import ctypes
import struct
import time
from control import Control

from PyMemoryEditor import OpenProcess, ScanTypesEnum

y_addrs = 0x1ab87ef4854
x_addrs = y_addrs - 0x4
z_addrs = y_addrs + 0x4
pitch_addrs = y_addrs + 0x18C
yaw_addrs = y_addrs + 0x188

addrs = [x_addrs, y_addrs, z_addrs, pitch_addrs, yaw_addrs]

process_name = "RobloxPlayerBeta.exe"
with OpenProcess(process_name=process_name) as process:
    print(f"Process ID: {process.pid}")
    while True:
        for address, value in process.search_by_addresses(bytes, 4, addrs):
            if address == x_addrs:
                print(f"x: {struct.unpack('f', value)[0]}")
            elif address == y_addrs:
                print(f"y: {struct.unpack('f', value)[0]}")
            elif address == z_addrs:
                print(f"z: {struct.unpack('f', value)[0]}")
            elif address == pitch_addrs:
                print(f"pitch: {struct.unpack('f', value)[0]}")
            elif address == yaw_addrs:
                print(f"yaw: {struct.unpack('f', value)[0]}")
        time.sleep(1)
