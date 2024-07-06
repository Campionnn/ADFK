#include <iostream>
#include <windows.h>
#include <vector>
#include <algorithm>
#include <cstdint>

bool ReadMemory(HANDLE hProcess, LPCVOID address, LPVOID buffer, SIZE_T size) {
    SIZE_T bytesRead;
    return ReadProcessMemory(hProcess, address, buffer, size, &bytesRead) && bytesRead == size;
}

#undef min
std::vector<LPCVOID> SearchMemoryForFloat(DWORD pid, float targetValue, float tolerance) {
    std::vector<LPCVOID> foundAddresses;
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);

    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    LPCVOID startAddress = sysInfo.lpMinimumApplicationAddress;
    LPCVOID endAddress = sysInfo.lpMaximumApplicationAddress;

    MEMORY_BASIC_INFORMATION memInfo;
    int bufferSize = 4096;
    std::vector<char> buffer(bufferSize);

    for (LPCVOID address = startAddress; address < endAddress;) {
        if (VirtualQueryEx(hProcess, address, &memInfo, sizeof(memInfo)) == 0) {
            address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(address) + bufferSize);
            continue;
        }

        if (memInfo.State == MEM_COMMIT && (memInfo.Protect == PAGE_READWRITE)) {
            SIZE_T regionSize = memInfo.RegionSize;
            LPCVOID regionBase = memInfo.BaseAddress;

            SIZE_T bytesRead = 0;
            while (bytesRead < regionSize) {
                SIZE_T bytesToRead = std::min(buffer.size(), regionSize - bytesRead);
                if (ReadMemory(hProcess, reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(regionBase) + bytesRead), buffer.data(), bytesToRead)) {
                    SIZE_T numFloats = bytesToRead / sizeof(float);
                    float* floatBuffer = reinterpret_cast<float*>(buffer.data());
                    for (SIZE_T i = 0; i < numFloats; ++i) {
                        float value = floatBuffer[i];
                        if (std::abs(value - targetValue) <= tolerance) {
                            foundAddresses.push_back(reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(regionBase) + bytesRead + i * sizeof(float)));
                        }
                    }
                } else {
                    break;
                }
                bytesRead += bytesToRead;
            }
        }

        address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(address) + memInfo.RegionSize);
    }

    CloseHandle(hProcess);
    return foundAddresses;
}

std::vector<uint64_t> SearchMemoryForFloatInAddresses(DWORD pid, std::vector<LPCVOID> addresses, float targetValue, float tolerance) {
    std::vector<uint64_t> foundAddresses;
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);

    float buffer;
    for (auto address : addresses) {
        if (ReadMemory(hProcess, address, &buffer, sizeof(float))) {
            if (std::abs(buffer - targetValue) <= tolerance) {
                foundAddresses.push_back(reinterpret_cast<uint64_t>(address));
            }
        }
    }

    CloseHandle(hProcess);
    return foundAddresses;
}

std::vector<float> ReadPlayerInfo(DWORD pid, uint64_t int_address) {
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ, FALSE, pid);

    LPCVOID base_address = reinterpret_cast<LPCVOID>(int_address);
    LPCVOID start_address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(base_address) - 0x4);
    SIZE_T size_to_read = 0x198;

    std::vector<BYTE> buffer(size_to_read);
    if (!ReadMemory(hProcess, start_address, buffer.data(), size_to_read)) {
        CloseHandle(hProcess);
        return {};
    }
    CloseHandle(hProcess);

    float x_addrs = *reinterpret_cast<float*>(buffer.data());
    float y_addrs = *reinterpret_cast<float*>(buffer.data() + 0x4);
    float z_addrs = *reinterpret_cast<float*>(buffer.data() + 0x8);
    float pitch = *reinterpret_cast<float*>(buffer.data() + 0x190);
    float yaw1 = *reinterpret_cast<float*>(buffer.data() + 0x18C);
    float yaw2 = *reinterpret_cast<float*>(buffer.data() + 0x194);

    return {x_addrs, y_addrs, z_addrs, pitch, yaw1, yaw2};
}

std::vector<float> ReadPlayerPos(DWORD pid, uint64_t int_address) {
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ, FALSE, pid);

    LPCVOID base_address = reinterpret_cast<LPCVOID>(int_address);
    LPCVOID start_address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(base_address) - 0x4);
    SIZE_T size_to_read = 0xC;

    std::vector<BYTE> buffer(size_to_read);
    if (!ReadMemory(hProcess, start_address, buffer.data(), size_to_read)) {
        CloseHandle(hProcess);
        return {};
    }
    CloseHandle(hProcess);

    float x_addrs = *reinterpret_cast<float*>(buffer.data());
    float y_addrs = *reinterpret_cast<float*>(buffer.data() + 0x4);
    float z_addrs = *reinterpret_cast<float*>(buffer.data() + 0x8);

    return {x_addrs, y_addrs, z_addrs};
}

std::vector<float> ReadPlayerRot(DWORD pid, uint64_t int_address) {
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ, FALSE, pid);

    LPCVOID base_address = reinterpret_cast<LPCVOID>(int_address);
    LPCVOID start_address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(base_address) + 0x188);
    SIZE_T size_to_read = 0xC;

    std::vector<BYTE> buffer(size_to_read);
    if (!ReadMemory(hProcess, start_address, buffer.data(), size_to_read)) {
        CloseHandle(hProcess);
        return {};
    }
    CloseHandle(hProcess);

    float pitch = *reinterpret_cast<float*>(buffer.data()+ 0x4);
    float yaw1 = *reinterpret_cast<float*>(buffer.data());
    float yaw2 = *reinterpret_cast<float*>(buffer.data() + 0x8);

    return {pitch, yaw1, yaw2};
}

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

PYBIND11_MODULE(memory_search, m) {
    m.doc() = "Memory module for searching for floats in memory";
    m.def("search_memory_for_float", &SearchMemoryForFloat);
    m.def("search_memory_for_float_in_addresses", &SearchMemoryForFloatInAddresses);
    m.def("read_player_info", &ReadPlayerInfo);
    m.def("read_player_pos", &ReadPlayerPos);
    m.def("read_player_rot", &ReadPlayerRot);
}