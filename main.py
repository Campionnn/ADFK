import ctypes
import struct
import time
from mem_edit import Process
from control import Control

from PyMemoryEditor import OpenProcess, ScanTypesEnum


pid = Process.get_pid_by_name('RobloxPlayerBeta.exe')
print(pid)
target_value = 12.680
with Process.open_process(pid) as p:
    value = p.read_memory(0x22BC6199C94, ctypes.c_float())
    print(value)
    # address_list = [0x1EAC82D88B0, 0x1EAC82D88B0+0x4, 0x1EAC82D88B0+0x8]
    # addrs = p.search_all_memory(ctypes.c_float(target_value), verbatim=True)
    #
    # # addrs = addrs[:100]
    # print(addrs)
    # for address in addrs:
    #     print(f"Address", address, "holds the value", p.read_memory(address, ctypes.c_float()).value)

with OpenProcess(pid=pid) as process:
    # value = p.read_process_memory(0x22BC6199C94, bytes, 4)
    # [value] = struct.unpack('f', value)
    # print(value)
    addrs = []
    start = time.time()
    results = process.search_by_value_between(bytes, 4, struct.pack('f', target_value - 0.0005), struct.pack('f', target_value + 0.0005), progress_information=True, writeable_only=True)
    for address, info in results:
        addrs.append(address)
        print(f"Address: 0x{address:016X} | Progress: {info['progress'] * 100:.1f}%")
    print(addrs)