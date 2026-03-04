#include <windows.h>
#include <iostream>

int main() {

    DWORD pid;
    std::cout << "Enter PID: ";
    std::cin >> pid;

    const char* dllPath = "goodsoup.dll";

    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);

    if (!hProcess) {
        std::cout << "Failed to open process\n";
        return 1;
    }

    LPVOID mem = VirtualAllocEx(
        hProcess,
        NULL,
        strlen(dllPath) + 1,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );

    WriteProcessMemory(
        hProcess,
        mem,
        dllPath,
        strlen(dllPath) + 1,
        NULL
    );

    HANDLE hThread = CreateRemoteThread(
        hProcess,
        NULL,
        0,
        (LPTHREAD_START_ROUTINE)GetProcAddress(
            GetModuleHandleA("kernel32.dll"),
            "LoadLibraryA"
        ),
        mem,
        0,
        NULL
    );

    WaitForSingleObject(hThread, INFINITE);

    CloseHandle(hThread);
    CloseHandle(hProcess);

    std::cout << "DLL Injected\n";

    return 0;
}