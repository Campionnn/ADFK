import os
import math
import psutil
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


def get_pids_by_name(process_name):
    pids = []
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            pids.append(process.info['pid'])
    return pids


def search_init_pos(pid, value, tolerance):
    suspend_process(pid)
    addresses = memory_search.search_memory_for_float(pid, value, tolerance)
    resume_process(pid)
    return addresses


def search_final_pos(pid, addresses, value, tolerance):
    suspend_process(pid)
    addresses = memory_search.search_memory_for_float_in_addresses(pid, addresses, value, tolerance)
    resume_process(pid)
    return addresses


def get_current_info(pid, y_address):
    pos = memory_search.read_player_info(pid, y_address)
    if len(pos) != 6:
        raise Exception("Could not read memory")
    return [pos[0], pos[1], pos[2], pos[3], floats_to_degree(pos[4], pos[5])]


def get_current_pos(pid, y_address):
    pos = memory_search.read_player_pos(pid, y_address)
    if len(pos) != 3:
        raise Exception("Could not read memory")
    return [pos[0], pos[1], pos[2]]


def get_current_rot(pid, y_address):
    pos = memory_search.read_player_rot(pid, y_address)
    if len(pos) != 3:
        raise Exception("Could not read memory")
    return [pos[0], floats_to_degree(pos[1], pos[2])]


def suspend_process(pid):
    try:
        process = psutil.Process(pid)
        process.suspend()
        return True
    except psutil.NoSuchProcess:
        return False


def resume_process(pid):
    try:
        process = psutil.Process(pid)
        process.resume()
        return True
    except psutil.NoSuchProcess:
        return False
