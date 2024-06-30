#include <iostream>
#include <windows.h>
#include <vector>
#include <algorithm>

bool ReadMemory(HANDLE hProcess, LPCVOID address, LPVOID buffer, SIZE_T size) {
    SIZE_T bytesRead;
    return ReadProcessMemory(hProcess, address, buffer, size, &bytesRead) && bytesRead == size;
}

#undef min
std::vector<LPCVOID> SearchMemoryForFloat(DWORD pid, float targetValue, float tolerance) {
    std::vector<LPCVOID> foundAddresses;
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, FALSE, pid);

    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    LPCVOID startAddress = sysInfo.lpMinimumApplicationAddress;
    LPCVOID endAddress = sysInfo.lpMaximumApplicationAddress;

    MEMORY_BASIC_INFORMATION memInfo;
    std::vector<char> buffer(4096);

    for (LPCVOID address = startAddress; address < endAddress;) {
        if (VirtualQueryEx(hProcess, address, &memInfo, sizeof(memInfo)) == 0) {
            address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(address) + 0x1000);
            continue;
        }

        if (memInfo.State == MEM_COMMIT && (memInfo.Protect == PAGE_READWRITE || memInfo.Protect == PAGE_READONLY)) {
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
                }
                bytesRead += bytesToRead;
            }
        }

        address = reinterpret_cast<LPCVOID>(reinterpret_cast<SIZE_T>(address) + memInfo.RegionSize);
    }

    CloseHandle(hProcess);
    return foundAddresses;
}

std::vector<LPCVOID> SearchMemoryForFloatInAddresses(DWORD pid, std::vector<LPCVOID> addresses, float targetValue, float tolerance) {
    std::vector<LPCVOID> foundAddresses;
    HANDLE hProcess = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, FALSE, pid);

    float buffer;
    for (auto address : addresses) {
        if (ReadMemory(hProcess, address, &buffer, sizeof(float))) {
            if (std::abs(buffer - targetValue) <= tolerance) {
                foundAddresses.push_back(address);
            }
        }
    }

    CloseHandle(hProcess);
    return foundAddresses;
}

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

PYBIND11_MODULE(memory_search, m) {
    m.doc() = "Memory module for searching for floats in memory";
    m.def("search_memory_for_float", &SearchMemoryForFloat);
    m.def("search_memory_for_float_in_addresses", &SearchMemoryForFloatInAddresses);
}