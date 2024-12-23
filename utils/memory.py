import os
import math
import psutil
import multiprocessing

import coords
from utils.exceptions import *
try:
    import memory_search
except ImportError:
    os.system("python utils/compile.py build_ext --inplace")
    import memory_search


def floats_to_degree(float1, float2):
    yaw_degrees = math.degrees(math.atan2(float2, float1))
    if yaw_degrees < 0:
        yaw_degrees += 360
    return yaw_degrees


def get_pids():
    pids = []
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] == "RobloxPlayerBeta.exe":
            pids.append(process.info["pid"])
    return pids


def search_multiprocess(pid, queue):
    try:
        addresses = memory_search.search_memory(pid, coords.init_pos_x, coords.init_pos_y, coords.init_pos_z, coords.init_pos_tolerance, coords.init_pitch, coords.init_pitch_tolerance, coords.rot_offset)
        queue.put(addresses)
    except Exception as e:
        queue.put(e)


def search(pid):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=search_multiprocess, args=(pid, queue))
    p.start()
    p.join()
    if p.exitcode != 0:
        raise MemoryException("Could not find memory addresses")
    result = queue.get()
    if isinstance(result, Exception):
        raise MemoryException("Could not find memory addresses")
    return result


def get_current_info(pid, y_address):
    pos = memory_search.read_player_info(pid, y_address, coords.rot_offset)
    if len(pos) != 6:
        raise MemoryException("Could not read play info")
    return [pos[0], pos[1], pos[2], pos[3], floats_to_degree(pos[4], pos[5])]


def get_current_pos(pid, y_address):
    pos = memory_search.read_player_pos(pid, y_address, coords.rot_offset)
    if len(pos) != 3:
        raise MemoryException("Could not read player pos")
    return [pos[0], pos[1], pos[2]]


def get_current_rot(pid, y_address):
    pos = memory_search.read_player_rot(pid, y_address, coords.rot_offset)
    if len(pos) != 3:
        raise MemoryException("Could not read player rot")
    return [pos[0], floats_to_degree(pos[1], pos[2])]
