import os
import math
import psutil
try:
    import memory_search
except ImportError:
    os.system("python setup.py build_ext --inplace")
    import memory_search


def calculate_degrees(float1, float2):
    yaw_degrees = math.degrees(math.atan2(float2, float1))
    if yaw_degrees < 0:
        yaw_degrees += 360
    return yaw_degrees


def get_pids_by_name(process_name):
    pids = []
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            pids.append(process.info['pid'])
    return pids


def search_init_pos(pid, value, tolerance):
    return memory_search.search_memory_for_float(pid, value, tolerance)


def search_final_pos(pid, addresses, value, tolerance):
    return memory_search.search_memory_for_float_in_addresses(pid, addresses, value, tolerance)


def get_current_pos(pid, y_address):
    pos = memory_search.read_player_pos(pid, y_address)
    return [pos[0], pos[1], pos[2], pos[3], calculate_degrees(pos[4], pos[5])]
