#include <iostream>
#include <windows.h>
#include <vector>
#include <algorithm>
#include <cstdint>

int rotOffset = 0x170;

std::vector<float> ReadPlayerInfoInternal(DWORD pid, uint64_t int_address, HANDLE hProcess = NULL);

bool ReadMemory(HANDLE hProcess, LPCVOID address, LPVOID buffer, SIZE_T size) {
    SIZE_T bytesRead;
    return ReadProcessMemory(hProcess, address, buffer, size, &bytesRead) && bytesRead == size;
}

#undef min
uint64_t SearchMemory(DWORD pid, float targetValueX, float targetValueY, float targetValueZ, float posTolerance, float targetPitch, float pitchTolerance) {
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);

    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    LPCVOID endAddress = sysInfo.lpMaximumApplicationAddress;
    endAddress = reinterpret_cast<LPCVOID>(static_cast<uintptr_t>(reinterpret_cast<SIZE_T>(endAddress) * 0.03));
    LPCVOID startAddress = reinterpret_cast<LPCVOID>(static_cast<uintptr_t>(reinterpret_cast<SIZE_T>(endAddress) * 0.01));

    MEMORY_BASIC_INFORMATION memInfo;
    int bufferSize = 1024;
    std::vector<char> buffer(bufferSize);
    std::vector<float> values;
    LPCVOID addressBuffer;

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
                        if (std::abs(value - targetValueY) <= posTolerance) {
                            addressBuffer = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(regionBase) + bytesRead + i * sizeof(float));
                            values = ReadPlayerInfoInternal(pid, reinterpret_cast<uint64_t>(addressBuffer), hProcess);
                            if (std::abs(values[0] - targetValueX) <= posTolerance && std::abs(values[2] - targetValueZ) <= posTolerance && abs(values[3] - targetPitch) <= pitchTolerance && std::abs(values[4]) <= 1 && std::abs(values[5]) <= 1) {
                                CloseHandle(hProcess);
                                return reinterpret_cast<uint64_t>(addressBuffer);
                            }
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
    return 0;
}

std::vector<float> ReadPlayerInfoInternal(DWORD pid, uint64_t intAddress, HANDLE hProcess) {
    LPCVOID base_address = reinterpret_cast<LPCVOID>(intAddress);
    LPCVOID start_address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(base_address) - 0x4);
    SIZE_T size_to_read = rotOffset + 0x10;

    std::vector<BYTE> buffer(size_to_read);
    if (!ReadMemory(hProcess, start_address, buffer.data(), size_to_read)) {
        return {};
    }

    float x_addrs = *reinterpret_cast<float*>(buffer.data());
    float y_addrs = *reinterpret_cast<float*>(buffer.data() + 0x4);
    float z_addrs = *reinterpret_cast<float*>(buffer.data() + 0x8);
    float yaw1 = *reinterpret_cast<float*>(buffer.data() + rotOffset + 0x4);
    float pitch = *reinterpret_cast<float*>(buffer.data() + rotOffset + 0x8);
    float yaw2 = *reinterpret_cast<float*>(buffer.data() + rotOffset + 0xC);

    return {x_addrs, y_addrs, z_addrs, pitch, yaw1, yaw2};
}

std::vector<float> ReadPlayerInfo(DWORD pid, uint64_t intAddress) {
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ, FALSE, pid);

    LPCVOID base_address = reinterpret_cast<LPCVOID>(intAddress);
    LPCVOID start_address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(base_address) - 0x4);
    SIZE_T size_to_read = rotOffset + 0x10;

    std::vector<BYTE> buffer(size_to_read);
    if (!ReadMemory(hProcess, start_address, buffer.data(), size_to_read)) {
        CloseHandle(hProcess);
        return {};
    }
    CloseHandle(hProcess);

    float x_addrs = *reinterpret_cast<float*>(buffer.data());
    float y_addrs = *reinterpret_cast<float*>(buffer.data() + 0x4);
    float z_addrs = *reinterpret_cast<float*>(buffer.data() + 0x8);
    float pitch = *reinterpret_cast<float*>(buffer.data() + rotOffset + 0x8);
    float yaw1 = *reinterpret_cast<float*>(buffer.data() + rotOffset + 0x4);
    float yaw2 = *reinterpret_cast<float*>(buffer.data() + rotOffset + 0xC);

    return {x_addrs, y_addrs, z_addrs, pitch, yaw1, yaw2};
}

std::vector<float> ReadPlayerPos(DWORD pid, uint64_t intAddress) {
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ, FALSE, pid);

    LPCVOID base_address = reinterpret_cast<LPCVOID>(intAddress);
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

std::vector<float> ReadPlayerRot(DWORD pid, uint64_t intAddress) {
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ, FALSE, pid);

    LPCVOID base_address = reinterpret_cast<LPCVOID>(intAddress);
    LPCVOID start_address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(base_address) + rotOffset);
    SIZE_T size_to_read = 0xC;

    std::vector<BYTE> buffer(size_to_read);
    if (!ReadMemory(hProcess, start_address, buffer.data(), size_to_read)) {
        CloseHandle(hProcess);
        return {};
    }
    CloseHandle(hProcess);

    float pitch = *reinterpret_cast<float*>(buffer.data() + 0x4);
    float yaw1 = *reinterpret_cast<float*>(buffer.data());
    float yaw2 = *reinterpret_cast<float*>(buffer.data() + 0x8);

    return {pitch, yaw1, yaw2};
}

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

PYBIND11_MODULE(memory_search, m) {
    m.doc() = "Memory module for searching for floats in memory";
    m.def("search_memory", &SearchMemory);
    m.def("read_player_info", &ReadPlayerInfo);
    m.def("read_player_pos", &ReadPlayerPos);
    m.def("read_player_rot", &ReadPlayerRot);
}